import reflex as rx
from typing import List, Optional, Dict, Any
from beanie.odm.fields import PydanticObjectId # type: ignore
from pydantic import ValidationError # 用於表單驗證

from .auth import AuthState
from ..models.users import UserGroup
from ..models.course import Course, CourseTimeSlot, VALID_PERIODS
from ..models.enrollment import Enrollment
from ..models.academic_year_setting import AcademicYearSetting
from ..utils import csv_utils # 匯入 CSV 工具模組

# 預設的空時段字典，用於新增時段
EMPTY_TIME_SLOT_DICT = {
    "week_number": None, "day_of_week": 1, "period": VALID_PERIODS[0],
    "start_time": "08:00", "end_time": "08:50", "location": ""
}

class ManagerCoursesState(AuthState):
    """管理課程管理者操作課程的狀態與邏輯"""

    courses_list: rx.Var[List[Course]] = rx.Var([])
    search_term: rx.Var[str] = ""
    filter_academic_year: rx.Var[str] = "" # 當前篩選的學年度
    academic_year_options: rx.Var[List[Dict[str, str]]] = rx.Var([]) # 學年度下拉選單選項
    
    # Modal 控制
    show_add_modal: rx.Var[bool] = False
    show_edit_modal: rx.Var[bool] = False
    
    editing_course_id: rx.Var[Optional[str]] = None 
    
    # 新增課程表單
    add_course_form_data: rx.Var[Dict[str, Any]] = rx.Var({})
    
    # 編輯課程表單
    edit_course_form_data: rx.Var[Dict[str, Any]] = rx.Var({})

    # CSV 上傳相關
    csv_import_feedback: rx.Var[str] = "" # 用於顯示匯入結果

    async def _load_academic_year_options(self):
        """載入學年度選項供篩選器使用"""
        settings = await AcademicYearSetting.find_all(sort=[("academic_year", -1)]).to_list()
        # 取不重複的學年度
        unique_years = sorted(list(set(s.academic_year for s in settings)), reverse=True)
        self.academic_year_options = [{"label": year, "value": year} for year in unique_years]
        
        # 設定預設篩選學年度
        if not self.filter_academic_year:
            current_setting = await AcademicYearSetting.get_current()
            if current_setting:
                self.filter_academic_year = current_setting.academic_year
            elif self.academic_year_options:
                self.filter_academic_year = self.academic_year_options[0]["value"]


    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            return
        if not self.is_member_of_any([UserGroup.COURSE_MANAGER, UserGroup.ADMIN]):
            return rx.redirect(self.DEFAULT_UNAUTHORIZED_REDIRECT_PATH) # type: ignore
        
        await self._load_academic_year_options()
        await self.load_courses()

    async def load_courses(self):
        """載入或篩選課程列表"""
        query_conditions: Dict[str, Any] = {}
        if self.filter_academic_year:
            query_conditions["academic_year"] = self.filter_academic_year
        
        if self.search_term:
            search_regex = {"$regex": self.search_term, "$options": "i"}
            query_conditions["$or"] = [
                {"course_name": search_regex},
                {"course_code": search_regex},
                {"instructor_name": search_regex},
            ]
        self.courses_list = await Course.find(query_conditions).sort([("academic_year", -1), ("course_code", 1)]).to_list()

    async def set_filter_academic_year_and_load(self, year: str):
        """設定學年度篩選並重新載入課程"""
        self.filter_academic_year = year
        await self.load_courses()

    async def handle_search_term_change_and_load(self, term: str):
        """設定搜尋詞並重新載入課程"""
        self.search_term = term
        await self.load_courses()

    # --- 新增課程 Modal 相關 ---
    def _reset_add_form(self):
        """重設新增課程表單"""
        default_ay = self.filter_academic_year
        if not default_ay and self.academic_year_options:
            default_ay = self.academic_year_options[0]["value"]
        
        self.add_course_form_data = {
            "academic_year": default_ay or "",
            "course_code": "", "course_name": "", "credits": 0.0,
            "fee_per_credit": 240, "instructor_name": "", "max_students": None,
            "is_open_for_registration": "是", # UI 上用字串 "是"/"否"
            "time_slots": [EMPTY_TIME_SLOT_DICT.copy()] # 預設一個空時段
        }

    def open_add_course_modal(self):
        self._reset_add_form()
        self.show_add_modal = True

    def close_add_course_modal(self):
        self.show_add_modal = False
        self._reset_add_form() # 清理表單

    def add_new_time_slot_to_add_form(self):
        current_slots = self.add_course_form_data.get("time_slots", [])
        current_slots.append(EMPTY_TIME_SLOT_DICT.copy())
        self.add_course_form_data = {**self.add_course_form_data, "time_slots": current_slots}

    def remove_time_slot_from_add_form(self, index: int):
        current_slots = self.add_course_form_data.get("time_slots", [])
        if 0 <= index < len(current_slots):
            current_slots.pop(index)
            self.add_course_form_data = {**self.add_course_form_data, "time_slots": current_slots}
    
    def update_add_form_time_slot(self, index: int, field: str, value: Any):
        """更新新增表單中特定時段的特定欄位"""
        current_slots = self.add_course_form_data.get("time_slots", [])
        if 0 <= index < len(current_slots):
            # 如果是 day_of_week，確保是 int
            if field == "day_of_week" and isinstance(value, str):
                try:
                    value = int(value)
                except ValueError:
                     # 保持原值或設定錯誤提示，這裡暫時忽略錯誤轉換
                    return
            current_slots[index][field] = value
            self.add_course_form_data = {**self.add_course_form_data, "time_slots": current_slots}


    async def handle_add_new_course(self):
        form_data = self.add_course_form_data
        try:
            # 驗證基本欄位
            if not all([form_data.get("academic_year"), form_data.get("course_code"), form_data.get("course_name")]):
                return rx.toast.error("學年度、科目代碼和科目名稱為必填項。") # type: ignore

            # 檢查課程是否已存在
            existing_course = await Course.find_one(
                Course.academic_year == form_data["academic_year"],
                Course.course_code == form_data["course_code"]
            )
            if existing_course:
                return rx.toast.error(f"課程代碼 {form_data['course_code']} 在學年 {form_data['academic_year']} 已存在。") # type: ignore

            time_slots_models = [CourseTimeSlot(**ts_data) for ts_data in form_data.get("time_slots", []) if any(ts_data.values())] # 僅轉換非空時段

            is_open = True if form_data.get("is_open_for_registration", "是") == "是" else False

            new_course_obj = Course(
                academic_year=form_data["academic_year"],
                course_code=form_data["course_code"],
                course_name=form_data["course_name"],
                credits=float(form_data.get("credits", 0.0) or 0.0),
                fee_per_credit=int(form_data.get("fee_per_credit", 0) or 0),
                instructor_name=form_data.get("instructor_name"),
                max_students=int(form_data.get("max_students", 0) or 0) if form_data.get("max_students") else None,
                is_open_for_registration=is_open,
                time_slots=time_slots_models
            )
            await new_course_obj.insert()
            self.close_add_course_modal()
            await self.load_courses()
            return rx.toast.success("課程新增成功！") # type: ignore
        except ValidationError as ve:
            # Pydantic 驗證錯誤 (主要來自 CourseTimeSlot)
            error_msgs = [f"時段資料錯誤: {err['loc'][-1] if err['loc'] else '未知欄位'} - {err['msg']}" for err in ve.errors()]
            return rx.toast.error(f"新增失敗: {'; '.join(error_msgs)}") # type: ignore
        except Exception as e:
            return rx.toast.error(f"新增課程失敗：{str(e)}") # type: ignore

    # --- 修改課程 Modal 相關 ---
    def _reset_edit_form(self):
        self.editing_course_id = None
        self.edit_course_form_data = {}

    async def start_edit_course(self, course: Course):
        self.editing_course_id = str(course.id)
        # 將 Course 物件轉換為字典，包括 time_slots
        form_data = course.model_dump(exclude={"id", "total_fee"}) # total_fee 是 computed
        form_data["is_open_for_registration"] = "是" if course.is_open_for_registration else "否"
        # time_slots 也需要是 dict list
        form_data["time_slots"] = [ts.model_dump() for ts in course.time_slots]
        self.edit_course_form_data = form_data
        self.show_edit_modal = True

    def close_edit_course_modal(self):
        self.show_edit_modal = False
        self._reset_edit_form()

    def add_new_time_slot_to_edit_form(self):
        current_slots = self.edit_course_form_data.get("time_slots", [])
        current_slots.append(EMPTY_TIME_SLOT_DICT.copy())
        self.edit_course_form_data = {**self.edit_course_form_data, "time_slots": current_slots}

    def remove_time_slot_from_edit_form(self, index: int):
        current_slots = self.edit_course_form_data.get("time_slots", [])
        if 0 <= index < len(current_slots):
            current_slots.pop(index)
            self.edit_course_form_data = {**self.edit_course_form_data, "time_slots": current_slots}
            
    def update_edit_form_time_slot(self, index: int, field: str, value: Any):
        """更新編輯表單中特定時段的特定欄位"""
        current_slots = self.edit_course_form_data.get("time_slots", [])
        if 0 <= index < len(current_slots):
            if field == "day_of_week" and isinstance(value, str):
                try:
                    value = int(value)
                except ValueError:
                    return 
            current_slots[index][field] = value
            self.edit_course_form_data = {**self.edit_course_form_data, "time_slots": current_slots}


    async def handle_save_edited_course(self):
        if not self.editing_course_id:
            return rx.toast.error("未指定要編輯的課程。") # type: ignore
        
        form_data = self.edit_course_form_data
        try:
            course_to_update = await Course.get(PydanticObjectId(self.editing_course_id))
            if not course_to_update:
                return rx.toast.error("找不到要編輯的課程。") # type: ignore

            # 檢查 course_code 是否與其他課程衝突 (如果 academic_year 或 course_code 有變動)
            if (course_to_update.academic_year != form_data.get("academic_year") or \
                course_to_update.course_code != form_data.get("course_code")):
                existing_course = await Course.find_one(
                    Course.academic_year == form_data.get("academic_year"),
                    Course.course_code == form_data.get("course_code"),
                    Course.id != PydanticObjectId(self.editing_course_id) # 排除自身
                )
                if existing_course:
                    return rx.toast.error(f"課程代碼 {form_data.get('course_code')} 在學年 {form_data.get('academic_year')} 已被其他課程使用。") # type: ignore

            time_slots_models = [CourseTimeSlot(**ts_data) for ts_data in form_data.get("time_slots", []) if any(ts_data.values())]
            is_open = True if form_data.get("is_open_for_registration", "是") == "是" else False

            # 更新欄位
            course_to_update.academic_year = form_data.get("academic_year", course_to_update.academic_year)
            course_to_update.course_code = form_data.get("course_code", course_to_update.course_code)
            course_to_update.course_name = form_data.get("course_name", course_to_update.course_name)
            course_to_update.credits = float(form_data.get("credits", course_to_update.credits) or 0.0)
            course_to_update.fee_per_credit = int(form_data.get("fee_per_credit", course_to_update.fee_per_credit) or 0)
            course_to_update.instructor_name = form_data.get("instructor_name", course_to_update.instructor_name)
            max_s = form_data.get("max_students")
            course_to_update.max_students = int(max_s) if isinstance(max_s, (str, int)) and str(max_s).isdigit() else None

            course_to_update.is_open_for_registration = is_open
            course_to_update.time_slots = time_slots_models
            
            await course_to_update.save()
            self.close_edit_course_modal()
            await self.load_courses()
            return rx.toast.success("課程修改成功！") # type: ignore
        except ValidationError as ve:
            error_msgs = [f"時段資料錯誤: {err['loc'][-1] if err['loc'] else '未知欄位'} - {err['msg']}" for err in ve.errors()]
            return rx.toast.error(f"修改失敗: {'; '.join(error_msgs)}") # type: ignore
        except Exception as e:
            return rx.toast.error(f"修改課程失敗：{str(e)}") # type: ignore

    # --- 刪除課程 ---
    async def handle_delete_course_confirmed(self, course_id_str: str):
        try:
            obj_id = PydanticObjectId(course_id_str)
            enrollments_exist = await Enrollment.find(Enrollment.course_id.id == obj_id).count() # type: ignore
            if enrollments_exist > 0:
                return rx.toast.error("無法刪除：此課程已有學生選課記錄。") # type: ignore
            
            course_to_delete = await Course.get(obj_id)
            if course_to_delete:
                await course_to_delete.delete()
                await self.load_courses()
                return rx.toast.info("課程已刪除。") # type: ignore
            return rx.toast.error("找不到要刪除的課程。") # type: ignore
        except Exception as e:
            return rx.toast.error(f"刪除課程失敗: {str(e)}") # type: ignore

    def confirm_delete_course(self, course_id: str):
        # rx.window_confirm 期望一個同步的 callable 或 JavaScript。
        # 為了處理異步操作，我們將在確認後調用一個事件。
        # 這裡我們直接返回一個 JavaScript 腳本來觸發一個事件。
        # 或者，更簡單的方式是讓 on_yes 呼叫一個同步的 handler，
        # 該 handler 再去呼叫 async 的 handle_delete_course_confirmed。
        # 為了簡化，我們假設 UI 會處理這個 confirm，然後直接呼叫 handle_delete_course_confirmed。
        # 在實際 UI 中，通常會用一個 rx.alert_dialog 來做確認。
        # 此處僅為示意，實際的 confirm 應在 UI 層面處理，然後調用 handle_delete_course_confirmed。
        # 例如，UI 按鈕的 on_click 可以是 lambda: self.set_course_to_delete_id(course_id)
        # 然後一個 rx.alert_dialog 的確認按鈕再 on_click=self.handle_delete_course_confirmed_wrapper
        # 此處簡化為直接調用，UI 層面應有確認機制。
        return self.handle_delete_course_confirmed(course_id)


    # --- CSV 匯入 ---
    async def handle_csv_upload(self, files: List[rx.UploadFile]):
        self.csv_import_feedback = "正在處理檔案..."
        if not files:
            self.csv_import_feedback = "請選擇要上傳的 CSV 檔案。"
            return rx.toast.warning(self.csv_import_feedback) # type: ignore
        
        try:
            file_content_bytes = await files[0].read()
            default_ay = self.filter_academic_year
            if not default_ay:
                current_setting = await AcademicYearSetting.get_current()
                if current_setting:
                    default_ay = current_setting.academic_year
                elif self.academic_year_options: # 如果系統沒設定，但選項有，用第一個
                     default_ay = self.academic_year_options[0]["value"]
                else: # 連選項都沒有，無法判斷預設學年
                    self.csv_import_feedback = "錯誤：無法確定預設學年度，請先設定或篩選一個學年度。"
                    return rx.toast.error(self.csv_import_feedback) # type: ignore

            results = await csv_utils.import_courses_from_csv(file_content_bytes, default_ay)
            
            feedback_lines = []
            if results["success"]:
                feedback_lines.append(f"成功匯入 {len(results['success'])} 筆課程。")
            if results["errors"]:
                feedback_lines.append(f"匯入失敗 {len(results['errors'])} 筆。錯誤詳情:")
                feedback_lines.extend([f"- {err}" for err in results["errors"][:10]]) # 最多顯示10條錯誤
                if len(results["errors"]) > 10:
                    feedback_lines.append("...還有更多錯誤未顯示。")
            
            self.csv_import_feedback = "\n".join(feedback_lines)
            if not results["errors"]:
                 rx.toast.success("CSV 課程資料匯入成功！") # type: ignore
            elif results["success"]:
                 rx.toast.warning("CSV 課程資料部分匯入成功，部分失敗。") # type: ignore
            else:
                 rx.toast.error("CSV 課程資料匯入失敗。") # type: ignore

            await self.load_courses() # 重新載入課程列表
        except Exception as e:
            self.csv_import_feedback = f"CSV 檔案處理失敗：{str(e)}"
            return rx.toast.error(self.csv_import_feedback) # type: ignore

    # Helper to set nested form data reactively
    def set_form_data_value(self, form_var_name: str, key: str, value: Any):
        """
        通用方法，用於更新 add_course_form_data 或 edit_course_form_data 中的值。
        form_var_name: "add_course_form_data" 或 "edit_course_form_data"
        """
        current_form_data = getattr(self, form_var_name)
        # 確保是字典的副本，以觸發 rx.Var 的更新
        new_form_data = current_form_data.copy()
        new_form_data[key] = value
        setattr(self, form_var_name, new_form_data)
