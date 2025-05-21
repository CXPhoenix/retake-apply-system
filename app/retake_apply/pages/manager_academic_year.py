"""課程管理者設定學年度與登記時間頁面模組。

此模組定義了供課程管理者（及系統管理者）設定和調整
系統當前運作學年度以及學生選課登記起迄時間的 Reflex 頁面。
頁面同時會展示學年度設定的歷史記錄。
"""
import reflex as rx
from reflex_google_auth import require_google_login
from ..states.auth import require_group # 從 auth.py 匯入權限群組檢查裝飾器
from ..models.users import UserGroup # UserGroup Enum 用於角色定義與檢查
# AcademicYearSetting 模型主要在 ManagerAcademicYearState 中使用，此處不直接匯入。
from ..components import navbar # 引入共用的導覽列元件
from ..states.manager_academic_year_state import ManagerAcademicYearState # 匯入此頁面專用的狀態管理類
from ..utils.funcs import format_datetime_to_taipei_str # 匯入日期時間格式化輔助函式

@rx.page(
    route="/manager/academic-year",  # 建議使用 manager/ 前綴以區分管理功能
    title="學年度管理",
    on_load=ManagerAcademicYearState.on_page_load # 頁面載入時觸發的事件
)
@require_google_login # 要求使用者必須先登入 Google 帳號
@require_group(allowed_groups=[UserGroup.COURSE_MANAGER, UserGroup.SYSTEM_ADMIN]) # 課程管理者或系統管理者可訪問
def manager_academic_year_page() -> rx.Component:
    """課程管理者設定學年度與學生登記時間的頁面元件。

    此頁面顯示當前生效的學年度與登記時間，提供表單讓管理者設定新的學年度及時間，
    並列出歷史設定記錄以供參考。

    Returns:
        rx.Component: 組建完成的學年度管理頁面。
    """
    return rx.vstack(
        navbar(), # 頁面頂部導覽列
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
