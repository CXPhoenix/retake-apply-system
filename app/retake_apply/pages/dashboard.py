import reflex as rx
from reflex_google_auth import require_google_login

@require_google_login
def user_dashboard() -> rx.Component:
    from ..states.auth import AuthState # authorize_by_groups 移至 auth.py 內部使用
    from ..models.users import UserGroup, User
    from ..models.required_course import RequiredCourse
    from ..models.enrollment import Enrollment # 用於顯示已選課程
    from ..components import navbar # 假設 navbar 元件已存在
    
    # TODO: 建立一個 DashboardState，繼承 AuthState，用於管理儀表板相關的資料載入與邏輯。
    #       例如：載入學生應重補修列表、已選課程列表等。
    #       class DashboardState(AuthState):
    #           required_courses_list: list[RequiredCourse] = []
    #           enrolled_courses_list: list[Enrollment] = []
    #
    #           async def load_student_data(self):
    #               if UserGroup.STUDENT in self.current_user_groups:
    #                   user = await User.find_one(User.google_sub == self.current_user_google_id)
    #                   if user:
    #                       self.required_courses_list = await RequiredCourse.find(RequiredCourse.user_id == user.id).to_list()
    #                       self.enrolled_courses_list = await Enrollment.find(Enrollment.user_id == user.id, fetch_links=True).to_list() # fetch_links 以取得課程詳細資訊

    def student_dashboard() -> rx.Component:
        # TODO: 應重補修科目列表的查詢邏輯需要修正。
        #       目前的查詢 `RequiredCourse.find(RequiredCourse.user_id.id == User.id, User.google_sub == AuthState.current_user_google_id)`
        #       無法正確獲取當前登入學生的 User ID。
        #       應改為先從 AuthState 獲取 current_user_google_id，然後查詢 User 模型獲取 User 物件，再用其 ID 查詢 RequiredCourse。
        #       此邏輯最好封裝在 DashboardState 的事件處理器中。
        #       例如: rx.foreach(DashboardState.required_courses_list, ...)
        
        # TODO: 實現「檢視個人已登記課程清單」功能。
        #       規格文件 2. 學生 (Student) -> 檢視個人已登記課程清單。
        #       需要查詢 Enrollment 模型，並顯示相關課程資訊。
        #       例如: rx.foreach(DashboardState.enrolled_courses_list, ...)
        return rx.vstack(
            navbar(),
            rx.heading("學生儀表板", size="lg", margin_bottom="1em"),
            rx.text("（TODO：以下應重補修科目列表需從 DashboardState 載入）"),
            # 範例顯示，實際應從 State 綁定
            # rx.foreach(
            #     DashboardState.required_courses_list, 
            #     lambda req_course: rx.box(...)
            # ),
            rx.text("（TODO：以下已選課程列表需從 DashboardState 載入）"),
            # 範例顯示
            # rx.foreach(
            #     DashboardState.enrolled_courses_list,
            #     lambda enrollment: rx.box(
            #         rx.text(f"課程名稱：{enrollment.course_id.course_name}"), # 假設 course_id 已 fetch_link
            #         rx.text(f"狀態：{enrollment.status.value}")
            #     )
            # ),
            rx.link(rx.button("前往選課"), href="/course-selection"), # 規格文件中的 course_selection.py
            align_items="center",
            padding="2em",
        )
    
    def course_manager_dashboard() -> rx.Component:
        # TODO: 根據規格文件「課程管理者介面與功能」(3.) 實現儀表板。
        #       可能包含：
        #       - 快速存取「課程管理」、「學生名單管理」、「學年度管理」、「報名管理」的連結。
        #       - 顯示系統當前學年度。
        #       - (可選) 顯示待處理事項或統計資訊。
        return rx.vstack(
            navbar(),
            rx.heading("課程管理者儀表板", size="lg", margin_bottom="1em"),
            rx.text("歡迎，課程管理者。"),
            rx.text("TODO: 顯示課程管理、學生名單管理、學年度設定、報名管理等功能的連結。"),
            rx.link(rx.button("管理課程"), href="/manager-courses"), # 規格文件中的 manager_courses.py
            rx.link(rx.button("管理學生應重補修名單"), href="/manager-students"), # 規格文件中的 manager_students.py
            rx.link(rx.button("管理學年度"), href="/manager-academic-year"), # 規格文件中的 manager_academic_year.py
            rx.link(rx.button("管理報名資料"), href="/manager-enrollments"), # 規格文件中的 manager_enrollments.py
            align_items="center",
            padding="2em",
        )
    
    def system_admin_dashboard() -> rx.Component:
        # TODO: 根據規格文件「系統管理者介面與功能」(4.) 實現儀表板。
        #       可能包含：
        #       - 快速存取「使用者角色與權限指派」、「系統運作日誌查閱」的連結。
        return rx.vstack(
            navbar(),
            rx.heading("系統管理者儀表板", size="lg", margin_bottom="1em"),
            rx.text("歡迎，系統管理者。"),
            rx.text("TODO: 顯示使用者角色管理、系統日誌查閱等功能的連結。"),
            rx.link(rx.button("管理使用者角色"), href="/admin-users"), # 規格文件中的 admin_users.py
            rx.link(rx.button("查閱系統日誌"), href="/admin-logs"), # 規格文件中的 admin_logs.py
            align_items="center",
            padding="2em",
        )
    
    # TODO: AuthState.has_required_groups 是 async def，直接用於 rx.cond 可能無法如預期運作。
    #       rx.cond 期望同步的布林值或 rx.Var[bool]。
    #       應在 AuthState 中提供一個 @rx.var is_in_group(group: UserGroup) -> bool
    #       或 is_student: bool, is_course_manager: bool 等。
    #       或者，將此頁面的主要邏輯移至一個 DashboardState，並在 on_load 時判斷角色並設定一個 rx.Var 來控制顯示哪個儀表板。
    #       目前的 require_group 裝飾器 (在 auth.py) 也是基於此概念設計，但頁面本身也需要此邏輯。
    return rx.cond(
        AuthState.is_hydrated, # 確保 AuthState 已水合
        rx.cond(
            # 假設 AuthState.current_user_groups 已經被正確填充
            UserGroup.STUDENT in AuthState.current_user_groups, # 直接檢查群組列表
            student_dashboard(),
            rx.cond(
                UserGroup.COURSE_MANAGER in AuthState.current_user_groups,
                course_manager_dashboard(),
                rx.cond(
                    UserGroup.SYSTEM_ADMIN in AuthState.current_user_groups,
                    system_admin_dashboard(),
                    rx.vstack( # 若無任何指定角色但已登入
                        navbar(),
                        rx.heading("角色未分配", size="lg", color_scheme="orange"),
                        rx.text("您的帳號已登入，但尚未被指派任何特定角色。"),
                        rx.text("請聯繫系統管理者為您設定權限。"),
                        rx.text(f"您的群組: {AuthState.current_user_groups}"),
                        align_items="center",
                        padding="2em",
                    )
                )
            )
        ),
        rx.center(rx.spinner(size="3"), padding_y="5em") # 水合時顯示 spinner
    )
