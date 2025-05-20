import reflex as rx
from reflex_google_auth import require_google_login
from ..states.auth import AuthState, authorize_by_groups
from ..models.users import UserGroup
from ..models.system_log import SystemLog
from ..components import navbar

# TODO: 建立 AdminLogsState，繼承 AuthState。
#       應包含：
#       - logs_list: rx.Var[list[SystemLog]]
#       - filter_level: rx.Var[str] (e.g., "ALL", "INFO", "ERROR")
#       - filter_content: rx.Var[str]
#       - filter_start_date: rx.Var[str]
#       - filter_end_date: rx.Var[str]
#       - show_details_modal: rx.Var[bool]
#       - selected_log_details: rx.Var[Optional[SystemLog]]
#       - async def load_logs(self):
#       - async def view_log_details(self, log_id: str):

# class AdminLogsState(AuthState):
#     logs_list: rx.Var[list[SystemLog]] = []
#     filter_level: rx.Var[str] = "ALL"
#     # ... 其他 rx.Var 和事件處理器 ...
#
#     async def on_load(self):
#         # await self.fetch_logs()
#         print("TODO: AdminLogsState.on_load 載入日誌")
#
#     async def fetch_logs(self):
#         # query_conditions = {}
#         # if self.filter_level != "ALL":
#         #     query_conditions["level"] = self.filter_level
#         # if self.filter_content:
#         #     query_conditions["message"] = {"$regex": self.filter_content, "$options": "i"} # 簡易訊息搜尋
#         # # TODO: 日期範圍篩選 (需轉換日期字串為 datetime 物件)
#         # self.logs_list = await SystemLog.find(query_conditions, sort=[("created_at", -1)]).limit(100).to_list() # 限制筆數
#         print(f"TODO: AdminLogsState.fetch_logs 載入日誌 (篩選條件...)")
#
#     # TODO: 實作 view_log_details, Modal 控制等

@rx.page(route="/admin-logs", title="系統日誌") # 路由根據 dashboard.py 中的連結調整
@require_google_login
# @authorize_by_groups(required_groups=[UserGroup.SYSTEM_ADMIN]) # 改由 State 控制權限
def admin_logs() -> rx.Component:
    """
    系統管理者頁面，用於查閱系統運作日誌與錯誤記錄。
    TODO: 此頁面應綁定到 AdminLogsState。
    """
    # TODO: 實現日誌詳細資訊 Modal (rx.modal)

    return rx.vstack(
        navbar(),
        rx.heading("系統日誌查閱", size="lg", margin_bottom="1em"),
        rx.text("（TODO: 此頁面應綁定到 AdminLogsState）"),
        rx.hstack(
            # rx.select(
            #     ["ALL", "INFO", "WARNING", "ERROR"], # 應與 SystemLog 中的 level 一致
            #     value=AdminLogsState.filter_level,
            #     on_change=AdminLogsState.set_filter_level,
            #     placeholder="選擇日誌級別",
            # ),
            # rx.input(placeholder="搜尋日誌內容...", value=AdminLogsState.filter_content, on_change=AdminLogsState.set_filter_content),
            # rx.input(type_="date", value=AdminLogsState.filter_start_date, on_change=AdminLogsState.set_filter_start_date),
            # rx.input(type_="date", value=AdminLogsState.filter_end_date, on_change=AdminLogsState.set_filter_end_date),
            # rx.button("查詢", on_click=AdminLogsState.fetch_logs),
            rx.select(["全部", "INFO", "WARNING", "ERROR"], placeholder="選擇日誌級別 (TODO)"),
            rx.input(placeholder="搜尋日誌內容... (TODO)"),
            rx.input(placeholder="開始日期 (YYYY-MM-DD) (TODO)", type_="date"),
            rx.input(placeholder="結束日期 (YYYY-MM-DD) (TODO)", type_="date"),
            rx.button("查詢 (TODO)"),
            spacing="1em",
            margin_bottom="1em",
            flex_wrap="wrap" # 允許換行
        ),
        # rx.foreach(
        #     AdminLogsState.logs_list,
        #     lambda log: rx.box(
        #         rx.text(f"時間：{log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else 'N/A'}"),
        #         rx.text(f"級別：{log.level}"),
        #         rx.text(f"訊息：{log.message}"),
        #         # ... 其他欄位 ...
        #         # rx.button("查看詳情", on_click=lambda: AdminLogsState.view_log_details(str(log.id))),
        #         border="1px solid #ddd", padding="1em", margin="0.5em 0", border_radius="5px",
        #     )
        # ),
        rx.text("（TODO: 日誌列表顯示區，應使用 rx.data_table 或 rx.foreach）"),
        
        # TODO: 日誌詳細資訊 Modal

        align_items="center",
        padding="2em",
        # on_mount=AdminLogsState.on_load
    )

# 以下 TODO 函式應移至 AdminLogsState 中
# TODO: filter_logs_by_level(value) -> AdminLogsState.set_filter_level(value)
# TODO: filter_logs_by_content(value) -> AdminLogsState.set_filter_content(value)
# TODO: filter_logs_by_start_date(value) -> AdminLogsState.set_filter_start_date(value)
# TODO: filter_logs_by_end_date(value) -> AdminLogsState.set_filter_end_date(value)
# TODO: show_log_details(log_id) -> AdminLogsState.view_log_details(log_id)
