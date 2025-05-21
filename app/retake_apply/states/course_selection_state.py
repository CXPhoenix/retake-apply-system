"""學生選課頁面的狀態管理模組。

此模組定義了 `CourseSelectionState` 類別，繼承自 `AuthState`，
負責處理學生選課頁面的所有後端邏輯，包括：
- 載入當前學年度及登記時間設定。
- 載入並篩選可選課程列表。
- 處理學生的選課操作，包括衝堂檢查。
- 管理使用者已選課程的狀態。
"""
import reflex as rx
from typing import List, Optional
from beanie.odm.fields import PydanticObjectId # type: ignore # 用於將字串 ID 轉換為 ObjectId
from datetime import datetime

from .auth import AuthState # 基礎身份驗證狀態
from ..models.course import Course # 課程資料模型
from ..models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus # 選課記錄模型及相關列舉
from ..models.users import User, UserGroup # 使用者模型及角色列舉
from ..models.academic_year_setting import AcademicYearSetting # 學年度設定模型
from ..utils.funcs import check_course_conflict, format_datetime_to_taipei_str # 衝堂檢查及時間格式化輔助函式

class CourseSelectionState(AuthState):
    """管理學生課程選擇頁面的狀態與相關邏輯。

    Attributes:
        available_courses (rx.Var[List[Course]]): 當前學年度可供選擇的課程列表。
        enrolled_course_ids_this_year (rx.Var[List[str]]): 當前使用者在本學年已成功選修
                                                          (或待確認) 的課程 ID 列表。
        search_term (rx.Var[str]): 用於搜尋課程的關鍵字。
        current_academic_year (rx.Var[str]): 當前系統運作的學年度字串 (例如 "113-1")。
        is_loading (rx.Var[bool]): 標記是否正在從後端載入課程資料。
        is_registration_open (rx.Var[bool]): 標記當前是否為選課登記開放時間。
        registration_time_message (rx.Var[str]): 顯示給使用者的關於登記時間的訊息。
    """

    available_courses: rx.Var[List[Course]] = rx.Var([])
    enrolled_course_ids_this_year: rx.Var[List[str]] = rx.Var([]) # 儲存已選課程的 ID (字串)
    search_term: rx.Var[str] = ""
    current_academic_year: rx.Var[str] = ""
    is_loading: rx.Var[bool] = False
    
    is_registration_open: rx.Var[bool] = False
    registration_time_message: rx.Var[str] = "" # 例如 "登記開放中 (開始時間 - 結束時間)"

    @rx.cached_var
    def has_student_role(self) -> bool:
        """檢查當前登入使用者是否具有學生 (`UserGroup.STUDENT`) 角色。

        Returns:
            bool: 若使用者具有學生角色則回傳 `True`，否則回傳 `False`。
        """
        return UserGroup.STUDENT in self.current_user_groups

    async def _load_current_academic_year_and_settings(self):
        """內部輔助函式，用於載入當前生效的學年度設定，
        並根據設定中的登記起迄時間來更新 `is_registration_open`
        和 `registration_time_message` 狀態。
        """
        setting = await AcademicYearSetting.get_current()
        if setting:
            self.current_academic_year = setting.academic_year
            now = datetime.utcnow()
            
            start_time = setting.registration_start_time
            end_time = setting.registration_end_time

            if start_time and end_time:
                if start_time <= now <= end_time:
                    self.is_registration_open = True
                    self.registration_time_message = f"登記開放中 ({format_datetime_to_taipei_str(start_time, '%Y/%m/%d %H:%M')} - {format_datetime_to_taipei_str(end_time, '%Y/%m/%d %H:%M')})"
                elif now < start_time:
                    self.is_registration_open = False
                    self.registration_time_message = f"登記尚未開始 (開始時間: {format_datetime_to_taipei_str(start_time, '%Y/%m/%d %H:%M')})"
                else: # now > end_time
                    self.is_registration_open = False
                    self.registration_time_message = f"登記已截止 (截止時間: {format_datetime_to_taipei_str(end_time, '%Y/%m/%d %H:%M')})"
            elif start_time and not end_time: # 只有開始時間
                 if start_time <= now:
                    self.is_registration_open = True
                    self.registration_time_message = f"登記開放中 (自 {format_datetime_to_taipei_str(start_time, '%Y/%m/%d %H:%M')} 起)"
                 else:
                    self.is_registration_open = False
                    self.registration_time_message = f"登記尚未開始 (開始時間: {format_datetime_to_taipei_str(start_time, '%Y/%m/%d %H:%M')})"
            elif not start_time and end_time: # 只有結束時間 (較少見，但處理一下)
                if now <= end_time:
                    self.is_registration_open = True # 假設無開始時間即代表已開始
                    self.registration_time_message = f"登記開放中 (截止時間: {format_datetime_to_taipei_str(end_time, '%Y/%m/%d %H:%M')})"
                else:
                    self.is_registration_open = False
                    self.registration_time_message = f"登記已截止 (截止時間: {format_datetime_to_taipei_str(end_time, '%Y/%m/%d %H:%M')})"
            else: # 都沒有設定
                self.is_registration_open = True # 預設為開放，除非有明確設定
                self.registration_time_message = "登記時間未設定 (預設開放)"
        else:
            self.current_academic_year = "未設定"
            self.is_registration_open = False
            self.registration_time_message = "系統尚未設定當前學年度，請聯繫課程管理者。"
            # rx.window_alert(self.registration_time_message) # type: ignore # 除錯用

    async def _load_user_enrollments_for_current_year(self):
        """內部輔助函式，載入當前使用者在本學年度所有有效（非取消狀態）的選課記錄ID。

        結果會更新 `self.enrolled_course_ids_this_year` 狀態變數。
        """
        if not self.token_is_valid or not self.current_user_google_id or \
           not self.current_academic_year or self.current_academic_year == "未設定":
            self.enrolled_course_ids_this_year = []
            return

        current_user_db = await User.find_one(User.google_sub == self.current_user_google_id)
        if not current_user_db:
            self.enrolled_course_ids_this_year = []
            return
        
        # 定義有效的選課狀態，用於判斷是否為已選修課程
        valid_enrollment_statuses = [EnrollmentStatus.SUCCESS, EnrollmentStatus.PENDING_CONFIRMATION]
        
        enrollments = await Enrollment.find(
            Enrollment.user_id.id == current_user_db.id, # type: ignore[attr-defined] # Beanie Link ID
            Enrollment.academic_year == self.current_academic_year,
            Enrollment.status.is_in(valid_enrollment_statuses) # type: ignore # Beanie is_in operator
        ).project(Enrollment.course_id).to_list() # 僅投影 course_id 以提高效率
        
        # 將獲取的課程 ID 轉換為字串列表
        self.enrolled_course_ids_this_year = [
            str(enroll.course_id.id) for enroll in enrollments if enroll.course_id # type: ignore[attr-defined]
        ]

    async def on_page_load(self):
        """選課頁面載入時執行的非同步操作。

        此方法會：
        1. 檢查使用者登入狀態和客戶端水合狀態。
        2. 載入當前學年度設定及登記時間狀態。
        3. 若登記開放且學年度已設定，則載入可選課程列表和使用者已選課程ID。
        4. 若登記未開放或學年度未設定，則清空可選課程列表。
        """
        if not self.is_hydrated or not self.token_is_valid:
            return # 等待客戶端水合或 token 驗證完成
        
        # 權限檢查已由頁面級別的 @require_group 裝飾器處理，
        # 此處專注於頁面資料的載入邏輯。
        await self._load_current_academic_year_and_settings()
        
        if self.is_registration_open and self.current_academic_year != "未設定":
            await self.load_available_courses() # 載入可選課程
            await self._load_user_enrollments_for_current_year() # 載入使用者已選課程
        else:
            # 若登記未開放或學年度未設定，則清空可選課程列表
            self.available_courses = [] 

    async def load_available_courses(self):
        """根據當前學年度、登記開放狀態及搜尋條件，從資料庫載入可選課程列表。

        查詢結果會更新 `self.available_courses` 狀態變數。
        若登記未開放或學年度未設定，則直接清空列表。
        """
        if not self.is_registration_open or \
           not self.current_academic_year or \
           self.current_academic_year == "未設定":
            self.available_courses = []
            return

        self.is_loading = True
        query_conditions = {
            "academic_year": self.current_academic_year,
            "is_open_for_registration": True,
        }
        if self.search_term:
            search_regex = {"$regex": self.search_term, "$options": "i"}
            query_conditions["$or"] = [
                 {"course_name": search_regex},
                 {"course_code": search_regex},
                 {"instructor_name": search_regex}
            ]
        
        self.available_courses = await Course.find(query_conditions).sort("course_code").to_list()
        self.is_loading = False

    async def handle_search_term_change(self, term: str):
        """處理課程搜尋關鍵字變更的事件。

        更新 `search_term` 狀態變數，並觸發重新載入可選課程列表。

        Args:
            term (str): 新的搜尋關鍵字。
        """
        self.search_term = term
        await self.load_available_courses()

    async def handle_select_course(self, course_id_str: str):
        """處理學生點擊「我要選課」按鈕的事件。

        此方法會執行一系列檢查：
        1. 使用者是否登入且為學生角色。
        2. 當前是否為登記開放時間。
        3. 所選課程是否存在且開放選修。
        4. 是否與已選課程發生衝堂 (時間重疊或同課程不同時段)。
        5. 是否已重複選修此課程。
        若所有檢查通過，則創建新的 `Enrollment` 記錄並儲存至資料庫，
        然後更新使用者已選課程列表並顯示成功訊息。若任一檢查失敗，則顯示錯誤訊息。

        Args:
            course_id_str (str): 被選課程的 ID 字串。
        """
        if not self.token_is_valid or not self.current_user_google_id:
            return rx.toast.error("請先登入後再進行選課。") # type: ignore
        
        if not self.has_student_role: # 確保是學生角色
             return rx.toast.error("只有學生才能進行選課。") # type: ignore

        if not self.is_registration_open:
            return rx.toast.error(self.registration_time_message or "目前非選課登記時間。") # type: ignore

        current_user_db = await User.find_one(User.google_sub == self.current_user_google_id)
        if not current_user_db:
            return rx.toast.error("無法找到您的使用者資訊，請重新登入。") # type: ignore

        try:
            obj_course_id = PydanticObjectId(course_id_str)
        except Exception:
            return rx.toast.error("無效的課程 ID。") # type: ignore

        selected_course = await Course.get(obj_course_id)
        if not selected_course:
            return rx.toast.error("無法找到所選課程，請重試。") # type: ignore

        if not selected_course.is_open_for_registration or selected_course.academic_year != self.current_academic_year:
            return rx.toast.error("此課程目前無法選修或不屬於當前學期。") # type: ignore

        # 獲取學生已選課程 (用於衝堂檢查)
        valid_statuses = [EnrollmentStatus.SUCCESS, EnrollmentStatus.PENDING_CONFIRMATION]
        existing_enrollments = await Enrollment.find(
            Enrollment.user_id.id == current_user_db.id, # type: ignore
            Enrollment.academic_year == self.current_academic_year,
            Enrollment.status.is_in(valid_statuses) # type: ignore
        ).fetch_links(Enrollment.course_id).to_list() # fetch_links 以便能訪問 course_id.time_slots

        enrolled_courses_details = []
        for enroll in existing_enrollments:
            if enroll.course_id: # enroll.course_id is a Link[Course]
                 # Beanie 0.24+ Link.fetch() is implicit if fetch_links=True on find
                 # but to be safe, or if it's not fetched, we can fetch it.
                 # However, if fetch_links=True was used, enroll.course_id should be the Course object.
                 # Let's assume it's already a Course object due to fetch_links.
                if isinstance(enroll.course_id, Course): # Check if it's already fetched
                    enrolled_courses_details.append(enroll.course_id)
                else: # If not, fetch it (this path might not be needed with Beanie's fetch_links)
                    course_doc = await enroll.course_id.fetch() # type: ignore
                    if course_doc:
                        enrolled_courses_details.append(course_doc)
        
        conflict_reason = check_course_conflict(selected_course, enrolled_courses_details, self.current_academic_year)
        if conflict_reason:
            return rx.toast.error(f"選課失敗：{conflict_reason}") # type: ignore
        
        # 檢查是否已重複選課 (Enrollment 模型應有唯一索引 (user_id, course_id, academic_year))
        # 但為防萬一，多一層檢查
        already_enrolled_this_exact_course = await Enrollment.find_one(
            Enrollment.user_id.id == current_user_db.id, # type: ignore
            Enrollment.course_id.id == selected_course.id, # type: ignore
            Enrollment.academic_year == self.current_academic_year
        )
        if already_enrolled_this_exact_course and already_enrolled_this_exact_course.is_active_enrollment:
             return rx.toast.info("您已報名此課程。") # type: ignore


        new_enrollment = Enrollment(
            user_id=current_user_db.id, # type: ignore
            course_id=selected_course.id, # type: ignore
            academic_year=self.current_academic_year,
            status=EnrollmentStatus.SUCCESS, # 預設成功，或可改為 PENDING_CONFIRMATION
            payment_status=PaymentStatus.AWAITING_PAYMENT # 預設待繳費
        )
        await new_enrollment.insert()
        
        await self._load_user_enrollments_for_current_year() # 更新已選課程 ID 列表
        # 可以考慮是否需要重新載入 available_courses (例如人數上限變化)
        # await self.load_available_courses() 
        return rx.toast.success(f"課程 '{selected_course.course_name}' 選課成功！") # type: ignore
