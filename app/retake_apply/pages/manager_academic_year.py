import reflex as rx
from reflex_google_auth import require_google_login
from ..states.auth import require_group # 從 auth.py 匯入 require_group
from ..models.users import UserGroup
# from ..models.academic_year_setting import AcademicYearSetting # 不直接在此使用模型
from ..components import navbar
from ..states.manager_academic_year_state import ManagerAcademicYearState # 匯入對應的 State
from ..utils.funcs import format_datetime_to_taipei_str # 匯入時間格式化函式

@rx.page(
    route="/manager/academic-year",  # 建議使用 manager/ 前綴
    title="學年度管理",
    on_load=ManagerAcademicYearState.on_page_load # 頁面載入時觸發
)
@require_google_login
@require_group(allowed_groups=[UserGroup.COURSE_MANAGER, UserGroup.ADMIN])
def manager_academic_year_page() -> rx.Component:
    """課程管理者頁面，用於設定與調整系統運作的學年度及學生登記時間。"""
    return rx.vstack(
        navbar(),
        rx.box(
            rx.heading("學年度與登記時間設定", size="7", margin_bottom="1em"),
            rx.text("設定系統目前運作的學年度，以及學生選課登記的起迄時間。"),
            
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.text("目前生效學年度:", weight="bold"),
                        rx.text(ManagerAcademicYearState.current_academic_year_str),
                        spacing="3",
                        align_items="center"
                    ),
                    rx.hstack(
                        rx.text("登記開始時間:", weight="bold"),
                        rx.text(ManagerAcademicYearState.current_reg_start_time_str),
                        spacing="3",
                        align_items="center"
                    ),
                    rx.hstack(
                        rx.text("登記結束時間:", weight="bold"),
                        rx.text(ManagerAcademicYearState.current_reg_end_time_str),
                        spacing="3",
                        align_items="center"
                    ),
                    spacing="3",
                ),
                margin_bottom="1.5em"
            ),

            rx.heading("設定新學年度與登記時間", size="5", margin_top="1.5em", margin_bottom="0.5em"),
            rx.vstack(
                rx.form.root(
                    rx.vstack(
                        rx.form.field(
                            rx.form.label("新學年度 (例如: 113-1):"),
                            rx.form.control(
                                rx.input(
                                    placeholder="XXX-S (S為1或2)",
                                    value=ManagerAcademicYearState.new_academic_year_input,
                                    on_change=ManagerAcademicYearState.set_new_academic_year_input, # type: ignore
                                    required=True,
                                ),
                            ),
                            rx.cond(
                                ManagerAcademicYearState.year_input_error_message != "",
                                rx.form.message(ManagerAcademicYearState.year_input_error_message, color_scheme="red"), # type: ignore
                            ),
                            width="100%",
                        ),
                        rx.form.field(
                            rx.form.label("登記開始時間:"),
                            rx.form.control(
                                rx.input(
                                    type_="datetime-local",
                                    value=ManagerAcademicYearState.new_reg_start_time_input,
                                    on_change=ManagerAcademicYearState.set_new_reg_start_time_input, # type: ignore
                                ),
                            ),
                             rx.cond(
                                ManagerAcademicYearState.start_time_error_message != "",
                                rx.form.message(ManagerAcademicYearState.start_time_error_message, color_scheme="red"), # type: ignore
                            ),
                            width="100%",
                        ),
                        rx.form.field(
                            rx.form.label("登記結束時間:"),
                            rx.form.control(
                                rx.input(
                                    type_="datetime-local",
                                    value=ManagerAcademicYearState.new_reg_end_time_input,
                                    on_change=ManagerAcademicYearState.set_new_reg_end_time_input, # type: ignore
                                ),
                            ),
                            rx.cond(
                                ManagerAcademicYearState.end_time_error_message != "",
                                rx.form.message(ManagerAcademicYearState.end_time_error_message, color_scheme="red"), # type: ignore
                            ),
                            width="100%",
                        ),
                        rx.form.submit(
                            rx.button("確認設定", type="submit", size="3"), # type: ignore
                            width="100%",
                            margin_top="1em",
                        ),
                        spacing="4",
                        width="100%",
                        max_width="500px",
                    ),
                    on_submit=ManagerAcademicYearState.handle_set_new_academic_year,
                    width="100%",
                ),
                align_items="center", # 使表單居中
                width="100%",
                margin_bottom="2em",
            ),

            rx.heading("學年度設定歷史記錄", size="5", margin_top="2em", margin_bottom="0.5em"),
            rx.cond(
                ManagerAcademicYearState.academic_year_history.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("學年度"),
                            rx.table.column_header_cell("登記開始"),
                            rx.table.column_header_cell("登記結束"),
                            rx.table.column_header_cell("設定者"),
                            rx.table.column_header_cell("設定時間"),
                            rx.table.column_header_cell("目前有效"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            ManagerAcademicYearState.academic_year_history,
                            lambda setting: rx.table.row(
                                rx.table.cell(setting.academic_year),
                                rx.table.cell(format_datetime_to_taipei_str(setting.registration_start_time, "%Y-%m-%d %H:%M") if setting.registration_start_time else "未設定"),
                                rx.table.cell(format_datetime_to_taipei_str(setting.registration_end_time, "%Y-%m-%d %H:%M") if setting.registration_end_time else "未設定"),
                                rx.table.cell(setting.set_by_user_email or "N/A"),
                                rx.table.cell(format_datetime_to_taipei_str(setting.set_at, "%Y-%m-%d %H:%M:%S") if setting.set_at else "N/A"), # 加上 if 判斷
                                rx.table.cell(rx.badge("是", color_scheme="green") if setting.is_active else rx.badge("否", color_scheme="gray")),
                            )
                        )
                    ),
                    variant="surface", # Radix Table variant
                    width="100%",
                ),
                rx.text("尚無歷史設定記錄。", color_scheme="gray", margin_top="1em")
            ),
            width="100%",
            padding_x="2em",
            padding_y="1em",
            max_width="container.lg", # 限制最大寬度
            margin="0 auto", # 水平居中
        ),
        align_items="center", # vstack 內容居中
        width="100%",
    )
