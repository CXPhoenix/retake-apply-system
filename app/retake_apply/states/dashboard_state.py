import reflex as rx
from typing import List, Optional

from .auth import AuthState
from ..models.users import User, UserGroup
from ..models.required_course import RequiredCourse
from ..models.enrollment import Enrollment, EnrollmentStatus
from ..models.academic_year_setting import AcademicYearSetting

class DashboardState(AuthState):
    """管理儀表板頁面的狀態與邏輯"""

    # 學生相關資料
    my_required_courses: rx.Var[List[RequiredCourse]] = rx.Var([])
    my_enrollments: rx.Var[List[Enrollment]] = rx.Var([])
    
    # 通用顯示
    current_academic_year_display: rx.Var[str] = "未設定"
    is_loading_dashboard_data: rx.Var[bool] = False

    async def _load_student_dashboard_data(self):
        """載入學生儀表板所需的資料"""
        if not self.token_is_valid or not self.current_user_google_id or self.current_academic_year_display == "未設定":
            self.my_required_courses = []
            self.my_enrollments = []
            return

        current_user_db = await User.find_one(User.google_sub == self.current_user_google_id)
        if not current_user_db:
            self.my_required_courses = []
            self.my_enrollments = []
            return

        # 載入應重補修科目 (僅未完成的)
        self.my_required_courses = await RequiredCourse.find(
            RequiredCourse.user_id.id == current_user_db.id, # type: ignore
            RequiredCourse.is_remedied == False,
            fetch_links=True # 雖然 RequiredCourse 目前沒有 Link User，但以防萬一
        ).sort("-uploaded_at").to_list()

        # 載入本學期已選課程
        valid_statuses = [
            EnrollmentStatus.SUCCESS, 
            EnrollmentStatus.PENDING_CONFIRMATION
        ]
        self.my_enrollments = await Enrollment.find(
            Enrollment.user_id.id == current_user_db.id, # type: ignore
            Enrollment.academic_year == self.current_academic_year_display,
            Enrollment.status.is_in(valid_statuses) # type: ignore
        ).fetch_links(True).sort("-enrolled_at").to_list() # fetch_links User and Course


    async def _load_dashboard_data(self):
        """根據使用者角色載入對應的儀表板資料"""
        self.is_loading_dashboard_data = True
        
        # 載入當前學年度
        current_setting = await AcademicYearSetting.get_current()
        if current_setting:
            self.current_academic_year_display = current_setting.academic_year
        else:
            self.current_academic_year_display = "未設定"

        # 根據角色載入特定資料
        if UserGroup.STUDENT in self.current_user_groups:
            await self._load_student_dashboard_data()
        
        # 課程管理者和系統管理者的儀表板目前主要是連結，不太需要載入特定資料到此 State
        # 如果未來需要，可以在此處添加邏輯

        self.is_loading_dashboard_data = False

    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            return 
        # 權限檢查由頁面裝飾器處理，此處專注資料載入
        await self._load_dashboard_data()
