"""系統日誌查閱頁面的狀態管理模組。

此模組定義了 `AdminLogsState` 類別，繼承自 `AuthState`，
負責處理系統日誌查閱頁面的所有後端邏輯，包括：
- 載入和篩選系統日誌記錄。
- 管理篩選條件的狀態。
- 控制日誌詳細資訊彈出視窗的顯示。
"""
import reflex as rx
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta # 用於日期篩選的轉換
from beanie.odm.fields import PydanticObjectId # type: ignore # 用於可能的 ID 操作，儘管此處未直接使用

from .auth import AuthState # 基礎身份驗證狀態
from ..models.users import UserGroup # 用於權限檢查
from ..models.system_log import SystemLog, LogLevel # SystemLog 模型及 LogLevel Enum

class AdminLogsState(AuthState):
    """管理系統日誌查閱頁面的狀態與相關邏輯。

    Attributes:
        logs_list (rx.Var[List[SystemLog]]): 從資料庫載入的日誌記錄列表。
        filter_level_str (rx.Var[str]): 用於篩選日誌級別的字串 ("ALL" 或 LogLevel 的值)。
        filter_source (rx.Var[str]): 用於篩選日誌來源的字串。
        filter_user_email (rx.Var[str]): 用於篩選使用者 Email 的字串。
        filter_message_content (rx.Var[str]): 用於篩選日誌訊息內容的字串。
        filter_start_date (rx.Var[str]): 篩選日誌的開始日期 (YYYY-MM-DD)。
        filter_end_date (rx.Var[str]): 篩選日誌的結束日期 (YYYY-MM-DD)。
        show_details_modal (rx.Var[bool]): 控制是否顯示日誌詳細資訊彈出視窗。
        selected_log_for_details (rx.Var[Optional[SystemLog]]): 當前在彈出視窗中顯示的日誌物件。
    """

    logs_list: rx.Var[List[SystemLog]] = rx.Var([])
    
    # 篩選條件狀態變數
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
        """提供給日誌級別篩選下拉選單的選項列表。

        包含 "全部級別" 以及所有 `LogLevel` Enum 的成員。

        Returns:
            List[Dict[str, str]]: 選項列表，每個選項是一個包含 "label" 和 "value" 的字典。
        """
        options = [{"label": "全部級別", "value": "ALL"}]
        options.extend([{"label": level.name, "value": level.value} for level in LogLevel])
        return options

    async def on_page_load(self):
        """頁面載入時執行的非同步操作。

        檢查使用者登入狀態和權限，若符合則載入初始日誌列表。
        若未登入或權限不足，則導向至未授權頁面。
        """
        if not self.is_hydrated or not self.token_is_valid:
            return # 等待客戶端水合或 token 驗證完成
        if not self.is_member_of_any([UserGroup.SYSTEM_ADMIN]): # 確保是系統管理員
            # 導向至預設的未授權頁面路徑 (應在 AuthState 中定義)
            return rx.redirect(getattr(self, "DEFAULT_UNAUTHORIZED_REDIRECT_PATH", "/")) # type: ignore
        await self.fetch_logs()

    async def fetch_logs(self):
        """根據當前的篩選條件從資料庫非同步載入日誌記錄。

        將篩選條件應用於 `SystemLog.find()` 查詢，
        結果按時間戳降序排列，並限制最多載入 200 筆記錄。
        查詢結果會更新 `self.logs_list` 狀態變數。
        """
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

    async def view_log_details(self, log: SystemLog):
        """設定並顯示指定日誌記錄的詳細資訊彈出視窗。

        Args:
            log (SystemLog): 要在彈出視窗中顯示的日誌物件。
        """
        if log:
            self.selected_log_for_details = log
            self.show_details_modal = True
        else:
            # 理論上，從 UI 點擊傳入的 log 物件不應為 None。
            # 此處為防禦性程式碼。
            return rx.toast.error("無法顯示日誌詳情：選擇的日誌無效。") # type: ignore

    def close_details_modal(self):
        """關閉日誌詳細資訊彈出視窗並清除已選擇的日誌。"""
        self.show_details_modal = False
        self.selected_log_for_details = None

    # --- 事件處理器：更新篩選條件並觸發查詢 ---
    async def set_filter_level(self, level_str: str):
        """設定日誌級別篩選條件並重新載入日誌。

        Args:
            level_str (str): 代表所選日誌級別的字串 (來自 Select 元件的 value)。
        """
        self.filter_level_str = level_str
        await self.fetch_logs()

    async def set_filter_source(self, source: str):
        """設定日誌來源篩選條件。

        注意：此方法僅更新狀態變數，通常由 `apply_all_filters` 或輸入框失焦事件觸發查詢。

        Args:
            source (str): 用於篩選日誌來源的字串。
        """
        self.filter_source = source
        # 備註：可考慮是否在輸入時即時搜尋，或提供明確的「套用」按鈕。
        # 若要即時搜尋，可取消下一行的註解：
        # await self.fetch_logs() 

    async def set_filter_user_email(self, email: str):
        """設定使用者 Email 篩選條件。

        Args:
            email (str): 用於篩選使用者 Email 的字串。
        """
        self.filter_user_email = email
        # await self.fetch_logs()

    async def set_filter_message_content(self, content: str):
        """設定日誌訊息內容篩選條件。

        Args:
            content (str): 用於篩選日誌訊息內容的關鍵字字串。
        """
        self.filter_message_content = content
        # await self.fetch_logs()

    async def set_filter_start_date(self, date_str: str):
        """設定日誌開始日期篩選條件。

        Args:
            date_str (str): 代表開始日期的字串 (格式 YYYY-MM-DD)。
        """
        self.filter_start_date = date_str
        # 備註：日期篩選通常在使用者完成選擇（例如失焦）或點擊「套用」按鈕時才觸發查詢。
        # await self.fetch_logs()

    async def set_filter_end_date(self, date_str: str):
        """設定日誌結束日期篩選條件。

        Args:
            date_str (str): 代表結束日期的字串 (格式 YYYY-MM-DD)。
        """
        self.filter_end_date = date_str
        # await self.fetch_logs()
    
    async def apply_all_filters(self):
        """手動觸發一次查詢，套用目前所有已設定的篩選條件。"""
        await self.fetch_logs()
