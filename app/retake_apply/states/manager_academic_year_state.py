import reflex as rx
from typing import List, Optional
import re # 用於學年度格式驗證

from .auth import AuthState
from ..models.users import UserGroup
from ..models.academic_year_setting import AcademicYearSetting
from ..utils.funcs import get_now # 假設 get_now 已存在

class ManagerAcademicYearState(AuthState):
    """管理學年度設定頁面的狀態與邏輯"""

    current_system_academic_year: rx.Var[str] = "未設定"
    academic_year_history: rx.Var[List[AcademicYearSetting]] = rx.Var([])
    new_academic_year_input: rx.Var[str] = ""

    # 格式驗證相關
    is_input_valid: rx.Var[bool] = True
    input_error_message: rx.Var[str] = ""

    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            return
        if UserGroup.COURSE_MANAGER not in self.current_user_groups:
            # return rx.redirect("/unauthorized")
            pass
        await self.load_current_and_history()

    async def load_current_and_history(self):
        """載入當前學年度和歷史設定記錄"""
        # TODO: 應參考 AcademicYearSetting 模型中的 TODO: 實現獲取當前學年度的方法
        #       該方法應能處理多筆記錄時，返回最新的有效設定。
        latest_setting = await AcademicYearSetting.find_one(sort=[("set_at", -1)])
        if latest_setting:
            self.current_system_academic_year = latest_setting.academic_year
        else:
            self.current_system_academic_year = "尚未設定"
        
        self.academic_year_history = await AcademicYearSetting.find_all(sort=[("set_at", -1)]).to_list()
        print(f"TODO: ManagerAcademicYearState.load_current_and_history - 當前: {self.current_system_academic_year}, 歷史數量: {len(self.academic_year_history)}")

    def validate_academic_year_input(self, year_string: str) -> bool:
        """驗證學年度輸入格式，例如 '113-1' 或 '113-2'"""
        self.new_academic_year_input = year_string # 即時更新 Var
        pattern = r"^\d{3}-(1|2)$" # 例如 113-1, 114-2
        if not year_string:
            self.is_input_valid = True # 允許空輸入，提交時再檢查
            self.input_error_message = ""
            return True
        if re.match(pattern, year_string):
            self.is_input_valid = True
            self.input_error_message = ""
            return True
        else:
            self.is_input_valid = False
            self.input_error_message = "格式錯誤，應為 XXX-1 或 XXX-2 (例如 113-1)"
            return False

    async def handle_set_new_academic_year(self):
        """處理設定新學年度的邏輯"""
        year_to_set = self.new_academic_year_input.strip()
        
        if not self.validate_academic_year_input(year_to_set) or not year_to_set:
            # return rx.toast.error(self.input_error_message or "學年度不可為空。")
            print(f"學年度設定失敗: {self.input_error_message or '學年度不可為空。'}")
            return

        # 檢查是否與當前學年度相同
        if year_to_set == self.current_system_academic_year:
            # return rx.toast.info("新設定的學年度與目前學年度相同，無需變更。")
            print("新設定的學年度與目前學年度相同，無需變更。")
            return

        current_user_email = self.tokeninfo.get("email") if self.token_is_valid else "系統（未知使用者）"
        
        try:
            new_setting = AcademicYearSetting(
                academic_year=year_to_set,
                set_by=current_user_email,
                set_at=get_now() # 確保 set_at 被正確設定
            )
            await new_setting.insert()
            
            self.new_academic_year_input = "" # 清空輸入框
            self.is_input_valid = True # 重設驗證狀態
            self.input_error_message = ""
            await self.load_current_and_history() # 重新載入資料
            # return rx.toast.success(f"學年度已成功設定為：{year_to_set}")
            print(f"學年度已成功設定為：{year_to_set}")
        except Exception as e:
            # return rx.toast.error(f"設定學年度失敗：{e}")
            print(f"設定學年度失敗：{e}")
