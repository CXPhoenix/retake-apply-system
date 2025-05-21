import reflex as rx
from typing import List, Optional
from beanie.odm.fields import PydanticObjectId # type: ignore
from datetime import datetime

from .auth import AuthState
from ..models.course import Course
from ..models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus # 匯入 PaymentStatus
from ..models.users import User, UserGroup 
from ..models.academic_year_setting import AcademicYearSetting
from ..utils.funcs import check_course_conflict, format_datetime_to_taipei_str # 衝堂檢查函式 及 時間格式化

class CourseSelectionState(AuthState):
    """管理學生課程選擇頁面的狀態與邏輯"""

    available_courses: rx.Var[List[Course]] = rx.Var([])
    enrolled_course_ids_this_year: rx.Var[List[str]] = rx.Var([]) # 儲存已選課程的 ID
    search_term: rx.Var[str] = ""
    current_academic_year: rx.Var[str] = ""
    is_loading: rx.Var[bool] = False
    
    is_registration_open: rx.Var[bool] = False
    registration_time_message: rx.Var[str] = "" # 例如 "登記開放中" 或 "登記已結束"

    @rx.cached_var
    def has_student_role(self) -> bool:
        return UserGroup.STUDENT in self.current_user_groups

    async def _load_current_academic_year_and_settings(self):
        """載入當前學年度設定，並判斷登記是否開放。"""
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
            # rx.window_alert(self.registration_time_message) # type: ignore

    async def _load_user_enrollments_for_current_year(self):
        """載入當前使用者在本學年的有效選課記錄ID。"""
        if not self.token_is_valid or not self.current_user_google_id or not self.current_academic_year or self.current_academic_year == "未設定":
            self.enrolled_course_ids_this_year = []
            return

        current_user_db = await User.find_one(User.google_sub == self.current_user_google_id)
        if not current_user_db:
            self.enrolled_course_ids_this_year = []
            return
        
        valid_statuses = [EnrollmentStatus.SUCCESS, EnrollmentStatus.PENDING_CONFIRMATION]
        enrollments = await Enrollment.find(
            Enrollment.user_id.id == current_user_db.id, # type: ignore
            Enrollment.academic_year == self.current_academic_year,
            Enrollment.status.is_in(valid_statuses) # type: ignore
        ).project(Enrollment.course_id).to_list()
        
        self.enrolled_course_ids_this_year = [str(enroll.course_id.id) for enroll in enrollments if enroll.course_id] # type: ignore

    async def on_page_load(self):
        if not self.is_hydrated or not self.token_is_valid:
            return
        # 權限檢查由頁面裝飾器處理，此處可專注載入邏輯
        await self._load_current_academic_year_and_settings()
        if self.is_registration_open and self.current_academic_year != "未設定":
            await self.load_available_courses()
            await self._load_user_enrollments_for_current_year()
        else:
            self.available_courses = [] # 如果登記未開放或學年未設，則清空可選課程

    async def load_available_courses(self):
        if not self.is_registration_open or not self.current_academic_year or self.current_academic_year == "未設定":
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
        self.search_term = term
        await self.load_available_courses()

    async def handle_select_course(self, course_id_str: str):
        if not self.token_is_valid or not self.current_user_google_id:
            return rx.toast.error("請先登入後再進行選課。") # type: ignore
        
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
