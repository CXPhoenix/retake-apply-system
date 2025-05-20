import reflex as rx
from typing import List, Optional, Dict, Any
from beanie.odm.fields import PydanticObjectId # 確保匯入

from .auth import AuthState
from ..models.users import UserGroup
from ..models.course import Course, CourseTimeSlot
from ..models.enrollment import Enrollment
# from ..utils.csv_utils import parse_courses_csv, CourseCSVRow # 假設的 CSV 工具函式與模型
# from ..utils.funcs import get_current_academic_year # 假設的輔助函式

class ManagerCoursesState(AuthState):
    """管理課程管理者操作課程的狀態與邏輯"""

    courses_list: rx.Var[List[Course]] = rx.Var([])
    search_term: rx.Var[str] = ""
    
    # Modal 控制
    show_add_modal: rx.Var[bool] = False
    show_edit_modal: rx.Var[bool] = False
    
    # 當前正在編輯的課程
    # TODO: 考慮 current_course_for_edit 的類型，直接用 Course 模型可能更方便綁定表單
    current_course_id_for_edit: rx.Var[Optional[str]] = None 
    
    # 表單資料綁定
    # TODO: 根據 Course 模型 (包含 CourseTimeSlot) 設計更完整的表單資料結構
    #       例如，time_slots 可能是一個 List[Dict]
    add_course_form_data: rx.Var[Dict[str, Any]] = rx.Var({
        "academic_year": "", # TODO: 應預設為當前學年度
        "course_code": "",
        "course_name": "",
        "credits": 0.0,
        "fee_per_credit": 240, # 預設值
        "instructor_name": "",
        "max_students": None,
        "is_open_for_registration": True,
        "time_slots": [] # List of CourseTimeSlot dicts
    })
    # TODO: edit_course_form_data 也需要類似的結構
    edit_course_form_data: rx.Var[Dict[str, Any]] = rx.Var({})

    # CSV 上傳相關
    # TODO: 處理 CSV 上傳的狀態，例如上傳進度、錯誤訊息等
    #       uploaded_file_info: rx.Var[Optional[rx.UploadFile]] = None
    #       csv_import_results: rx.Var[List[str]] = [] # 顯示匯入結果

    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            return
        if UserGroup.COURSE_MANAGER not in self.current_user_groups:
            # 權限不足，可以考慮重導向或顯示訊息
            # return rx.redirect("/unauthorized")
            pass 
        
        # TODO: 載入當前學年度並設定到 add_course_form_data.academic_year
        # current_year = await get_current_academic_year()
        # self.add_course_form_data["academic_year"] = current_year
        
        await self.load_courses()

    async def load_courses(self):
        """載入或篩選課程列表"""
        # TODO: 根據 search_term 和其他可能的篩選條件 (如學年度) 查詢課程
        # query_conditions = {}
        # if self.search_term:
        #     query_conditions["course_name"] = {"$regex": self.search_term, "$options": "i"}
        # self.courses_list = await Course.find(query_conditions).to_list()
        print(f"TODO: ManagerCoursesState.load_courses 尚未從資料庫載入，搜尋詞: {self.search_term}")
        # 模擬資料
        # self.courses_list = [
        #     Course(id=PydanticObjectId(), academic_year="113-1", course_code="MGR001", course_name="管理課程A", credits=3.0, fee_per_credit=240, total_fee=720),
        #     Course(id=PydanticObjectId(), academic_year="113-1", course_code="MGR002", course_name="管理課程B", credits=2.0, fee_per_credit=240, total_fee=480)
        # ]


    # --- 新增課程 Modal 相關 ---
    def open_add_course_modal(self):
        """開啟新增課程 Modal 並重設表單"""
        # TODO: 重設 add_course_form_data 為初始值，特別是 time_slots
        #       並將當前學年度填入 academic_year 欄位
        self.add_course_form_data = {
            "academic_year": "113-1", # TODO: 應來自系統設定
            "course_code": "", "course_name": "", "credits": 0.0,
            "fee_per_credit": 240, "instructor_name": "", "max_students": None,
            "is_open_for_registration": True, "time_slots": []
        }
        self.show_add_modal = True

    def close_add_course_modal(self):
        self.show_add_modal = False

    async def handle_add_new_course(self):
        """處理新增課程表單提交"""
        # TODO: 從 self.add_course_form_data 獲取資料
        #       進行資料驗證 (Pydantic 模型可以在此處發揮作用)
        #       轉換 time_slots 的 dict list 為 List[CourseTimeSlot]
        #       計算 total_fee
        #       創建 Course 物件並儲存到資料庫
        #       成功後關閉 Modal 並重新載入課程列表
        #       處理可能的錯誤 (例如科目代碼重複)
        form_data = self.add_course_form_data
        try:
            # time_slots_models = [CourseTimeSlot(**ts) for ts in form_data.get("time_slots", [])]
            # new_course_obj = Course(
            #     **form_data, # 解包除了 time_slots 以外的欄位
            #     time_slots=time_slots_models
            # )
            # new_course_obj.total_fee = new_course_obj.calculate_total_fee() # 計算總費用
            # await new_course_obj.insert()
            # self.close_add_course_modal()
            # await self.load_courses()
            # return rx.toast.success("課程新增成功！")
            print(f"TODO: handle_add_new_course 尚未實作，表單資料: {form_data}")
            self.close_add_course_modal() # 暫時直接關閉
        except Exception as e:
            # return rx.toast.error(f"新增失敗：{e}")
            print(f"TODO: handle_add_new_course 錯誤處理: {e}")


    # --- 修改課程 Modal 相關 ---
    async def start_edit_course(self, course_id_str: str):
        """開啟修改課程 Modal 並載入課程資料到表單"""
        # TODO: 根據 course_id_str 查詢課程
        #       將課程資料填入 self.edit_course_form_data
        #       (注意 time_slots 需要轉換回 dict list)
        #       設定 self.current_course_id_for_edit = course_id_str
        #       self.show_edit_modal = True
        # course_to_edit = await Course.get(PydanticObjectId(course_id_str))
        # if course_to_edit:
        #     self.edit_course_form_data = course_to_edit.model_dump(exclude={"id"}) # 轉換為 dict
        #     # self.edit_course_form_data["time_slots"] = [ts.model_dump() for ts in course_to_edit.time_slots]
        #     self.current_course_id_for_edit = course_id_str
        #     self.show_edit_modal = True
        # else:
        #     rx.toast.error("找不到要編輯的課程。")
        print(f"TODO: start_edit_course 尚未實作，課程 ID: {course_id_str}")


    def close_edit_course_modal(self):
        self.show_edit_modal = False
        self.current_course_id_for_edit = None

    async def handle_save_edited_course(self):
        """處理修改課程表單提交"""
        # TODO: 從 self.edit_course_form_data 和 self.current_course_id_for_edit 獲取資料
        #       進行資料驗證
        #       更新 Course 物件並儲存到資料庫
        #       成功後關閉 Modal 並重新載入課程列表
        # if self.current_course_id_for_edit:
        #     course_to_update = await Course.get(PydanticObjectId(self.current_course_id_for_edit))
        #     if course_to_update:
        #         # updated_data = self.edit_course_form_data
        #         # time_slots_models = [CourseTimeSlot(**ts) for ts in updated_data.get("time_slots", [])]
        #         # await course_to_update.update({"$set": {**updated_data, "time_slots": time_slots_models}})
        #         # course_to_update.total_fee = course_to_update.calculate_total_fee()
        #         # await course_to_update.save()
        #         self.close_edit_course_modal()
        #         await self.load_courses()
        #         return rx.toast.success("課程修改成功！")
        # return rx.toast.error("修改失敗，找不到課程。")
        print(f"TODO: handle_save_edited_course 尚未實作")
        self.close_edit_course_modal() # 暫時直接關閉

    # --- 刪除課程 ---
    async def handle_delete_course_confirmed(self, course_id_str: str):
        """確認後執行刪除課程"""
        # TODO: 檢查是否有相關選課記錄 (Enrollment)，若有則提示無法刪除
        #       enrollments_exist = await Enrollment.find(Enrollment.course_id == PydanticObjectId(course_id_str)).count()
        #       if enrollments_exist > 0:
        #           return rx.toast.error("無法刪除：此課程已有學生選課記錄。")
        # course_to_delete = await Course.get(PydanticObjectId(course_id_str))
        # if course_to_delete:
        #     await course_to_delete.delete()
        #     await self.load_courses()
        #     return rx.toast.info("課程已刪除。")
        # return rx.toast.error("找不到要刪除的課程。")
        print(f"TODO: handle_delete_course_confirmed 尚未實作，課程 ID: {course_id_str}")


    def confirm_delete_course(self, course_id: str):
        """顯示刪除確認對話框"""
        # TODO: 這裡的 on_yes 應該是一個可以被 rx.window_confirm 正確呼叫的事件。
        #       直接傳遞 async 方法可能需要調整，或者使用 rx.call_script。
        #       一個常見模式是 confirm_delete_course 設定一個 rx.Var (e.g., course_id_to_delete_confirmed)
        #       然後另一個 event handler 觀察此 Var 變化來執行刪除。
        #       或者，on_yes 呼叫一個同步的 event handler，該 handler 內部再用 await。
        # return rx.window_confirm(
        #     f"確定要刪除課程 (ID: {course_id}) 嗎？此操作無法復原。",
        #     on_yes=lambda: self.handle_delete_course_confirmed(course_id) # 這樣傳遞可能會有問題
        # )
        print(f"TODO: confirm_delete_course 尚未完整實作，課程 ID: {course_id}")
        # 暫時模擬直接刪除 (不推薦)
        # yield self.handle_delete_course_confirmed(course_id) # 修正 yield 的使用


    # --- CSV 匯入 ---
    async def handle_csv_upload(self, files: List[rx.UploadFile]):
        """處理 CSV 檔案上傳並匯入課程"""
        # TODO: 規格 3.1 & 6.1
        #       檢查檔案類型和大小
        #       讀取檔案內容 (files[0].read())
        #       調用 utils.csv_utils 中的 parse_courses_csv 進行解析與驗證
        #       根據解析結果 (成功/失敗列表) 批量創建 Course 物件
        #       顯示匯入結果給使用者 (成功幾筆，失敗幾筆及原因)
        #       完成後重新載入課程列表
        if not files:
            # return rx.toast.warning("請選擇要上傳的 CSV 檔案。")
            print("請選擇要上傳的 CSV 檔案。") # 改為 print
            return
        try:
            # csv_content = await files[0].read()
            # parsed_data = parse_courses_csv(csv_content.decode('utf-8')) # 假設的解析函式
            # success_count = 0
            # error_messages = []
            # for row in parsed_data:
            #     if isinstance(row, CourseCSVRow) and row.is_valid:
            #         # 轉換為 Course 物件並儲存
            #         success_count +=1
            #     else:
            #         error_messages.append(f"第 {row.line_number} 行錯誤: {row.error}")
            # await self.load_courses()
            # return rx.toast.info(f"CSV 匯入完成：成功 {success_count} 筆。錯誤：{len(error_messages)} 筆。")
            print(f"TODO: CSV 匯入成功/失敗邏輯尚未實作")
        except Exception as e:
            # return rx.toast.error(f"CSV 檔案處理失敗：{e}")
            print(f"CSV 檔案處理失敗：{e}")
        print(f"TODO: handle_csv_upload 尚未實作，檔案數量: {len(files) if files else 0}")

# 移除類別定義之後的無效 Python 程式碼 (原為 Markdown 格式的說明文字)
