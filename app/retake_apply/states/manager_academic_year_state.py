import reflex as rx
from typing import List, Optional
import re # 用於學年度格式驗證
from datetime import datetime, timezone, timedelta # 新增 timezone, timedelta

from .auth import AuthState
from ..models.users import UserGroup
from ..models.academic_year_setting import AcademicYearSetting
from ..utils.funcs import format_datetime_to_taipei_str # 匯入時間格式化函式

class ManagerAcademicYearState(AuthState):
    """管理學年度設定頁面的狀態與邏輯"""

    current_setting_display: rx.Var[Optional[AcademicYearSetting]] = None # 儲存當前 AcademicYearSetting 物件
    academic_year_history: rx.Var[List[AcademicYearSetting]] = rx.Var([])
    
    # 新學年度設定的輸入綁定
    new_academic_year_input: rx.Var[str] = ""
    new_reg_start_time_input: rx.Var[str] = "" # 格式 YYYY-MM-DDTHH:MM
    new_reg_end_time_input: rx.Var[str] = ""   # 格式 YYYY-MM-DDTHH:MM

    # 格式驗證相關
    year_input_error_message: rx.Var[str] = ""
    start_time_error_message: rx.Var[str] = ""
    end_time_error_message: rx.Var[str] = ""

    @rx.var
    def current_academic_year_str(self) -> str:
        """顯示用的當前學年度字串"""
        if self.current_setting_display:
            return self.current_setting_display.academic_year
        return "尚未設定"

    @rx.var
    def current_reg_start_time_str(self) -> str:
        """顯示用的當前登記開始時間字串"""
        if self.current_setting_display and self.current_setting_display.registration_start_time:
            # 假設 registration_start_time 在資料庫中是 UTC (修正後會是)
            return format_datetime_to_taipei_str(self.current_setting_display.registration_start_time, "%Y-%m-%d %H:%M")
        return "未設定"

    @rx.var
    def current_reg_end_time_str(self) -> str:
        """顯示用的當前登記結束時間字串"""
        if self.current_setting_display and self.current_setting_display.registration_end_time:
            # 假設 registration_end_time 在資料庫中是 UTC (修正後會是)
            return format_datetime_to_taipei_str(self.current_setting_display.registration_end_time, "%Y-%m-%d %H:%M")
        return "未設定"

    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            # 如果需要強制登入才能看到此頁面，應由 require_google_login 和 require_group 處理
            # 此處僅為初步檢查
            return
        
        # 權限檢查
        if not self.is_member_of_any([UserGroup.COURSE_MANAGER, UserGroup.ADMIN]):
             # 如果不是課程管理者或系統管理員，則重導向
            return rx.redirect(self.DEFAULT_UNAUTHORIZED_REDIRECT_PATH) # type: ignore
        
        await self.load_current_and_history()

    async def load_current_and_history(self):
        """載入當前學年度和歷史設定記錄"""
        self.current_setting_display = await AcademicYearSetting.get_current()
        self.academic_year_history = await AcademicYearSetting.find_all(sort=[("set_at", -1)]).to_list()
        # print(f"學年度資料已載入 - 當前: {self.current_setting_display.academic_year if self.current_setting_display else '無'}, 歷史數量: {len(self.academic_year_history)}")

    def _validate_academic_year_format(self, year_string: str) -> bool:
        """私有方法：驗證學年度輸入格式"""
        pattern = r"^\d{3}-(1|2)$" # 例如 113-1, 114-2
        if not year_string:
            self.year_input_error_message = "學年度不可為空。"
            return False
        if re.match(pattern, year_string):
            self.year_input_error_message = ""
            return True
        else:
            self.year_input_error_message = "格式錯誤，應為 XXX-1 或 XXX-2 (例如 113-1)"
            return False

    def _parse_datetime_input(self, datetime_str: str, field_name: str) -> Optional[datetime]:
        """私有方法：解析日期時間字串"""
        if not datetime_str:
            if field_name == "start_time":
                self.start_time_error_message = "" # 允許為空
            elif field_name == "end_time":
                self.end_time_error_message = "" # 允許為空
            return None
        try:
            # HTML datetime-local input format is 'YYYY-MM-DDTHH:MM'
            naive_dt_obj = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")
            
            # 假設 naive_dt_obj 代表台北時間 (UTC+8)
            taipei_tz = timezone(timedelta(hours=8))
            aware_taipei_dt = naive_dt_obj.replace(tzinfo=taipei_tz)
            
            # 轉換為 UTC 時間
            utc_dt_obj = aware_taipei_dt.astimezone(timezone.utc)
            
            if field_name == "start_time":
                self.start_time_error_message = ""
            elif field_name == "end_time":
                self.end_time_error_message = ""
            return utc_dt_obj
        except ValueError:
            error_msg = "日期時間格式錯誤，應為 YYYY-MM-DDTHH:MM"
            if field_name == "start_time":
                self.start_time_error_message = error_msg
            elif field_name == "end_time":
                self.end_time_error_message = error_msg
            return None

    async def handle_set_new_academic_year(self):
        """處理設定新學年度的邏輯"""
        year_to_set = self.new_academic_year_input.strip()
        
        # 驗證學年度格式
        if not self._validate_academic_year_format(year_to_set):
            return rx.toast.error(self.year_input_error_message) # type: ignore

        # 解析登記開始與結束時間
        reg_start_dt = self._parse_datetime_input(self.new_reg_start_time_input, "start_time")
        if self.new_reg_start_time_input and reg_start_dt is None: # 輸入了但格式錯誤
            return rx.toast.error(self.start_time_error_message) # type: ignore
        
        reg_end_dt = self._parse_datetime_input(self.new_reg_end_time_input, "end_time")
        if self.new_reg_end_time_input and reg_end_dt is None: # 輸入了但格式錯誤
            return rx.toast.error(self.end_time_error_message) # type: ignore

        # 檢查結束時間是否晚於開始時間 (如果兩者都提供了)
        if reg_start_dt and reg_end_dt and reg_end_dt <= reg_start_dt:
            self.end_time_error_message = "結束時間必須晚於開始時間。"
            return rx.toast.error(self.end_time_error_message) # type: ignore
        else:
             # 如果之前有此錯誤，但現在已修正或其中一個為空，則清除錯誤
            if self.end_time_error_message == "結束時間必須晚於開始時間。":
                self.end_time_error_message = ""


        # 檢查是否與當前學年度及設定相同 (如果當前設定存在)
        if self.current_setting_display:
            if year_to_set == self.current_setting_display.academic_year and \
               reg_start_dt == self.current_setting_display.registration_start_time and \
               reg_end_dt == self.current_setting_display.registration_end_time:
                return rx.toast.info("新設定與目前設定相同，無需變更。") # type: ignore

        current_user_email = self.tokeninfo.get("email") if self.token_is_valid else "系統（未知使用者）"
        
        try:
            await AcademicYearSetting.set_current(
                academic_year=year_to_set,
                registration_start=reg_start_dt,
                registration_end=reg_end_dt,
                user_email=current_user_email
            )
            
            # 清空輸入框
            self.new_academic_year_input = ""
            self.new_reg_start_time_input = ""
            self.new_reg_end_time_input = ""
            # 重設驗證狀態
            self.year_input_error_message = ""
            self.start_time_error_message = ""
            self.end_time_error_message = ""
            
            await self.load_current_and_history() # 重新載入資料
            return rx.toast.success(f"學年度已成功設定為：{year_to_set}") # type: ignore
        except Exception as e:
            # print(f"設定學年度失敗：{e}") # 開發時調試用
            return rx.toast.error(f"設定學年度失敗：{str(e)}") # type: ignore
