import reflex as rx
from typing import List, Optional, Dict, Any
from beanie.odm.fields import PydanticObjectId # type: ignore
from datetime import datetime

from .auth import AuthState
from ..models.users import User, UserGroup
from ..models.course import Course
from ..models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus
from ..models.academic_year_setting import AcademicYearSetting
from ..utils import csv_utils # 匯入 CSV 工具模組
from ..utils.funcs import check_course_conflict # 衝堂檢查

class ManagerEnrollmentsState(AuthState):
    """管理課程管理者操作報名資料的狀態與邏輯"""

    enrollments_list: List[Enrollment] = []
    search_term: str = ""
    selected_academic_year: str = "" # 預設為空，由 on_page_load 設定
    academic_year_options: List[Dict[str, str]] = []

    # 現場報名 Modal 控制
    show_manual_enroll_modal: bool = False
    manual_enroll_form_data: Dict[str, Any] = {
        "student_identifier": "", # 學號或 Email
        "selected_course_id_to_enroll": None, # 儲存選擇的課程 ID
    }
    manual_enroll_course_search_results: List[Course] = []
    manual_enroll_course_search_term: str = ""
    
    # 用於在 Modal 中顯示選中的課程名稱
    manual_enroll_selected_course_name: str = ""


    async def _load_academic_year_options(self):
        """載入學年度選項供篩選，並設定預設篩選學年度"""
        settings = await AcademicYearSetting.find_all(sort=[("academic_year", -1)]).to_list()
        unique_years = sorted(list(set(s.academic_year for s in settings)), reverse=True)
        
        options = [{"label": "全部學年度", "value": "ALL"}]
        options.extend([{"label": year, "value": year} for year in unique_years])
        self.academic_year_options = options
        
        if not self.selected_academic_year: # 如果尚未設定
            current_setting = await AcademicYearSetting.get_current()
            if current_setting and current_setting.academic_year in unique_years:
                self.selected_academic_year = current_setting.academic_year
            elif unique_years: # 如果系統當前學年不在選項中，選最新的
                self.selected_academic_year = unique_years[0]
            else: # 都沒有，則選 "ALL"
                self.selected_academic_year = "ALL"


    async def on_page_load(self):
        if not self.is_hydrated or not self.token_is_valid:
            return
        if not self.is_member_of_any([UserGroup.COURSE_MANAGER, UserGroup.ADMIN]):
            return rx.redirect(self.DEFAULT_UNAUTHORIZED_REDIRECT_PATH) # type: ignore
        
        await self._load_academic_year_options()
        await self.load_enrollments_data()

    async def load_enrollments_data(self):
        """載入或篩選報名資料列表"""
        query_conditions: Dict[str, Any] = {}
        if self.selected_academic_year != "ALL":
            query_conditions["academic_year"] = self.selected_academic_year
        
        if self.search_term:
            search_regex = {"$regex": self.search_term, "$options": "i"}
            # 搜尋 User 的 email, student_id, fullname
            user_matches_query = {"$or": [
                {"email": search_regex},
                {"student_id": search_regex},
                {"fullname": search_regex}
            ]}
            matching_users = await User.find(user_matches_query).project(User.id).to_list()
            matching_user_ids = [user.id for user in matching_users]

            # 搜尋 Course 的 course_name, course_code
            course_matches_query = {"$or": [
                {"course_name": search_regex},
                {"course_code": search_regex}
            ]}
            matching_courses = await Course.find(course_matches_query).project(Course.id).to_list()
            matching_course_ids = [course.id for course in matching_courses]

            search_or_conditions = []
            if matching_user_ids:
                search_or_conditions.append({"user_id": {"$in": matching_user_ids}})
            if matching_course_ids:
                search_or_conditions.append({"course_id": {"$in": matching_course_ids}})
            
            if search_or_conditions:
                if "$or" in query_conditions: # 如果已有 $or (不太可能在此情況發生)
                    query_conditions["$and"] = [{"$or": query_conditions["$or"]}, {"$or": search_or_conditions}]
                    del query_conditions["$or"]
                else:
                    query_conditions["$or"] = search_or_conditions
            else: # 如果 search_term 沒匹配到任何 user 或 course，則結果應為空
                self.enrollments_list = []
                return

        self.enrollments_list = await Enrollment.find(
            query_conditions, 
            fetch_links=True # Fetch User and Course objects
        ).sort("-enrolled_at").to_list()

    async def handle_search_term_change(self, term: str):
        self.search_term = term
        await self.load_enrollments_data() 

    async def handle_academic_year_change(self, year: str):
        self.selected_academic_year = year
        await self.load_enrollments_data()

    async def handle_csv_export(self):
        """處理下載報名資料 CSV"""
        if not self.enrollments_list:
            return rx.toast.info("目前沒有可匯出的報名資料。") # type: ignore
        
        try:
            # 確保 enrollments_list 中的 user_id 和 course_id 都已 fetch
            # load_enrollments_data 中已設定 fetch_links=True
            csv_data_string = await csv_utils.export_enrollments_to_csv(self.enrollments_list)
            return rx.download(data=csv_data_string.encode("utf-8-sig"), filename="學生報名資料.csv")
        except Exception as e:
            return rx.toast.error(f"匯出 CSV 失敗: {str(e)}") # type: ignore

    # --- 現場報名 Modal ---
    def open_manual_enroll_modal(self):
        self.manual_enroll_form_data = {"student_identifier": "", "selected_course_id_to_enroll": None}
        self.manual_enroll_course_search_results = []
        self.manual_enroll_course_search_term = ""
        self.manual_enroll_selected_course_name = ""
        self.show_manual_enroll_modal = True

    def close_manual_enroll_modal(self):
        self.show_manual_enroll_modal = False
        
    async def search_courses_for_manual_enroll(self, term: str):
        self.manual_enroll_course_search_term = term
        self.manual_enroll_selected_course_name = "" # 清除已選課程顯示
        self.manual_enroll_form_data["selected_course_id_to_enroll"] = None

        if not term or len(term) < 1: # 調整為至少1個字
            self.manual_enroll_course_search_results = []
            return

        current_ay_setting = await AcademicYearSetting.get_current()
        if not current_ay_setting:
            self.manual_enroll_course_search_results = []
            return rx.toast.error("系統尚未設定當前學年度，無法搜尋課程。") # type: ignore
        
        current_sys_ay = current_ay_setting.academic_year
        
        search_regex = {"$regex": term, "$options": "i"}
        self.manual_enroll_course_search_results = await Course.find(
            Course.academic_year == current_sys_ay,
            Course.is_open_for_registration == True,
            {"$or": [{"course_name": search_regex}, {"course_code": search_regex}]}
        ).limit(10).to_list()

    def select_course_for_manual_enroll(self, course: Course): # 改為接收 Course 物件
        self.manual_enroll_form_data["selected_course_id_to_enroll"] = str(course.id)
        self.manual_enroll_selected_course_name = f"{course.course_name} ({course.course_code})"
        self.manual_enroll_course_search_results = [] # 清空搜尋結果
        self.manual_enroll_course_search_term = self.manual_enroll_selected_course_name # 在輸入框顯示已選

    async def handle_manual_enroll_submit(self):
        student_identifier = self.manual_enroll_form_data.get("student_identifier","").strip()
        selected_course_id = self.manual_enroll_form_data.get("selected_course_id_to_enroll")

        if not student_identifier or not selected_course_id:
            return rx.toast.error("學生識別碼和選修課程皆須填寫。") # type: ignore
        
        try:
            found_user = await User.find_one(User.student_id == student_identifier)
            if not found_user:
                found_user = await User.find_one(User.email == student_identifier)
            if not found_user:
                return rx.toast.error(f"找不到學生：{student_identifier}") # type: ignore

            selected_course = await Course.get(PydanticObjectId(selected_course_id))
            if not selected_course:
                return rx.toast.error("找不到所選課程。") # type: ignore

            current_ay_setting = await AcademicYearSetting.get_current()
            if not current_ay_setting or selected_course.academic_year != current_ay_setting.academic_year:
                return rx.toast.error("所選課程不屬於當前系統運作的學年度。") # type: ignore
            
            # 衝堂檢查
            enrolled_courses_for_student = await Enrollment.find(
                Enrollment.user_id.id == found_user.id, # type: ignore
                Enrollment.academic_year == current_ay_setting.academic_year,
                Enrollment.status.is_in([EnrollmentStatus.SUCCESS, EnrollmentStatus.PENDING_CONFIRMATION]) # type: ignore
            ).fetch_links().to_list() # fetch_links 以便 check_course_conflict 能訪問 course_id.time_slots

            # 將 Enrollment 列表中的 course_id (Link[Course]) 轉換為 Course 物件列表
            enrolled_actual_courses = []
            for enroll in enrolled_courses_for_student:
                if enroll.course_id: # course_id is a Link
                    course_obj = await enroll.course_id.fetch() # Fetch the actual Course document
                    if course_obj:
                        enrolled_actual_courses.append(course_obj)
            
            conflict_reason = check_course_conflict(selected_course, enrolled_actual_courses, current_ay_setting.academic_year)
            if conflict_reason:
                return rx.toast.error(f"選課失敗：{conflict_reason}") # type: ignore

            # 檢查是否已選過此課程
            existing_enrollment = await Enrollment.find_one(
                Enrollment.user_id.id == found_user.id, # type: ignore
                Enrollment.course_id.id == selected_course.id, # type: ignore
                Enrollment.academic_year == current_ay_setting.academic_year
            )
            if existing_enrollment and existing_enrollment.is_active_enrollment: # is_active_enrollment 是自定義屬性
                 return rx.toast.error(f"學生已報名過此課程 '{selected_course.course_name}'。") # type: ignore


            new_enrollment = Enrollment(
                user_id=found_user.id, # type: ignore
                course_id=selected_course.id, # type: ignore
                academic_year=current_ay_setting.academic_year,
                status=EnrollmentStatus.SUCCESS, # 現場報名預設成功
                # payment_status 預設為 AWAITING_PAYMENT (除非課程免費，此處未處理免費邏輯)
            )
            await new_enrollment.insert()
            
            # (可選) 處理繳費單 TODO: 根據規格 5.1，初期僅規劃模型，此處不產生實際繳費單。

            self.close_manual_enroll_modal()
            await self.load_enrollments_data()
            return rx.toast.success(f"學生 {found_user.fullname or found_user.email} 報名課程 '{selected_course.course_name}' 成功！") # type: ignore
        except Exception as e:
            return rx.toast.error(f"現場報名失敗：{str(e)}") # type: ignore
            
    # Helper to set form data reactively
    def set_manual_enroll_form_field_value(self, key: str, value: Any):
        current_data = self.manual_enroll_form_data.copy()
        current_data[key] = value
        self.manual_enroll_form_data = current_data
