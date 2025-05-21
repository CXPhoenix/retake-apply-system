import reflex as rx
from reflex_google_auth import require_google_login

from ..states.dashboard_state import DashboardState # 匯入新的 DashboardState
from ..models.users import UserGroup # 用於角色判斷
from ..components import navbar 
from ..utils.funcs import format_datetime_to_taipei_str # 匯入時間格式化函式

# --- 學生儀表板元件 ---
def student_dashboard_content() -> rx.Component:
    return rx.vstack(
        rx.heading("學生儀表板", size="7", margin_bottom="1em"),
        rx.text(f"目前學年度: {DashboardState.current_academic_year_display}", color_scheme="gray", margin_bottom="1em"), # type: ignore

        rx.heading("我的應重補修科目 (未完成)", size="5", margin_top="1em", margin_bottom="0.5em"),
        rx.cond(
            DashboardState.my_required_courses.length() > 0, # type: ignore
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("科目代碼"),
                        rx.table.column_header_cell("科目名稱"),
                        rx.table.column_header_cell("原始修課學年"),
                        rx.table.column_header_cell("原始成績"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        DashboardState.my_required_courses,
                        lambda req: rx.table.row(
                            rx.table.cell(req.course_code),
                            rx.table.cell(req.course_name),
                            rx.table.cell(req.academic_year_taken),
                            rx.table.cell(req.original_grade),
                        )
                    )
                ),
                variant="surface", width="100%"
            ),
            rx.text("目前沒有需要重補修的科目記錄。", color_scheme="gray")
        ),

        rx.heading("我已登記的課程 (本學期)", size="5", margin_top="1.5em", margin_bottom="0.5em"),
        rx.cond(
            DashboardState.my_enrollments.length() > 0, # type: ignore
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("科目代碼"),
                        rx.table.column_header_cell("科目名稱"),
                        rx.table.column_header_cell("選課狀態"),
                        rx.table.column_header_cell("繳費狀態"),
                        rx.table.column_header_cell("報名時間"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        DashboardState.my_enrollments,
                        lambda enroll: rx.table.row(
                            rx.table.cell(enroll.course_id.course_code if enroll.course_id else "N/A"), # type: ignore
                            rx.table.cell(enroll.course_id.course_name if enroll.course_id else "N/A"), # type: ignore
                            rx.table.cell(rx.badge(enroll.status.value if enroll.status else "N/A")),
                            rx.table.cell(rx.badge(enroll.payment_status.value if enroll.payment_status else "N/A")),
                            rx.table.cell(format_datetime_to_taipei_str(enroll.enrolled_at, "%Y-%m-%d %H:%M") if enroll.enrolled_at else "N/A"), # 使用輔助函式
                        )
                    )
                ),
                variant="surface", width="100%"
            ),
            rx.text("您在本學期尚未登記任何課程。", color_scheme="gray")
        ),
        rx.link(rx.button("前往選課", margin_top="2em", size="3"), href="/course-selection"),
        align_items="stretch", # 使表格等元件寬度一致
        width="100%",
        spacing="4"
    )

# --- 課程管理者儀表板元件 ---
def course_manager_dashboard_content() -> rx.Component:
    return rx.vstack(
        rx.heading("課程管理者儀表板", size="7", margin_bottom="1em"),
        rx.text(f"歡迎，{DashboardState.tokeninfo.get('name', '課程管理者')}!", margin_bottom="1em"), # type: ignore
        rx.text(f"目前系統運作學年度: {DashboardState.current_academic_year_display}", weight="bold", margin_bottom="1.5em"), # type: ignore
        rx.grid(
            rx.link(rx.card(rx.text("管理課程資料", weight="medium")), href="/manager/courses", width="100%"),
            rx.link(rx.card(rx.text("管理學生應重補修名單", weight="medium")), href="/manager/students", width="100%"),
            rx.link(rx.card(rx.text("設定學年度與登記時間", weight="medium")), href="/manager/academic-year", width="100%"),
            rx.link(rx.card(rx.text("管理學生報名資料", weight="medium")), href="/manager/enrollments", width="100%"),
            columns="2", spacing="3", width="100%", max_width="800px"
        ),
        align_items="center",
        width="100%",
        spacing="4"
    )

# --- 系統管理者儀表板元件 ---
def system_admin_dashboard_content() -> rx.Component:
    return rx.vstack(
        rx.heading("系統管理者儀表板", size="7", margin_bottom="1em"),
        rx.text(f"歡迎，{DashboardState.tokeninfo.get('name', '系統管理者')}!", margin_bottom="1.5em"), # type: ignore
         rx.grid(
            rx.link(rx.card(rx.text("管理使用者角色", weight="medium")), href="/admin/users", width="100%"),
            rx.link(rx.card(rx.text("查閱系統日誌", weight="medium")), href="/admin/logs", width="100%"),
            # 系統管理者也可以存取課程管理者的學年度設定功能
            rx.link(rx.card(rx.text("設定學年度與登記時間", weight="medium")), href="/manager/academic-year", width="100%"),
            columns="2", spacing="3", width="100%", max_width="800px"
        ),
        align_items="center",
        width="100%",
        spacing="4"
    )

# --- 主儀表板頁面 ---
@rx.page(
    route="/dashboard", 
    title="儀表板",
    on_load=DashboardState.on_page_load # 綁定到新的 DashboardState
)
@require_google_login # 所有儀表板都需要登入
def dashboard_page() -> rx.Component:
    """根據使用者角色顯示不同的儀表板。"""
    return rx.vstack(
        navbar(),
        rx.box(
            rx.cond(
                DashboardState.is_loading_dashboard_data, # type: ignore
                rx.center(rx.spinner(size="3"), padding_y="5em"),
                rx.cond(
                    DashboardState.is_member_of_any([UserGroup.ADMIN]), # type: ignore
                    system_admin_dashboard_content(),
                    rx.cond(
                        DashboardState.is_member_of_any([UserGroup.COURSE_MANAGER]), # type: ignore
                        course_manager_dashboard_content(),
                        rx.cond(
                            DashboardState.is_member_of_any([UserGroup.STUDENT]), # type: ignore
                            student_dashboard_content(),
                            # 若已登入但無任何預期角色 (例如僅有 AUTHENTICATED_USER)
                            rx.vstack(
                                rx.heading("歡迎", size="7", color_scheme="orange"),
                                rx.text("您的帳號已登入，但目前無特定操作權限。"),
                                rx.text("如有疑問請聯繫系統管理者。"),
                                rx.text(f"您的群組: {DashboardState.current_user_groups.to_string()}"), # type: ignore
                                align_items="center", spacing="3"
                            )
                        )
                    )
                )
            ),
            width="100%",
            padding_x="2em",
            padding_y="1em",
            max_width="container.lg",
            margin="0 auto", # 水平居中
        ),
        align_items="center",
        width="100%",
    )
