"""課程管理頁面的狀態管理模組。

此模組定義了 `ManagerCoursesState` 類別，繼承自 `AuthState`，
負責處理課程管理者（及系統管理者）管理課程資料頁面的所有後端邏輯，
包括課程的增刪改查、CSV 匯入等。
"""
import reflex as rx
from typing import List, Optional, Dict, Any
from beanie.odm.fields import PydanticObjectId # type: ignore # 用於將字串 ID 轉換為 ObjectId
from pydantic import ValidationError # 用於處理 CourseTimeSlot 驗證錯誤

from .auth import AuthState # 基礎身份驗證狀態
from ..models.users import UserGroup # 用於權限檢查
from ..models.course import Course, CourseTimeSlot, VALID_PERIODS # 課程模型及相關常數
from ..models.enrollment import Enrollment # 用於檢查課程是否被選修
from ..models.academic_year_setting import AcademicYearSetting # 用於獲取學年度選項
from ..utils import csv_utils # CSV 處理工具

# 預設的空時段字典，用於初始化新增課程時的時段表單
EMPTY_TIME_SLOT_DICT: Dict[str, Any] = {
    "week_number": None,
    "day_of_week": 1,  # 預設星期一
    "period": VALID_PERIODS[0] if VALID_PERIODS else "D1", # 預設第一個有效節次
    "start_time": "08:00",
    "end_time": "08:50",
    "location": ""
}

class ManagerCoursesState(AuthState):
    """管理課程管理者操作課程資料的狀態與相關邏輯。

    Attributes:
        courses_list (rx.Var[List[Course]]): 顯示在頁面上的課程列表。
        search_term (rx.Var[str]): 用於篩選課程列表的搜尋關鍵字。
        filter_academic_year (rx.Var[str]): 當前用於篩選課程的學年度。
        academic_year_options (rx.Var[List[Dict[str, str]]]):
            提供給學年度篩選下拉選單的選項列表。
        show_add_modal (rx.Var[bool]): 控制是否顯示新增課程的彈出視窗。
        show_edit_modal (rx.Var[bool]): 控制是否顯示編輯課程的彈出視窗。
        editing_course_id (rx.Var[Optional[str]]): 當前正在編輯的課程 ID (字串形式)。
        add_course_form_data (rx.Var[Dict[str, Any]]):
            綁定到新增課程表單的資料字典。
        edit_course_form_data (rx.Var[Dict[str, Any]]):
            綁定到編輯課程表單的資料字典。
        csv_import_feedback (rx.Var[str]): 用於顯示 CSV 匯入操作結果的訊息。
    """

    courses_list: rx.Var[List[Course]] = rx.Var([])
    search_term: rx.Var[str] = ""
    filter_academic_year: rx.Var[str] = ""
    academic_year_options: rx.Var[List[Dict[str, str]]] = rx.Var([])

    # --- Modal 顯示控制 ---
    show_add_modal: rx.Var[bool] = False
    show_edit_modal: rx.Var[bool] = False

    editing_course_id: rx.Var[Optional[str]] = None

    # --- 表單資料 ---
    add_course_form_data: rx.Var[Dict[str, Any]] = rx.Var({})
    edit_course_form_data: rx.Var[Dict[str, Any]] = rx.Var({})

    # --- CSV 匯入相關 ---
    csv_import_feedback: rx.Var[str] = ""

    async def _load_academic_year_options(self):
        """內部輔助函式，從 `AcademicYearSetting` 載入不重複的學年度選項，
        並設定預設的 `filter_academic_year`。
        """
        settings = await AcademicYearSetting.find_all(sort=[("academic_year", -1)]).to_list()
        # 提取不重複的學年度並排序
        unique_years = sorted(list(set(s.academic_year for s in settings)), reverse=True)
        self.academic_year_options = [{"label": year, "value": year} for year in unique_years]

        # 設定預設篩選學年度：優先使用當前生效學年，其次用選項中的最新學年
        if not self.filter_academic_year: # 僅在尚未設定時進行預設
            current_setting = await AcademicYearSetting.get_current()
            if current_setting:
                self.filter_academic_year = current_setting.academic_year
            elif self.academic_year_options: # 若無當前生效學年，但選項列表不為空
                self.filter_academic_year = self.academic_year_options[0]["value"] # 使用最新的學年度作為預設

    async def on_page_load(self):
        """課程管理頁面載入時執行的非同步操作。

        檢查使用者登入狀態和權限 (課程管理者或系統管理員)，
        若符合則載入學年度選項和初始課程列表。
        若未登入或權限不足，則導向至未授權頁面。
        """
        if not self.is_hydrated or not self.token_is_valid:
            return # 等待客戶端水合或 token 驗證完成

        if not self.is_member_of_any([UserGroup.COURSE_MANAGER, UserGroup.SYSTEM_ADMIN]):
            return rx.redirect(getattr(self, "DEFAULT_UNAUTHORIZED_REDIRECT_PATH", "/")) # type: ignore

        await self._load_academic_year_options() # 載入學年度選項
        await self.load_courses() # 載入初始課程列表

    async def load_courses(self):
        """根據 `filter_academic_year` 和 `search_term` 從資料庫載入課程列表。

        查詢結果按學年度降序、科目代碼升序排列，並更新 `self.courses_list`。
        """
        query_conditions: Dict[str, Any] = {}
        if self.filter_academic_year:
            query_conditions["academic_year"] = self.filter_academic_year

        if self.search_term:
            search_regex = {"$regex": self.search_term, "$options": "i"} # 不區分大小寫的模糊查詢
            query_conditions["$or"] = [ # 滿足任一條件即可
                {"course_name": search_regex},
                {"course_code": search_regex},
                {"instructor_name": search_regex},
            ]
        self.courses_list = await Course.find(query_conditions).sort(
            [("academic_year", -1), ("course_code", 1)] # 排序：學年降序，科目代碼升序
        ).to_list()

    async def set_filter_academic_year_and_load(self, year: str):
        """設定學年度篩選條件並觸發重新載入課程列表。

        Args:
            year (str): 要篩選的學年度字串。
        """
        self.filter_academic_year = year
        await self.load_courses()

    async def handle_search_term_change_and_load(self, term: str):
        """處理搜尋關鍵字變更並觸發重新載入課程列表。

        Args:
            term (str): 新的搜尋關鍵字。
        """
        self.search_term = term
        await self.load_courses()

    # --- 新增課程 Modal 相關方法 ---
    def _reset_add_form(self):
        """內部輔助函式，重設用於新增課程的表單資料 (`add_course_form_data`) 為預設值。

        預設學年度會嘗試使用目前篩選的學年度，若無則使用學年度選項中的第一個。
        預設包含一個空的上課時段。
        """
        default_ay = self.filter_academic_year
        if not default_ay and self.academic_year_options: # 若篩選器未選，但選項存在
            default_ay = self.academic_year_options[0]["value"] # 使用選項中的第一個作為預設

        self.add_course_form_data = {
            "academic_year": default_ay or "", # 若連選項都沒有，則為空字串
            "course_code": "",
            "course_name": "",
            "credits": 0.0,
            "fee_per_credit": 240, # 預設每學分費用
            "instructor_name": "",
            "max_students": None, # 人數上限預設為 None (無限制)
            "is_open_for_registration": "是", # UI 上用字串 "是"/"否"，預設為 "是"
            "time_slots": [EMPTY_TIME_SLOT_DICT.copy()] # 預設一個空的上課時段
        }

    def open_add_course_modal(self):
        """開啟新增課程的彈出視窗，並重設表單資料。"""
        self._reset_add_form()
        self.show_add_modal = True

    def close_add_course_modal(self):
        """關閉新增課程的彈出視窗，並重設(清理)表單資料。"""
        self.show_add_modal = False
        self._reset_add_form() # 確保關閉時表單被清理

    def add_new_time_slot_to_add_form(self):
        """在新增課程表單中動態添加一個新的空上課時段。"""
        current_slots = self.add_course_form_data.get("time_slots", [])
        current_slots.append(EMPTY_TIME_SLOT_DICT.copy()) # 添加一個新的空時段副本
        # 更新整個表單資料以觸發 Reflex 的狀態變更
        self.add_course_form_data = {**self.add_course_form_data, "time_slots": current_slots}

    def remove_time_slot_from_add_form(self, index: int):
        """從新增課程表單中移除指定索引的上課時段。

        Args:
            index (int): 要移除的時段在 `time_slots` 列表中的索引。
        """
        current_slots = self.add_course_form_data.get("time_slots", [])
        if 0 <= index < len(current_slots):
            current_slots.pop(index)
            self.add_course_form_data = {**self.add_course_form_data, "time_slots": current_slots}

    def update_add_form_time_slot(self, index: int, field: str, value: Any):
        """更新新增課程表單中，指定索引的上課時段內的特定欄位值。

        Args:
            index (int): 要更新的時段在 `time_slots` 列表中的索引。
            field (str): 要更新的時段字典中的鍵 (欄位名稱)。
            value (Any): 要設定的新值。
        """
        current_slots = self.add_course_form_data.get("time_slots", [])
        if 0 <= index < len(current_slots):
            # 特殊處理：若更新的是星期 (day_of_week)，且傳入值為字串，則嘗試轉為整數
            if field == "day_of_week" and isinstance(value, str):
                try:
                    value = int(value)
                except ValueError:
                     # 若轉換失敗 (例如空字串)，保持原樣或可考慮設定錯誤提示。此處暫不處理。
                    return
            current_slots[index][field] = value
            self.add_course_form_data = {**self.add_course_form_data, "time_slots": current_slots}

    async def handle_add_new_course(self):
        """處理新增課程表單的提交事件。

        此方法會執行以下操作：
        1. 驗證表單中的必填欄位（學年度、科目代碼、科目名稱）。
        2. 檢查具有相同學年度和科目代碼的課程是否已存在。
        3. 將表單中的上課時段資料轉換為 `CourseTimeSlot` 模型列表。
        4. 創建新的 `Course` 物件並插入資料庫。
        5. 若成功，則關閉 Modal、重新載入課程列表並顯示成功訊息。
        6. 若發生 Pydantic 驗證錯誤 (通常來自 `CourseTimeSlot`) 或其他例外，則顯示錯誤訊息。
        """
        form_data = self.add_course_form_data
        try:
            # 基本欄位驗證
            if not all([form_data.get("academic_year"), form_data.get("course_code"), form_data.get("course_name")]):
                return rx.toast.error("學年度、科目代碼和科目名稱為必填項。") # type: ignore

            # 檢查課程是否已存在 (相同學年、相同代碼)
            existing_course = await Course.find_one(
                Course.academic_year == form_data["academic_year"],
                Course.course_code == form_data["course_code"]
            )
            if existing_course:
                return rx.toast.error(f"課程代碼 '{form_data['course_code']}' 在學年 '{form_data['academic_year']}' 已存在。") # type: ignore

            # 轉換上課時段資料，僅處理與預設空時段不同的時段字典
            time_slots_models = [
                CourseTimeSlot(**ts_data)
                for ts_data in form_data.get("time_slots", [])
                if ts_data != EMPTY_TIME_SLOT_DICT # 只有當使用者修改過預設空時段時才轉換
            ]
            # 如果所有時段都與預設空時段相同，則 time_slots_models 會是空列表，這是預期行為。
            # 如果業務邏輯要求至少要有一個有效時段，則應在此處添加額外檢查。

            is_open_for_reg = True if form_data.get("is_open_for_registration", "是") == "是" else False

            new_course_obj = Course(
                academic_year=form_data["academic_year"],
                course_code=form_data["course_code"],
                course_name=form_data["course_name"],
                credits=float(form_data.get("credits", 0.0) or 0.0), # 確保為 float
                fee_per_credit=int(form_data.get("fee_per_credit", 0) or 0), # 確保為 int
                instructor_name=form_data.get("instructor_name"),
                max_students=int(form_data.get("max_students", 0) or 0) if form_data.get("max_students") else None, # 處理 None 或空字串
                is_open_for_registration=is_open_for_reg,
                time_slots=time_slots_models
            )
            await new_course_obj.insert() # 插入新課程至資料庫

            self.close_add_course_modal() # 關閉新增 Modal
            await self.load_courses() # 重新載入課程列表以顯示新課程
            return rx.toast.success(f"課程 '{new_course_obj.course_name}' 新增成功！") # type: ignore
        except ValidationError as ve:
            # 處理 Pydantic 模型驗證錯誤 (主要來自 CourseTimeSlot)
            error_messages = [
                f"時段資料錯誤 (欄位: {err['loc'][-1] if err['loc'] else '未知'}): {err['msg']}"
                for err in ve.errors()
            ]
            return rx.toast.error(f"新增失敗，資料驗證錯誤: {'; '.join(error_messages)}") # type: ignore
        except Exception as e:
            # 應記錄更詳細的錯誤日誌
            # await SystemLog.log(LogLevel.ERROR, f"新增課程失敗: {e}", source="ManagerCoursesState", details=form_data)
            return rx.toast.error(f"新增課程時發生未預期錯誤：{str(e)}") # type: ignore

    # --- 修改課程 Modal 相關方法 ---
    def _reset_edit_form(self):
        """內部輔助函式，重設用於編輯課程的表單資料及相關狀態。"""
        self.editing_course_id = None
        self.edit_course_form_data = {}

    async def start_edit_course(self, course: Course):
        """準備並開啟編輯指定課程的彈出視窗。

        將選定課程的資料填充到 `edit_course_form_data` 中。

        Args:
            course (Course): 要編輯的課程物件。
        """
        self.editing_course_id = str(course.id)
        # 將 Course 物件轉換為字典，包括 time_slots
        form_data = course.model_dump(exclude={"id", "total_fee"}) # total_fee 是 computed
        form_data["is_open_for_registration"] = "是" if course.is_open_for_registration else "否"
        # time_slots 也需要是 dict list
        form_data["time_slots"] = [ts.model_dump() for ts in course.time_slots]
        self.edit_course_form_data = form_data
        self.show_edit_modal = True

    def close_edit_course_modal(self):
        """關閉編輯課程的彈出視窗，並重設相關表單資料。"""
        self.show_edit_modal = False
        self._reset_edit_form() # 清理表單

    def add_new_time_slot_to_edit_form(self):
        """在編輯課程表單中動態添加一個新的空上課時段。"""
        current_slots = self.edit_course_form_data.get("time_slots", [])
        current_slots.append(EMPTY_TIME_SLOT_DICT.copy())
        self.edit_course_form_data = {**self.edit_course_form_data, "time_slots": current_slots}

    def remove_time_slot_from_edit_form(self, index: int):
        """從編輯課程表單中移除指定索引的上課時段。

        Args:
            index (int): 要移除的時段在 `time_slots` 列表中的索引。
        """
        current_slots = self.edit_course_form_data.get("time_slots", [])
        if 0 <= index < len(current_slots):
            current_slots.pop(index)
            self.edit_course_form_data = {**self.edit_course_form_data, "time_slots": current_slots}

    def update_edit_form_time_slot(self, index: int, field: str, value: Any):
        """更新編輯課程表單中，指定索引的上課時段內的特定欄位值。

        Args:
            index (int): 要更新的時段在 `time_slots` 列表中的索引。
            field (str): 要更新的時段字典中的鍵 (欄位名稱)。
            value (Any): 要設定的新值。
        """
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
        """處理儲存已編輯課程資料的邏輯。

        此方法會：
        1. 驗證是否有正在編輯的課程 ID。
        2. 獲取資料庫中的課程物件。
        3. 若學年度或科目代碼有變動，檢查是否與其他現有課程衝突。
        4. 將表單中的上課時段資料轉換為 `CourseTimeSlot` 模型列表。
        5. 更新課程物件的各個欄位。
        6. 儲存變更至資料庫。
        7. 若成功，則關閉 Modal、重新載入課程列表並顯示成功訊息。
        8. 若發生 Pydantic 驗證錯誤或其他例外，則顯示錯誤訊息。
        """
        if not self.editing_course_id:
            return rx.toast.error("錯誤：未指定要編輯的課程。") # type: ignore

        form_data = self.edit_course_form_data
        try:
            course_to_update = await Course.get(PydanticObjectId(self.editing_course_id))
            if not course_to_update:
                return rx.toast.error("錯誤：找不到要編輯的課程。") # type: ignore

            # 檢查課程代碼唯一性 (如果學年或代碼有變更)
            if (course_to_update.academic_year != form_data.get("academic_year") or \
                course_to_update.course_code != form_data.get("course_code")):
                existing_course = await Course.find_one(
                    Course.academic_year == form_data.get("academic_year"),
                    Course.course_code == form_data.get("course_code"),
                    Course.id != PydanticObjectId(self.editing_course_id) # 排除自身
                )
                if existing_course:
                    return rx.toast.error(f"課程代碼 '{form_data.get('course_code')}' 在學年 '{form_data.get('academic_year')}' 已被其他課程使用。") # type: ignore

            time_slots_models = [
                CourseTimeSlot(**ts_data)
                for ts_data in form_data.get("time_slots", [])
                if ts_data != EMPTY_TIME_SLOT_DICT
            ]
            is_open = True if form_data.get("is_open_for_registration", "是") == "是" else False

            # 更新課程物件的欄位
            course_to_update.academic_year = form_data.get("academic_year", course_to_update.academic_year)
            course_to_update.course_code = form_data.get("course_code", course_to_update.course_code)
            course_to_update.course_name = form_data.get("course_name", course_to_update.course_name)
            course_to_update.credits = float(form_data.get("credits", course_to_update.credits) or 0.0)
            course_to_update.fee_per_credit = int(form_data.get("fee_per_credit", course_to_update.fee_per_credit) or 0)
            course_to_update.instructor_name = form_data.get("instructor_name", course_to_update.instructor_name)
            max_s_str = str(form_data.get("max_students", "")) # 確保是字串以便 isdigit
            course_to_update.max_students = int(max_s_str) if max_s_str.isdigit() else None

            course_to_update.is_open_for_registration = is_open
            course_to_update.time_slots = time_slots_models

            await course_to_update.save() # 儲存變更
            self.close_edit_course_modal() # 關閉編輯 Modal
            await self.load_courses() # 重新載入課程列表
            return rx.toast.success(f"課程 '{course_to_update.course_name}' 修改成功！") # type: ignore
        except ValidationError as ve:
            error_messages = [
                f"時段資料錯誤 (欄位: {err['loc'][-1] if err['loc'] else '未知'}): {err['msg']}"
                for err in ve.errors()
            ]
            return rx.toast.error(f"修改失敗，資料驗證錯誤: {'; '.join(error_messages)}") # type: ignore
        except Exception as e:
            return rx.toast.error(f"修改課程時發生未預期錯誤：{str(e)}") # type: ignore

    # --- 刪除課程 ---
    async def handle_delete_course_confirmed(self, course_id_str: str):
        """處理確認刪除課程的操作。

        在刪除前會檢查此課程是否已有學生選課記錄。

        Args:
            course_id_str (str): 要刪除的課程 ID 字串。
        """
        try:
            obj_id = PydanticObjectId(course_id_str)
            # 檢查是否有學生已選修此課程
            enrollments_exist = await Enrollment.find(Enrollment.course_id.id == obj_id).count() # type: ignore[attr-defined]
            if enrollments_exist > 0:
                return rx.toast.error("無法刪除：此課程已有學生選課記錄。請先處理相關選課資料。") # type: ignore

            course_to_delete = await Course.get(obj_id)
            if course_to_delete:
                await course_to_delete.delete()
                await self.load_courses() # 重新載入課程列表
                return rx.toast.info(f"課程 '{course_to_delete.course_name}' 已成功刪除。") # type: ignore
            return rx.toast.error("錯誤：找不到要刪除的課程。") # type: ignore
        except Exception as e:
            return rx.toast.error(f"刪除課程時發生錯誤: {str(e)}") # type: ignore

    def confirm_delete_course(self, course_id: str):
        """（主要由 UI 的 Alert Dialog 確認按鈕觸發）執行刪除課程的確認後操作。

        此方法本身不直接執行刪除，而是被 UI 中的確認機制（例如 Alert Dialog）
        在使用者確認後間接調用 `handle_delete_course_confirmed`。
        此處保留此方法簽名是為了與先前可能的 UI 綁定兼容，但實際刪除邏輯
        在 `handle_delete_course_confirmed` 中。

        Args:
            course_id (str): 要刪除的課程 ID 字串。
        """
        # 實際的 UI 確認流程應在頁面元件中處理，
        # 例如，一個按鈕的 on_click 設定一個待刪除 ID，然後彈出 Alert Dialog，
        # Alert Dialog 的確認按鈕再呼叫 `handle_delete_course_confirmed`。
        # 此方法目前直接調用，假設 UI 已完成確認。
        return self.handle_delete_course_confirmed(course_id)


    # --- CSV 匯入 ---
    async def handle_csv_upload(self, files: List[rx.UploadFile]):
        """處理課程資料 CSV 檔案的上傳與匯入。

        Args:
            files (List[rx.UploadFile]): 由 `rx.upload` 元件提供的已上傳檔案列表。
                                         預期只處理列表中的第一個檔案。
        """
        self.csv_import_feedback = "正在處理檔案，請稍候..."
        if not files:
            self.csv_import_feedback = "錯誤：未選擇任何檔案。請選擇一個 CSV 檔案上傳。"
            return rx.toast.warning(self.csv_import_feedback) # type: ignore

        try:
            file_content_bytes = await files[0].read() # 讀取第一個上傳的檔案內容

            # 確定用於 CSV 匯入的預設學年度
            default_ay = self.filter_academic_year
            if not default_ay: # 若篩選器未選擇學年度
                current_setting = await AcademicYearSetting.get_current()
                if current_setting:
                    default_ay = current_setting.academic_year
                elif self.academic_year_options: # 若系統無當前設定，但選項列表存在
                     default_ay = self.academic_year_options[0]["value"] # 使用選項中的第一個
                else: # 若連學年度選項都沒有，則無法確定預設學年
                    self.csv_import_feedback = "錯誤：無法確定預設學年度。請先在系統中設定當前學年度，或在頁面上篩選一個學年度後再進行匯入。"
                    return rx.toast.error(self.csv_import_feedback) # type: ignore

            # 呼叫 CSV 工具函式進行匯入
            results = await csv_utils.import_courses_from_csv(file_content_bytes, default_ay)

            # 構建匯入結果的回饋訊息
            feedback_lines = []
            if results["success"]:
                feedback_lines.append(f"成功匯入 {len(results['success'])} 筆課程記錄。")
            if results["errors"]:
                feedback_lines.append(f"匯入失敗 {len(results['errors'])} 筆記錄。錯誤詳情（最多顯示10筆）:")
                feedback_lines.extend([f"- {err}" for err in results["errors"][:10]])
                if len(results["errors"]) > 10:
                    feedback_lines.append("...還有更多錯誤未在此處顯示，請檢查系統日誌。")

            self.csv_import_feedback = "\n".join(feedback_lines)

            # 根據匯入結果顯示 toast 訊息
            if not results["errors"] and results["success"]:
                 rx.toast.success("CSV 課程資料已全部成功匯入！") # type: ignore
            elif results["success"] and results["errors"]:
                 rx.toast.warning("CSV 課程資料部分匯入成功，部分記錄失敗。請查看匯入結果詳情。") # type: ignore
            elif not results["success"] and results["errors"]:
                 rx.toast.error("CSV 課程資料匯入失敗。請查看匯入結果詳情。") # type: ignore
            else: # results["success"] 和 results["errors"] 都為空 (例如空檔案)
                 rx.toast.info("CSV 檔案中沒有可匯入的課程資料。") # type: ignore


            await self.load_courses() # 重新載入課程列表以反映匯入結果
        except Exception as e:
            # 應記錄更詳細的錯誤日誌
            # await SystemLog.log(LogLevel.ERROR, f"CSV 課程匯入失敗: {e}", source="ManagerCoursesState")
            self.csv_import_feedback = f"CSV 檔案處理過程中發生未預期錯誤：{str(e)}"
            return rx.toast.error(self.csv_import_feedback) # type: ignore

    # --- 通用表單欄位更新輔助方法 ---
    def set_form_data_value(self, form_var_name: str, key: str, value: Any):
        """
        通用輔助方法，用於更新 `add_course_form_data` 或 `edit_course_form_data`
        狀態變數中指定鍵的值。

        此方法確保在更新字典型態的 `rx.Var` 時，是透過創建副本再賦值的方式，
        以正確觸發 Reflex 的反應式更新。

        Args:
            form_var_name (str): 要更新的表單資料狀態變數的名稱
                                 (例如："add_course_form_data" 或 "edit_course_form_data")。
            key (str): 表單資料字典中要更新的鍵。
            value (Any): 要設定的新值。
        """
        current_form_data_dict = getattr(self, form_var_name)
        # 為了觸發 Reflex Var 的更新，需要創建一個新的字典副本
        new_form_data_dict = current_form_data_dict.copy()
        new_form_data_dict[key] = value
        setattr(self, form_var_name, new_form_data_dict)
