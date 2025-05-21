"""儀表板頁面的狀態管理模組。

此模듈定義了 `DashboardState` 類別，繼承自 `AuthState`，
負責處理應用程式儀表板頁面的所有後端邏輯。
主要功能是根據登入使用者的角色，載入並準備對應儀表板所需的資料。
"""
import reflex as rx
from typing import List, Optional

from .auth import AuthState # 基礎身份驗證狀態
from ..models.users import User, UserGroup # 使用者模型及角色列舉
from ..models.required_course import RequiredCourse # 應重補修科目模型
from ..models.enrollment import Enrollment, EnrollmentStatus # 選課記錄模型及狀態列舉
from ..models.academic_year_setting import AcademicYearSetting # 學年度設定模型

class DashboardState(AuthState):
    """管理儀表板頁面的狀態與相關邏輯。

    根據登入使用者的角色，動態載入並顯示不同的儀表板資訊。

    Attributes:
        my_required_courses (rx.Var[List[RequiredCourse]]): 若使用者為學生，
            儲存其未完成的應重補修科目列表。
        my_enrollments (rx.Var[List[Enrollment]]): 若使用者為學生，
            儲存其在本學期已登記的課程列表。
        current_academic_year_display (rx.Var[str]): 顯示在儀表板上的當前學年度字串。
        is_loading_dashboard_data (rx.Var[bool]): 標記是否正在從後端載入儀表板資料。
    """

    # --- 學生儀表板相關狀態 ---
    my_required_courses: rx.Var[List[RequiredCourse]] = rx.Var([])
    my_enrollments: rx.Var[List[Enrollment]] = rx.Var([])
    
    # --- 通用顯示狀態 ---
    current_academic_year_display: rx.Var[str] = "未設定"
    is_loading_dashboard_data: rx.Var[bool] = False # 用於控制載入指示器的顯示

    async def _load_student_dashboard_data(self):
        """內部輔助函式，專門載入學生角色儀表板所需的資料。

        包括學生未完成的應重補修科目列表，以及在本學期已登記的課程列表。
        若使用者未登入、無 Google ID，或當前學年度未設定，則清空相關列表。
        """
        if not self.token_is_valid or not self.current_user_google_id or \
           self.current_academic_year_display == "未設定":
            self.my_required_courses = []
            self.my_enrollments = []
            return

        current_user_db = await User.find_one(User.google_sub == self.current_user_google_id)
        if not current_user_db:
            self.my_required_courses = []
            self.my_enrollments = []
            return

        # 載入學生未完成的應重補修科目
        self.my_required_courses = await RequiredCourse.find(
            RequiredCourse.user_id.id == current_user_db.id, # type: ignore[attr-defined]
            RequiredCourse.is_remedied == False
            # fetch_links=True # RequiredCourse 目前沒有 Link[User]，但若未來加入可啟用
        ).sort("-uploaded_at").to_list()

        # 載入學生在本學期已登記且狀態有效的課程
        valid_enrollment_statuses = [
            EnrollmentStatus.SUCCESS, 
            EnrollmentStatus.PENDING_CONFIRMATION
            # 可根據需求加入其他視為「有效」的選課狀態
        ]
        self.my_enrollments = await Enrollment.find(
            Enrollment.user_id.id == current_user_db.id, # type: ignore[attr-defined]
            Enrollment.academic_year == self.current_academic_year_display,
            Enrollment.status.is_in(valid_enrollment_statuses) # type: ignore # Beanie is_in operator
        ).fetch_links(True).sort("-enrolled_at").to_list() # fetch_links=True 會載入關聯的 User 和 Course


    async def _load_dashboard_data(self):
        """內部輔助函式，根據登入使用者的角色載入對應的儀表板資料。

        首先會載入當前學年度設定，然後根據使用者是否為學生角色，
        決定是否呼叫 `_load_student_dashboard_data`。
        """
        self.is_loading_dashboard_data = True
        
        # 步驟 1: 載入當前學年度設定
        current_academic_setting = await AcademicYearSetting.get_current()
        if current_academic_setting:
            self.current_academic_year_display = current_academic_setting.academic_year
        else:
            self.current_academic_year_display = "未設定" # 若系統無有效學年度設定

        # 步驟 2: 根據使用者角色載入特定資料
        if UserGroup.STUDENT in self.current_user_groups:
            await self._load_student_dashboard_data()
        
        # 備註：課程管理者和系統管理者的儀表板目前主要顯示靜態連結，
        # 若未來這些角色儀表板需要顯示動態資料 (例如統計數據)，
        # 則應在此處加入相應的資料載入邏輯。

        self.is_loading_dashboard_data = False

    async def on_page_load(self):
        """儀表板頁面載入時執行的非同步操作。

        此方法會檢查使用者登入狀態和客戶端水合狀態，
        然後呼叫 `_load_dashboard_data` 以載入儀表板所需的資料。
        頁面級別的權限檢查已由 `@require_google_login` 裝飾器處理。
        """
        if not self.is_hydrated or not self.token_is_valid:
            return # 等待客戶端水合或 token 驗證完成
        
        # 頁面級別的權限（例如是否登入）已由 @require_google_login 處理。
        # 此處專注於載入儀表板內容所需的資料。
        await self._load_dashboard_data()
