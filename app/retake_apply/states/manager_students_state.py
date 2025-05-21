import reflex as rx
from typing import List, Optional, Dict, Any
from beanie.odm.fields import PydanticObjectId # type: ignore
from pydantic import ValidationError

from .auth import AuthState
from ..models.users import User, UserGroup
from ..models.required_course import RequiredCourse
from ..models.academic_year_setting import AcademicYearSetting # 用於獲取預設學年度
from ..utils import csv_utils

class ManagerStudentsState(AuthState):
    """管理課程管理者操作學生應重補修名單的狀態與邏輯"""

    required_courses_list: rx.Var[List[RequiredCourse]] = rx.Var([])
    search_term: rx.Var[str] = ""

    # Modal 控制與表單資料 (合併新增與編輯)
    show_form_modal: rx.Var[bool] = False
    editing_record_id: rx.Var[Optional[str]] = None # None 表示新增模式
    form_data: rx.Var[Dict[str, Any]] = rx.Var({})
    
    # CSV 上傳相關
    csv_import_feedback: rx.Var[str] = ""

    @rx.var
    def form_modal_title(self) -> str:
        return "編輯應重補修記錄" if self.editing_record_id else "新增應重補修記錄"

    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            return
        if not self.is_member_of_any([UserGroup.COURSE_MANAGER, UserGroup.ADMIN]):
            return rx.redirect(self.DEFAULT_UNAUTHORIZED_REDIRECT_PATH) # type: ignore
        await self.load_records()

    async def load_records(self):
        """載入或篩選學生應重補修記錄列表"""
        query_conditions: Dict[str, Any] = {}
        # 複雜搜尋：如果 search_term 存在，我們需要搜尋 RequiredCourse 的欄位，
        # 以及其關聯 User 的 fullname, student_id, email。
        # 這通常需要多階段查詢或資料庫層面的 $lookup。
        # 簡化：先只搜尋 RequiredCourse 的 course_name 和 course_code。
        # 如果使用者輸入的是學號或 Email，可以先查 User，再用 user_id 查 RequiredCourse。
        
        # 暫時簡化搜尋邏輯，只搜尋課程相關欄位
        if self.search_term:
            search_regex = {"$regex": self.search_term, "$options": "i"}
            # 嘗試匹配 User 的 email 或 student_id
            user_matches = await User.find(
                {"$or": [{"email": search_regex}, {"student_id": search_regex}]}
            ).project(User.id).to_list()
            user_ids_match = [user.id for user in user_matches]

            or_conditions = [
                {"course_name": search_regex},
                {"course_code": search_regex},
            ]
            if user_ids_match:
                or_conditions.append({"user_id": {"$in": user_ids_match}})
            
            query_conditions["$or"] = or_conditions

        self.required_courses_list = await RequiredCourse.find(
            query_conditions, 
            fetch_links=True # 確保 user_id 被解析為 User 物件
        ).sort("-uploaded_at").to_list()

    async def handle_search_term_change(self, term: str):
        self.search_term = term
        await self.load_records()

    def _reset_form_data(self):
        # 獲取一個預設的 "不及格科目之學年度"，例如當前系統學年的上一個學期
        # 這裡簡化，可以讓使用者手動輸入或提供選擇器
        self.form_data = {
            "user_identifier": "", # 用於查找 User (例如學號或 Email)
            "academic_year_taken": "112-2", # 應有更好的預設邏輯
            "course_code": "",
            "course_name": "",
            "original_grade": "",
            "is_remedied": False
        }

    def open_add_modal(self):
        self._reset_form_data()
        self.editing_record_id = None
        self.show_form_modal = True

    async def open_edit_modal(self, record: RequiredCourse):
        self.editing_record_id = str(record.id)
        user_identifier = ""
        if record.user_id: # user_id 應該已經是 fetch 過的 User 物件
            user_obj = record.user_id # type: ignore
            user_identifier = user_obj.email or user_obj.student_id or "" # type: ignore
        
        self.form_data = {
            "user_identifier": user_identifier,
            "academic_year_taken": record.academic_year_taken,
            "course_code": record.course_code,
            "course_name": record.course_name,
            "original_grade": record.original_grade,
            "is_remedied": record.is_remedied
        }
        self.show_form_modal = True

    def close_form_modal(self):
        self.show_form_modal = False
        self.editing_record_id = None
        self._reset_form_data()

    async def handle_save_record(self):
        form_data = self.form_data
        try:
            user_identifier = form_data.get("user_identifier", "").strip()
            if not user_identifier:
                return rx.toast.error("學生識別碼 (學號或Email) 不可為空。") # type: ignore

            found_user = await User.find_one(User.student_id == user_identifier)
            if not found_user:
                found_user = await User.find_one(User.email == user_identifier)
            
            if not found_user:
                return rx.toast.error(f"找不到學生：{user_identifier}") # type: ignore

            # 檢查必填欄位
            required_fields = ["academic_year_taken", "course_code", "course_name", "original_grade"]
            for field in required_fields:
                if not form_data.get(field):
                    return rx.toast.error(f"欄位 '{field}' 不可為空。") # type: ignore
            
            is_remedied_val = form_data.get("is_remedied", False)
            if isinstance(is_remedied_val, str): # 從 checkbox 可能得到 "true"/"false"
                is_remedied_val = is_remedied_val.lower() == "true"


            record_data = {
                "user_id": found_user.id, # type: ignore
                "academic_year_taken": form_data["academic_year_taken"],
                "course_code": form_data["course_code"],
                "course_name": form_data["course_name"],
                "original_grade": form_data["original_grade"],
                "is_remedied": bool(is_remedied_val)
            }

            if self.editing_record_id: # 編輯模式
                record_to_update = await RequiredCourse.get(PydanticObjectId(self.editing_record_id))
                if not record_to_update:
                    return rx.toast.error("找不到要更新的記錄。") # type: ignore
                
                # 更新 RequiredCourse 物件的欄位
                for key, value in record_data.items():
                    setattr(record_to_update, key, value)
                await record_to_update.save()
                toast_message = "記錄更新成功！"
            else: # 新增模式
                # 檢查記錄是否已存在
                existing_record = await RequiredCourse.find_one(
                    RequiredCourse.user_id.id == found_user.id, # type: ignore
                    RequiredCourse.academic_year_taken == record_data["academic_year_taken"],
                    RequiredCourse.course_code == record_data["course_code"]
                )
                if existing_record:
                    return rx.toast.error("此學生相同的應重補修科目記錄已存在。") # type: ignore
                
                new_record = RequiredCourse(**record_data) # type: ignore
                await new_record.insert()
                toast_message = "記錄新增成功！"
            
            self.close_form_modal()
            await self.load_records()
            return rx.toast.success(toast_message) # type: ignore
        except ValidationError as ve:
            return rx.toast.error(f"資料驗證失敗: {str(ve)}") # type: ignore
        except Exception as e:
            return rx.toast.error(f"操作失敗：{str(e)}") # type: ignore

    # --- 刪除記錄 ---
    async def handle_delete_record_confirmed(self, record_id_str: str):
        try:
            record_to_delete = await RequiredCourse.get(PydanticObjectId(record_id_str))
            if record_to_delete:
                await record_to_delete.delete()
                await self.load_records()
                return rx.toast.info("記錄已刪除。") # type: ignore
            return rx.toast.error("找不到要刪除的記錄。") # type: ignore
        except Exception as e:
            return rx.toast.error(f"刪除失敗: {str(e)}") # type: ignore

    # --- CSV 匯入 ---
    async def handle_csv_upload(self, files: List[rx.UploadFile]):
        self.csv_import_feedback = "正在處理檔案..."
        if not files:
            self.csv_import_feedback = "請選擇要上傳的 CSV 檔案。"
            return rx.toast.warning(self.csv_import_feedback) # type: ignore
        
        try:
            file_content_bytes = await files[0].read()
            results = await csv_utils.import_required_courses_from_csv(file_content_bytes)
            
            feedback_lines = []
            if results["success"]:
                feedback_lines.append(f"成功匯入 {len(results['success'])} 筆記錄。")
            if results["errors"]:
                feedback_lines.append(f"匯入失敗 {len(results['errors'])} 筆。錯誤詳情:")
                feedback_lines.extend([f"- {err}" for err in results["errors"][:10]])
                if len(results["errors"]) > 10:
                    feedback_lines.append("...還有更多錯誤未顯示。")
            
            self.csv_import_feedback = "\n".join(feedback_lines)
            if not results["errors"]:
                 rx.toast.success("CSV 學生應重補修名單匯入成功！") # type: ignore
            elif results["success"]:
                 rx.toast.warning("CSV 資料部分匯入成功，部分失敗。") # type: ignore
            else:
                 rx.toast.error("CSV 資料匯入失敗。") # type: ignore

            await self.load_records()
        except Exception as e:
            self.csv_import_feedback = f"CSV 檔案處理失敗：{str(e)}"
            return rx.toast.error(self.csv_import_feedback) # type: ignore
            
    # Helper to set form data reactively
    def set_form_field_value(self, key: str, value: Any):
        """更新 form_data 中的特定欄位值"""
        current_data = self.form_data.copy() # 確保是副本以觸發更新
        current_data[key] = value
        self.form_data = current_data
