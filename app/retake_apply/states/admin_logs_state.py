import reflex as rx
from typing import List, Optional, Dict
from datetime import datetime # 用於日期轉換

from .auth import AuthState
from ..models.users import UserGroup
from ..models.system_log import SystemLog # 假設 SystemLog 模型已定義

class AdminLogsState(AuthState):
    """管理系統日誌查閱頁面的狀態與邏輯"""

    logs_list: rx.Var[List[SystemLog]] = rx.Var([])
    
    # 篩選條件
    filter_level: rx.Var[str] = "ALL"  # "ALL", "INFO", "WARNING", "ERROR"
    filter_content: rx.Var[str] = ""
    filter_start_date: rx.Var[str] = "" # YYYY-MM-DD
    filter_end_date: rx.Var[str] = ""   # YYYY-MM-DD
    
    # 日誌詳細資訊 Modal 控制
    show_details_modal: rx.Var[bool] = False
    selected_log_for_details: rx.Var[Optional[SystemLog]] = None

    # 日誌級別選項
    LOG_LEVEL_OPTIONS: List[Dict[str, str]] = [
        {"label": "全部級別", "value": "ALL"},
        {"label": "資訊 (INFO)", "value": "INFO"},
        {"label": "警告 (WARNING)", "value": "WARNING"},
        {"label": "錯誤 (ERROR)", "value": "ERROR"},
        # TODO: 根據 SystemLog 模型中實際使用的級別調整
    ]

    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            return
        if UserGroup.SYSTEM_ADMIN not in self.current_user_groups:
            # return rx.redirect("/unauthorized")
            pass
        await self.fetch_logs()

    async def fetch_logs(self):
        """根據篩選條件載入日誌"""
        # query_conditions = {}
        # if self.filter_level != "ALL":
        #     query_conditions["level"] = self.filter_level
        #
        # if self.filter_content:
        #     # 搜尋 message 和 details 欄位
        #     search_regex = {"$regex": self.filter_content, "$options": "i"}
        #     query_conditions["$or"] = [
        #         {"message": search_regex},
        #         {"details": search_regex}
        #     ]
        #
        # date_filter = {}
        # try:
        #     if self.filter_start_date:
        #         date_filter["$gte"] = datetime.strptime(self.filter_start_date, "%Y-%m-%d")
        #     if self.filter_end_date:
        #         # 包含結束日期當天，所以查詢到隔天零點
        #         end_date_dt = datetime.strptime(self.filter_end_date, "%Y-%m-%d")
        #         date_filter["$lt"] = datetime(end_date_dt.year, end_date_dt.month, end_date_dt.day + 1) # type: ignore
        # except ValueError:
        #     # return rx.toast.error("日期格式不正確，請使用 YYYY-MM-DD。")
        #     print("日期格式不正確") # 暫時用 print
        #
        # if date_filter:
        #     query_conditions["created_at"] = date_filter
        #
        # # self.logs_list = await SystemLog.find(query_conditions, sort=[("created_at", -1)]).limit(200).to_list() # 限制筆數
        print(f"TODO: AdminLogsState.fetch_logs 尚未從資料庫載入。篩選條件: Level={self.filter_level}, Content='{self.filter_content}', Start='{self.filter_start_date}', End='{self.filter_end_date}'")
        # 模擬資料
        # self.logs_list = [
        #     SystemLog(level="INFO", message="使用者登入成功", source="auth.py", user_id="user1@example.com", created_at=datetime.now()),
        #     SystemLog(level="ERROR", message="資料庫連接失敗", source="db.py", details="Connection timed out", created_at=datetime.now())
        # ]

    async def view_log_details(self, log_id_str: str):
        """顯示指定日誌的詳細資訊"""
        # log = await SystemLog.get(log_id_str) # Beanie 0.24+ PydanticObjectId(log_id_str)
        # if log:
        #     self.selected_log_for_details = log
        #     self.show_details_modal = True
        # else:
        #     rx.toast.error("找不到該日誌記錄。")
        print(f"TODO: view_log_details 尚未實作，日誌 ID: {log_id_str}")
        # 模擬
        # self.selected_log_for_details = SystemLog(level="INFO", message="模擬日誌詳情", details="這是模擬的完整日誌內容...", created_at=datetime.now())
        # self.show_details_modal = True


    def close_details_modal(self):
        self.show_details_modal = False
        self.selected_log_for_details = None

    # 事件處理器用於更新篩選條件
    def set_filter_level_handler(self, level: str):
        self.filter_level = level
        # await self.fetch_logs() # 可選擇即時更新或按鈕觸發

    def set_filter_content_handler(self, content: str):
        self.filter_content = content
        # await self.fetch_logs()

    def set_filter_start_date_handler(self, date_str: str):
        self.filter_start_date = date_str
        # await self.fetch_logs()

    def set_filter_end_date_handler(self, date_str: str):
        self.filter_end_date = date_str
        # await self.fetch_logs()
