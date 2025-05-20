import reflex as rx
from typing import List, Optional, Dict, Any
from beanie.odm.fields import PydanticObjectId

from .auth import AuthState
from ..models.users import User, UserGroup
from ..models.required_course import RequiredCourse
# from ..utils.csv_utils import parse_required_courses_csv, RequiredCourseCSVRow # 假設的 CSV 工具

class ManagerStudentsState(AuthState):
    """管理課程管理者操作學生應重補修名單的狀態與邏輯"""

    required_courses_list: rx.Var[List[RequiredCourse]] = rx.Var([])
    search_term: rx.Var[str] = "" # 可搜尋學號、姓名、科目名稱/代碼等

    # Modal 控制
    show_add_modal: rx.Var[bool] = False
    show_edit_modal: rx.Var[bool] = False
    
    current_record_id_for_edit: rx.Var[Optional[str]] = None
    
    # 表單資料綁定
    # TODO: 根據 RequiredCourse 模型設計表單資料結構
    #       特別注意 user_id 的關聯方式，可能需要透過學號或 Email 查找 User
    add_form_data: rx.Var[Dict[str, Any]] = rx.Var({
        "user_identifier": "", # 用於查找 User (例如學號或 Email)
        "academic_year_taken": "", # TODO: 應有預設或選擇器
        "course_code": "",
        "course_name": "",
        "original_grade": "",
        "is_remedied": False
    })
    edit_form_data: rx.Var[Dict[str, Any]] = rx.Var({})

    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            return
        if UserGroup.COURSE_MANAGER not in self.current_user_groups:
            # return rx.redirect("/unauthorized")
            pass
        await self.load_records()

    async def load_records(self):
        """載入或篩選學生應重補修記錄列表"""
        # TODO: 根據 search_term 查詢 RequiredCourse
        #       需要 fetch_links=True 或額外查詢 User 以顯示學生資訊
        # query_conditions = {}
        # if self.search_term:
        #     # 構建多欄位模糊查詢，例如 user.fullname, user.student_id, course_name, course_code
        #     # 這部分查詢可能較複雜，需要仔細設計
        #     pass
        # self.required_courses_list = await RequiredCourse.find(query_conditions, fetch_links=True).to_list()
        print(f"TODO: ManagerStudentsState.load_records 尚未從資料庫載入，搜尋詞: {self.search_term}")
        # 模擬資料
        # user1 = User(google_sub="sub1", email="student1@example.com", fullname="學生一", student_id="S001")
        # self.required_courses_list = [
        #     RequiredCourse(id=PydanticObjectId(), user_id=user1, academic_year_taken="112-1", course_code="REQ001", course_name="必修國文(上)", original_grade="50"),
        #     RequiredCourse(id=PydanticObjectId(), user_id=user1, academic_year_taken="112-1", course_code="REQ002", course_name="必修數學(上)", original_grade="40")
        # ]


    # --- 新增記錄 Modal ---
    def open_add_record_modal(self):
        self.add_form_data = {
            "user_identifier": "", "academic_year_taken": "112-2", # TODO: 預設學年度
            "course_code": "", "course_name": "", "original_grade": "", "is_remedied": False
        }
        self.show_add_modal = True

    def close_add_record_modal(self):
        self.show_add_modal = False

    async def handle_add_new_record(self):
        """處理新增應重補修記錄"""
        # TODO: 從 self.add_form_data 獲取資料
        #       根據 user_identifier (學號/Email) 查找 User 物件
        #       若 User 不存在，提示錯誤或引導創建
        #       創建 RequiredCourse 物件並儲存
        #       成功後關閉 Modal 並重新載入列表
        form_data = self.add_form_data
        try:
            # user_identifier = form_data.get("user_identifier")
            # # found_user = await User.find_one(User.student_id == user_identifier) or await User.find_one(User.email == user_identifier)
            # # if not found_user:
            # #    return rx.toast.error(f"找不到學生：{user_identifier}")
            #
            # # new_record = RequiredCourse(
            # #    user_id=found_user.id,
            # #    academic_year_taken=form_data.get("academic_year_taken"),
            # #    ...
            # # )
            # # await new_record.insert()
            # self.close_add_record_modal()
            # await self.load_records()
            # return rx.toast.success("記錄新增成功！")
            print(f"TODO: handle_add_new_record 尚未實作，表單資料: {form_data}")
            self.close_add_record_modal()
        except Exception as e:
            # return rx.toast.error(f"新增失敗：{e}")
            print(f"TODO: handle_add_new_record 錯誤處理: {e}")

    # --- 修改記錄 Modal ---
    async def start_edit_record(self, record_id_str: str):
        # TODO: 載入記錄並填充 edit_form_data
        #       需要處理 user_identifier 的顯示
        # record_to_edit = await RequiredCourse.get(PydanticObjectId(record_id_str), fetch_links=True)
        # if record_to_edit:
        #     self.edit_form_data = record_to_edit.model_dump(exclude={"id", "user_id"})
        #     if record_to_edit.user_id:
        #         self.edit_form_data["user_identifier"] = record_to_edit.user_id.student_id or record_to_edit.user_id.email
        #     self.current_record_id_for_edit = record_id_str
        #     self.show_edit_modal = True
        # else:
        #     rx.toast.error("找不到要編輯的記錄。")
        print(f"TODO: start_edit_record 尚未實作，記錄 ID: {record_id_str}")

    def close_edit_record_modal(self):
        self.show_edit_modal = False
        self.current_record_id_for_edit = None

    async def handle_save_edited_record(self):
        # TODO: 儲存修改後的記錄
        # if self.current_record_id_for_edit:
        #     record_to_update = await RequiredCourse.get(PydanticObjectId(self.current_record_id_for_edit))
        #     if record_to_update:
        #         # updated_data = self.edit_form_data
        #         # user_identifier = updated_data.pop("user_identifier", None)
        #         # if user_identifier:
        #         #     # 重新查找 User
        #         #     pass
        #         # await record_to_update.update({"$set": updated_data})
        #         # await record_to_update.save() # Beanie 0.24+
        #         self.close_edit_record_modal()
        #         await self.load_records()
        #         return rx.toast.success("記錄修改成功！")
        # return rx.toast.error("修改失敗。")
        print(f"TODO: handle_save_edited_record 尚未實作")
        self.close_edit_record_modal()

    # --- 刪除記錄 ---
    async def handle_delete_record_confirmed(self, record_id_str: str):
        # record_to_delete = await RequiredCourse.get(PydanticObjectId(record_id_str))
        # if record_to_delete:
        #     await record_to_delete.delete()
        #     await self.load_records()
        #     return rx.toast.info("記錄已刪除。")
        # return rx.toast.error("找不到要刪除的記錄。")
        print(f"TODO: handle_delete_record_confirmed 尚未實作，記錄 ID: {record_id_str}")

    def confirm_delete_record(self, record_id: str):
        # return rx.window_confirm(
        #     f"確定要刪除此筆記錄 (ID: {record_id}) 嗎？",
        #     on_yes=lambda: self.handle_delete_record_confirmed(record_id)
        # )
        print(f"TODO: confirm_delete_record 尚未實作，記錄 ID: {record_id}")
        # yield self.handle_delete_record_confirmed(record_id)


    # --- CSV 匯入 ---
    async def handle_csv_upload(self, files: List[rx.UploadFile]):
        """處理 CSV 檔案上傳並匯入學生應重補修名單"""
        # TODO: 規格 3.2 & 6.2
        #       解析 CSV (包含 學號, 學生姓名, 不及格科目之學年度, 不及格科目代碼, 不及格科目名稱, 不及格成績, 學生GoogleEmail)
        #       根據 Email 或學號查找/創建 User
        #       創建 RequiredCourse 記錄
        # if not files:
        #     return rx.toast.warning("請選擇 CSV 檔案。")
        # try:
        #     csv_content = await files[0].read()
        #     # parsed_rows = parse_required_courses_csv(csv_content.decode('utf-8'))
        #     # for row_data in parsed_rows:
        #     #     # 查找 User, 創建 RequiredCourse ...
        #     # await self.load_records()
        #     # return rx.toast.info("CSV 匯入完成。")
        # except Exception as e:
        #     return rx.toast.error(f"CSV 處理失敗：{e}")
        print(f"TODO: handle_csv_upload 尚未實作，檔案數量: {len(files) if files else 0}")
