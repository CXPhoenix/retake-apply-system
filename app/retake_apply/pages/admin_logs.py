"""系統日誌查閱頁面模組。

此模組定義了供系統管理者查閱系統運作日誌的 Reflex 頁面。
頁面包含篩選日誌的功能，並以表格形式展示日誌列表，
同時提供查看單筆日誌詳細資訊的彈出視窗。
"""
import reflex as rx
from reflex_google_auth import require_google_login
import json # 用於格式化顯示 JSON details

from ..states.auth import require_group # 引入權限群組檢查裝飾器
from ..models.users import UserGroup
from ..models.system_log import LogLevel # 匯入 LogLevel
from ..components import navbar
from ..states.admin_logs_state import AdminLogsState # 匯入此頁面專用的狀態管理類
from ..utils.funcs import format_datetime_to_taipei_str # 匯入日期時間格式化輔助函式

def get_log_level_color(level: LogLevel) -> str:
    """根據日誌級別返回對應的 Radix Themes 顏色方案 (color_scheme) 字串。

    Args:
        level (LogLevel): 日誌的級別。

    Returns:
        str: 對應於該日誌級別的顏色方案字串 (例如 "red", "amber", "blue")。
    """
    if level == LogLevel.ERROR or level == LogLevel.CRITICAL:
        return "red"
    if level == LogLevel.WARNING:
        return "amber"
    if level == LogLevel.INFO:
        return "blue"
    if level == LogLevel.DEBUG:
        return "gray"
    return "gray"

@rx.page(
    route="/admin/logs", # 建議使用 admin/ 前綴
    title="系統日誌查閱",
    on_load=AdminLogsState.on_page_load # 頁面載入時觸發的事件
)
@require_google_login # 要求使用者必須先登入 Google 帳號
@require_group(allowed_groups=[UserGroup.SYSTEM_ADMIN]) # 要求使用者必須屬於 SYSTEM_ADMIN 群組
def admin_logs_page() -> rx.Component:
    """系統管理者查閱系統日誌的頁面元件。

    此頁面允許管理者透過多種條件篩選日誌，
    並以表格形式展示日誌列表，點擊可查看日誌詳情。

    Returns:
        rx.Component: 組建完成的系統日誌查閱頁面。
    """
    return rx.vstack(
        navbar(), # 頁面頂部導覽列
        rx.box(
            rx.heading("系統日誌查閱", size="7", margin_bottom="1em"),
            
            rx.grid(
                rx.form.field(
                    rx.form.label("日誌級別:"),
                    rx.select.root(
                        rx.select.trigger(placeholder="選擇日誌級別"),
                        rx.select.content(
                            rx.foreach(
                                AdminLogsState.log_level_options, # type: ignore
                                lambda option: rx.select.item(option["label"], value=option["value"])
                            )
                        ),
                        value=AdminLogsState.filter_level_str,
                        on_change=AdminLogsState.set_filter_level, # type: ignore
                        name="log_level_filter"
                    ),
                    grid_column="span 2",
                ),
                rx.form.field(
                    rx.form.label("日誌來源:"),
                    rx.input(
                        placeholder="例如: AuthState",
                        value=AdminLogsState.filter_source,
                        on_change=AdminLogsState.set_filter_source, # type: ignore
                        on_blur=AdminLogsState.apply_all_filters, # type: ignore
                    ),
                    grid_column="span 2",
                ),
                rx.form.field(
                    rx.form.label("使用者 Email:"),
                    rx.input(
                        placeholder="輸入 Email",
                        value=AdminLogsState.filter_user_email,
                        on_change=AdminLogsState.set_filter_user_email, # type: ignore
                        on_blur=AdminLogsState.apply_all_filters, # type: ignore
                    ),
                    grid_column="span 2",
                ),
                rx.form.field(
                    rx.form.label("訊息內容包含:"),
                    rx.input(
                        placeholder="輸入關鍵字",
                        value=AdminLogsState.filter_message_content,
                        on_change=AdminLogsState.set_filter_message_content, # type: ignore
                        on_blur=AdminLogsState.apply_all_filters, # type: ignore
                    ),
                    grid_column="span 6", # 佔滿剩餘空間
                ),
                rx.form.field(
                    rx.form.label("開始日期:"),
                    rx.input(
                        type_="date",
                        value=AdminLogsState.filter_start_date,
                        on_change=AdminLogsState.set_filter_start_date, # type: ignore
                        on_blur=AdminLogsState.apply_all_filters, # type: ignore
                    ),
                    grid_column="span 3",
                ),
                rx.form.field(
                    rx.form.label("結束日期:"),
                    rx.input(
                        type_="date",
                        value=AdminLogsState.filter_end_date,
                        on_change=AdminLogsState.set_filter_end_date, # type: ignore
                        on_blur=AdminLogsState.apply_all_filters, # type: ignore
                    ),
                    grid_column="span 3",
                ),
                rx.button(
                    "套用篩選", 
                    on_click=AdminLogsState.apply_all_filters, # type: ignore
                    grid_column="span 2", 
                    margin_top="1.75em", # 對齊 Label
                    size="2"
                ),
                columns="12", # 總共 12 欄
                spacing="3",
                width="100%",
                margin_bottom="1.5em"
            ),

            rx.cond(
                AdminLogsState.logs_list.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("時間戳"),
                            rx.table.column_header_cell("級別"),
                            rx.table.column_header_cell("來源"),
                            rx.table.column_header_cell("使用者"),
                            rx.table.column_header_cell("訊息"),
                            rx.table.column_header_cell("操作"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            AdminLogsState.logs_list,
                            lambda log: rx.table.row(
                                rx.table.cell(format_datetime_to_taipei_str(log.timestamp)), # 使用輔助函式
                                rx.table.cell(rx.badge(log.level.value, color_scheme=get_log_level_color(log.level))),
                                rx.table.cell(log.source or "N/A"),
                                rx.table.cell(log.user_email or "N/A"),
                                rx.table.cell(
                                    rx.text(
                                        log.message, 
                                        white_space="nowrap", # 保持單行
                                        overflow="hidden", 
                                        text_overflow="ellipsis", 
                                        max_width="300px", # 限制寬度
                                        title=log.message # 滑鼠懸停顯示完整訊息
                                    )
                                ),
                                rx.table.cell(
                                    rx.button("詳情", on_click=lambda: AdminLogsState.view_log_details(log), size="1") # type: ignore
                                ),
                            )
                        )
                    ),
                    variant="surface",
                    width="100%",
                ),
                rx.text("找不到符合條件的日誌記錄。", color_scheme="gray", margin_top="1em")
            ),
            
            # 日誌詳細資訊 Modal
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("日誌詳情"),
                    rx.cond(
                        AdminLogsState.selected_log_for_details,
                        rx.vstack(
                            rx.text(f"時間戳: {format_datetime_to_taipei_str(AdminLogsState.selected_log_for_details.timestamp, '%Y-%m-%d %H:%M:%S.%f') if AdminLogsState.selected_log_for_details else 'N/A'}"), # type: ignore
                            rx.text(f"級別: {AdminLogsState.selected_log_for_details.level.value if AdminLogsState.selected_log_for_details.level else 'N/A'}"), # type: ignore
                            rx.text(f"來源: {AdminLogsState.selected_log_for_details.source or 'N/A'}"), # type: ignore
                            rx.text(f"使用者: {AdminLogsState.selected_log_for_details.user_email or 'N/A'}"), # type: ignore
                            rx.text("訊息:", weight="bold"),
                            rx.text(AdminLogsState.selected_log_for_details.message, white_space="pre-wrap"), # type: ignore
                            rx.cond(
                                AdminLogsState.selected_log_for_details.details, # type: ignore
                                rx.vstack(
                                    rx.text("詳細資料:", weight="bold", margin_top="0.5em"),
                                    rx.code_block(
                                        json.dumps(AdminLogsState.selected_log_for_details.details, indent=2, ensure_ascii=False), # type: ignore
                                        language="json",
                                        can_copy=True,
                                        theme="light", # 或其他主題
                                        width="100%",
                                        max_height="300px", # 限制高度可滾動
                                    ),
                                    align_items="start",
                                    width="100%"
                                )
                            ),
                            spacing="2",
                            align_items="start",
                            width="100%"
                        ),
                        rx.text("沒有選擇日誌。") # 理論上不應顯示
                    ),
                    rx.dialog.close(
                        rx.button("關閉", on_click=AdminLogsState.close_details_modal, margin_top="1em", variant="soft") # type: ignore
                    ),
                    min_width="600px" # 讓 Modal 寬一點
                ),
                open=AdminLogsState.show_details_modal, # type: ignore
                on_open_change=AdminLogsState.set_show_details_modal, # type: ignore
            ),
            width="100%",
            padding_x="2em",
            padding_y="1em",
            max_width="container.xl", # 使用更大的容器寬度
            margin="0 auto",
        ),
        align_items="center",
        width="100%",
    )
