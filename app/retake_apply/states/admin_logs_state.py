import reflex as rx
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta # 用於日期轉換
from beanie.odm.fields import PydanticObjectId # type: ignore

from .auth import AuthState
from ..models.users import UserGroup
from ..models.system_log import SystemLog, LogLevel # 匯入 LogLevel Enum

class AdminLogsState(AuthState):
    """管理系統日誌查閱頁面的狀態與邏輯"""

    logs_list: rx.Var[List[SystemLog]] = rx.Var([])
    
    # 篩選條件
    filter_level_str: rx.Var[str] = "ALL"  # 綁定 Select，值為 LogLevel.value 或 "ALL"
    filter_source: rx.Var[str] = ""
    filter_user_email: rx.Var[str] = ""
    filter_message_content: rx.Var[str] = ""
    filter_start_date: rx.Var[str] = "" # YYYY-MM-DD
    filter_end_date: rx.Var[str] = ""   # YYYY-MM-DD
    
    # 日誌詳細資訊 Modal 控制
    show_details_modal: rx.Var[bool] = False
    selected_log_for_details: rx.Var[Optional[SystemLog]] = None

    @rx.var
    def log_level_options(self) -> List[Dict[str, str]]:
        """提供給 Select 元件的日誌級別選項"""
        options = [{"label": "全部級別", "value": "ALL"}]
        options.extend([{"label": level.name, "value": level.value} for level in LogLevel])
        return options

    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            return
        if not self.is_member_of_any([UserGroup.ADMIN]): # 假設 UserGroup.ADMIN 是系統管理員
            return rx.redirect(self.DEFAULT_UNAUTHORIZED_REDIRECT_PATH) # type: ignore
        await self.fetch_logs()

    async def fetch_logs(self):
        """根據篩選條件載入日誌"""
        query_conditions: Dict[str, Any] = {}
        
        if self.filter_level_str != "ALL":
            try:
                # 從字串值轉換回 LogLevel Enum 成員
                log_level_enum = LogLevel(self.filter_level_str)
                query_conditions["level"] = log_level_enum
            except ValueError:
                # 如果 filter_level_str 不是有效的 LogLevel 值 (理論上不應發生，因 UI 綁定選項)
                # 可以選擇忽略此篩選或報錯
                pass 
        
        if self.filter_source:
            query_conditions["source"] = {"$regex": self.filter_source, "$options": "i"}
        
        if self.filter_user_email:
            query_conditions["user_email"] = {"$regex": self.filter_user_email, "$options": "i"}

        if self.filter_message_content:
            query_conditions["message"] = {"$regex": self.filter_message_content, "$options": "i"}
        
        date_filter: Dict[str, datetime] = {}
        try:
            if self.filter_start_date:
                start_dt = datetime.strptime(self.filter_start_date, "%Y-%m-%d")
                date_filter["$gte"] = datetime(start_dt.year, start_dt.month, start_dt.day, 0, 0, 0)
            if self.filter_end_date:
                end_dt = datetime.strptime(self.filter_end_date, "%Y-%m-%d")
                # 包含結束日期當天，所以查詢到隔天零點
                date_filter["$lt"] = datetime(end_dt.year, end_dt.month, end_dt.day) + timedelta(days=1)
        except ValueError:
            # 可以在 UI 上顯示日期格式錯誤的提示
            # 此處暫不處理，讓查詢繼續 (可能不含日期篩選)
            # rx.toast.error("日期格式不正確，請使用 YYYY-MM-DD。")
            pass 
        
        if date_filter:
            query_conditions["timestamp"] = date_filter # 模型中已改為 timestamp
        
        self.logs_list = await SystemLog.find(query_conditions, sort=[("timestamp", -1)]).limit(200).to_list()

    async def view_log_details(self, log: SystemLog): # 直接傳遞 SystemLog 物件
        """顯示指定日誌的詳細資訊"""
        if log:
            self.selected_log_for_details = log
            self.show_details_modal = True
        else:
            # 理論上 log 物件是從列表中點擊傳入，不應為 None
            return rx.toast.error("無法顯示日誌詳情：日誌不存在。") # type: ignore

    def close_details_modal(self):
        self.show_details_modal = False
        self.selected_log_for_details = None

    # 事件處理器用於更新篩選條件並觸發查詢
    async def set_filter_level(self, level_str: str):
        self.filter_level_str = level_str
        await self.fetch_logs()

    async def set_filter_source(self, source: str):
        self.filter_source = source
        # 考慮是否即時搜尋或提供按鈕
        # await self.fetch_logs() 

    async def set_filter_user_email(self, email: str):
        self.filter_user_email = email
        # await self.fetch_logs()

    async def set_filter_message_content(self, content: str):
        self.filter_message_content = content
        # await self.fetch_logs()

    async def set_filter_start_date(self, date_str: str):
        self.filter_start_date = date_str
        # await self.fetch_logs() # 日期通常在失去焦點或按鈕點擊時更新

    async def set_filter_end_date(self, date_str: str):
        self.filter_end_date = date_str
        # await self.fetch_logs()
    
    async def apply_all_filters(self):
        """手動觸發套用所有篩選條件並重新查詢"""
        await self.fetch_logs()
