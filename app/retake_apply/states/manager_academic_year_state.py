"""學年度與登記時間管理頁面的狀態管理模組。

此模組定義了 `ManagerAcademicYearState` 類別，繼承自 `AuthState`，
負責處理課程管理者（及系統管理者）設定和調整系統當前運作學年度
以及學生選課登記起迄時間的相關邏輯。
"""
import reflex as rx
from typing import List, Optional
import re # 用於學年度格式驗證
from datetime import datetime, timezone, timedelta # 用於日期時間處理與時區轉換

from .auth import AuthState # 基礎身份驗證狀態
from ..models.users import UserGroup # 用於權限檢查
from ..models.academic_year_setting import AcademicYearSetting # 學年度設定模型
from ..utils.funcs import format_datetime_to_taipei_str # 日期時間格式化輔助函式

class ManagerAcademicYearState(AuthState):
    """管理學年度與登記時間設定頁面的狀態與相關邏輯。

    Attributes:
        current_setting_display (rx.Var[Optional[AcademicYearSetting]]): 
            儲存當前生效的 `AcademicYearSetting` 物件，用於在 UI 中顯示。
        academic_year_history (rx.Var[List[AcademicYearSetting]]): 
            儲存所有學年度設定的歷史記錄列表。
        new_academic_year_input (rx.Var[str]): 
            綁定到新學年度輸入框的值。
        new_reg_start_time_input (rx.Var[str]): 
            綁定到新登記開始時間輸入框的值 (格式 YYYY-MM-DDTHH:MM)。
        new_reg_end_time_input (rx.Var[str]): 
            綁定到新登記結束時間輸入框的值 (格式 YYYY-MM-DDTHH:MM)。
        year_input_error_message (rx.Var[str]): 
            學年度輸入格式錯誤時的提示訊息。
        start_time_error_message (rx.Var[str]): 
            登記開始時間輸入格式錯誤時的提示訊息。
        end_time_error_message (rx.Var[str]): 
            登記結束時間輸入格式錯誤或邏輯錯誤時的提示訊息。
    """

    current_setting_display: Optional[AcademicYearSetting] = None
    academic_year_history: List[AcademicYearSetting] = []
    
    # --- 新學年度設定表單相關狀態 ---
    new_academic_year_input: str = ""
    new_reg_start_time_input: str = "" # HTML datetime-local input format
    new_reg_end_time_input: str = ""   # HTML datetime-local input format

    # --- 表單驗證錯誤訊息 ---
    year_input_error_message: str = ""
    start_time_error_message: str = ""
    end_time_error_message: str = ""

    @rx.var
    def current_academic_year_str(self) -> str:
        """計算屬性：顯示用的當前生效學年度字串。

        Returns:
            str: 當前學年度字串，若未設定則為 "尚未設定"。
        """
        if self.current_setting_display:
            return self.current_setting_display.academic_year
        return "尚未設定"

    @rx.var
    def current_reg_start_time_str(self) -> str:
        """計算屬性：顯示用的當前登記開始時間字串 (台北時間)。

        Returns:
            str: 格式化後的登記開始時間字串，若未設定則為 "未設定"。
        """
        if self.current_setting_display and self.current_setting_display.registration_start_time:
            # 假設 registration_start_time 在資料庫中儲存的是 UTC 時間
            return format_datetime_to_taipei_str(self.current_setting_display.registration_start_time, "%Y-%m-%d %H:%M")
        return "未設定"

    @rx.var
    def current_reg_end_time_str(self) -> str:
        """計算屬性：顯示用的當前登記結束時間字串 (台北時間)。

        Returns:
            str: 格式化後的登記結束時間字串，若未設定則為 "未設定"。
        """
        if self.current_setting_display and self.current_setting_display.registration_end_time:
            # 假設 registration_end_time 在資料庫中儲存的是 UTC 時間
            return format_datetime_to_taipei_str(self.current_setting_display.registration_end_time, "%Y-%m-%d %H:%M")
        return "未設定"

    async def on_page_load(self):
        """頁面載入時執行的非同步操作。

        檢查使用者登入狀態和權限 (課程管理者或系統管理員)，
        若符合則載入當前學年度設定和歷史記錄。
        若未登入或權限不足，則導向至未授權頁面。
        """
        if not self.is_hydrated or not self.token_is_valid:
            return # 等待客戶端水合或 token 驗證完成
        
        # 權限檢查
        if not self.is_member_of_any([UserGroup.COURSE_MANAGER, UserGroup.SYSTEM_ADMIN]):
            # 若非課程管理者或系統管理員，則重導向
            return rx.redirect(getattr(self, "DEFAULT_UNAUTHORIZED_REDIRECT_PATH", "/")) # type: ignore
        
        await self.load_current_and_history()

    async def load_current_and_history(self):
        """從資料庫載入當前生效的學年度設定以及所有歷史設定記錄。

        查詢結果會更新 `current_setting_display` 和 `academic_year_history` 狀態變數。
        """
        self.current_setting_display = await AcademicYearSetting.get_current()
        self.academic_year_history = await AcademicYearSetting.find_all(sort=[("set_at", -1)]).to_list()
        # console.debug(f"學年度資料已載入 - 當前: {self.current_setting_display.academic_year if self.current_setting_display else '無'}, 歷史數量: {len(self.academic_year_history)}")

    def _validate_academic_year_format(self, year_string: str) -> bool:
        """內部輔助函式：驗證學年度字串的格式是否符合 "XXX-S" (S為1或2)。

        Args:
            year_string (str): 待驗證的學年度字串。

        Returns:
            bool: 若格式正確則回傳 `True` 並清除錯誤訊息，否則回傳 `False` 並設定錯誤訊息。
        """
        pattern = r"^\d{3}-(1|2)$" # 例如 113-1, 114-2
        if not year_string:
            self.year_input_error_message = "學年度不可為空。"
            return False
        if re.match(pattern, year_string):
            self.year_input_error_message = "" # 清除錯誤訊息
            return True
        else:
            self.year_input_error_message = "格式錯誤，應為 XXX-1 或 XXX-2 (例如 113-1)"
            return False

    def _parse_datetime_input(self, datetime_str: str, field_name: str) -> Optional[datetime]:
        """內部輔助函式：解析來自 HTML datetime-local 輸入框的日期時間字串。

        將 "YYYY-MM-DDTHH:MM" 格式的本地時間（假設為台北時間 UTC+8）
        轉換為 timezone-aware 的 UTC `datetime` 物件。

        Args:
            datetime_str (str): HTML datetime-local 輸入框的日期時間字串。
            field_name (str): 欄位名稱 ("start_time" 或 "end_time")，用於設定對應的錯誤訊息。

        Returns:
            Optional[datetime]: 若解析成功，則回傳轉換後的 UTC `datetime` 物件；
                                若輸入為空或格式錯誤，則回傳 `None` 並設定相應的錯誤訊息。
        """
        error_message_var_name = f"{field_name}_error_message" # 動態取得錯誤訊息變數名稱

        if not datetime_str:
            setattr(self, error_message_var_name, "") # 輸入為空時，清除該欄位的錯誤訊息
            return None
        try:
            # HTML datetime-local input format is 'YYYY-MM-DDTHH:MM'
            naive_dt_obj = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")
            
            # 假設使用者輸入的是本地時間 (台北時間 UTC+8)
            taipei_tz = timezone(timedelta(hours=8))
            aware_taipei_dt = naive_dt_obj.replace(tzinfo=taipei_tz)
            
            # 將本地時間轉換為 UTC 時間儲存
            utc_dt_obj = aware_taipei_dt.astimezone(timezone.utc)
            
            setattr(self, error_message_var_name, "") # 解析成功，清除錯誤訊息
            return utc_dt_obj
        except ValueError:
            setattr(self, error_message_var_name, "日期時間格式錯誤，應為 YYYY-MM-DDTHH:MM")
            return None

    async def handle_set_new_academic_year(self):
        """處理「確認設定」按鈕點擊事件，以設定新的學年度與登記時間。

        此方法會執行以下操作：
        1. 驗證新學年度字串的格式。
        2. 解析並驗證登記開始時間和結束時間的格式及邏輯（結束時間需晚於開始時間）。
        3. 檢查新設定是否與當前設定完全相同，若相同則提示無需變更。
        4. 若所有驗證通過，則呼叫 `AcademicYearSetting.set_current` 方法更新資料庫。
        5. 更新成功後，清空輸入欄位、重設驗證錯誤訊息，並重新載入頁面資料。
        """
        year_to_set = self.new_academic_year_input.strip()
        
        # 步驟 1: 驗證學年度格式
        if not self._validate_academic_year_format(year_to_set):
            return rx.toast.error(self.year_input_error_message or "學年度格式不正確。") # type: ignore

        # 步驟 2: 解析並驗證登記開始與結束時間
        reg_start_dt_utc = self._parse_datetime_input(self.new_reg_start_time_input, "start_time")
        if self.new_reg_start_time_input and reg_start_dt_utc is None: # 使用者輸入了但格式錯誤
            return rx.toast.error(self.start_time_error_message or "開始時間格式錯誤。") # type: ignore
        
        reg_end_dt_utc = self._parse_datetime_input(self.new_reg_end_time_input, "end_time")
        if self.new_reg_end_time_input and reg_end_dt_utc is None: # 使用者輸入了但格式錯誤
            return rx.toast.error(self.end_time_error_message or "結束時間格式錯誤。") # type: ignore

        # 步驟 3: 檢查結束時間是否晚於開始時間 (如果兩者都提供了)
        if reg_start_dt_utc and reg_end_dt_utc and reg_end_dt_utc <= reg_start_dt_utc:
            self.end_time_error_message = "結束時間必須晚於開始時間。"
            return rx.toast.error(self.end_time_error_message) # type: ignore
        else:
            # 如果之前有此錯誤，但現在已修正 (例如，其中一個時間被清空或順序正確)，則清除錯誤訊息
            if self.end_time_error_message == "結束時間必須晚於開始時間。":
                self.end_time_error_message = ""

        # 步驟 4: 檢查是否與當前設定相同 (避免不必要的更新)
        if self.current_setting_display:
            if year_to_set == self.current_setting_display.academic_year and \
               reg_start_dt_utc == self.current_setting_display.registration_start_time and \
               reg_end_dt_utc == self.current_setting_display.registration_end_time:
                return rx.toast.info("新設定與目前生效的設定完全相同，無需變更。") # type: ignore

        # 步驟 5: 執行設定
        current_user_email = self.tokeninfo.get("email") if self.token_is_valid else "系統（未知使用者）"
        
        try:
            await AcademicYearSetting.set_current(
                academic_year=year_to_set,
                registration_start=reg_start_dt_utc,
                registration_end=reg_end_dt_utc,
                user_email=current_user_email
            )
            
            # 操作成功後，清空輸入欄位並重設驗證錯誤訊息
            self.new_academic_year_input = ""
            self.new_reg_start_time_input = ""
            self.new_reg_end_time_input = ""
            self.year_input_error_message = ""
            self.start_time_error_message = ""
            self.end_time_error_message = ""
            
            await self.load_current_and_history() # 重新載入頁面資料以顯示更新
            return rx.toast.success(f"學年度已成功設定為：{year_to_set}") # type: ignore
        except Exception as e:
            # 應記錄更詳細的錯誤日誌
            # await SystemLog.log(LogLevel.ERROR, f"設定學年度失敗: {e}", source="ManagerAcademicYearState", user_email=current_user_email)
            return rx.toast.error(f"設定學年度時發生錯誤：{str(e)}") # type: ignore
