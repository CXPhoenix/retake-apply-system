import reflex as rx
from reflex_google_auth import require_google_login
from ..states.auth import AuthState, authorize_by_groups
from ..models.users import UserGroup
from ..models.academic_year_setting import AcademicYearSetting
from ..components import navbar

# TODO: 建立 ManagerAcademicYearState，繼承 AuthState。
#       應包含：
#       - current_system_academic_year: rx.Var[str] (當前生效的學年度)
#       - academic_year_history: rx.Var[list[AcademicYearSetting]] (歷史設定記錄)
#       - new_academic_year_input: rx.Var[str] (用於綁定輸入框)
#       - async def load_current_and_history(self):
#       - async def handle_set_new_academic_year(self):

# class ManagerAcademicYearState(AuthState):
#     current_system_academic_year: rx.Var[str] = "未設定"
#     academic_year_history: rx.Var[list[AcademicYearSetting]] = []
#     new_academic_year_input: rx.Var[str] = ""
#
#     async def on_load(self): # 或 on_page_load
#         # 載入當前學年度和歷史記錄
#         # latest_setting = await AcademicYearSetting.find_one(sort=[("set_at", -1)])
#         # if latest_setting:
#         #     self.current_system_academic_year = latest_setting.academic_year
#         # self.academic_year_history = await AcademicYearSetting.find_all(sort=[("set_at", -1)]).to_list()
#         print("TODO: ManagerAcademicYearState.on_load 載入學年度資料")
#
#     async def handle_set_new_year(self):
#         # year_to_set = self.new_academic_year_input.strip()
#         # if not year_to_set: # TODO: 加入更嚴謹的格式驗證 (e.g., "113-1")
#         #     return rx.window_alert("學年度格式不正確。")
#         #
#         # # TODO: 獲取當前登入使用者資訊以記錄 set_by
#         # # current_user_email = self.tokeninfo.get("email") if self.token_is_valid else "系統"
#         #
#         # new_setting = AcademicYearSetting(
#         #     academic_year=year_to_set,
#         #     set_by=current_user_email 
#         # )
#         # await new_setting.insert()
#         # self.new_academic_year_input = "" # 清空輸入框
#         # await self.on_load() # 重新載入
#         # return rx.window_alert(f"學年度已設定為：{year_to_set}")
#         print(f"TODO: ManagerAcademicYearState.handle_set_new_year 設定學年度: {self.new_academic_year_input}")


@rx.page(route="/manager-academic-year", title="學年度管理") # 路由根據 dashboard.py 中的連結調整
@require_google_login
# @authorize_by_groups(required_groups=[UserGroup.COURSE_MANAGER]) # 改由 State 控制權限
def manager_academic_year() -> rx.Component:
    """
    課程管理者頁面，用於設定與調整系統運作的學年度。
    TODO: 此頁面應綁定到 ManagerAcademicYearState。
    """
    return rx.vstack(
        navbar(),
        rx.heading("學年度設定", size="lg", margin_bottom="1em"),
        rx.text("（TODO: 此頁面應綁定到 ManagerAcademicYearState）"),
        rx.text("設定系統目前運作的學年度，影響選課與開課操作。"),
        rx.box(
            rx.text("目前學年度："),
            # rx.text(ManagerAcademicYearState.current_system_academic_year, font_weight="bold"),
            rx.text("（TODO: 顯示 ManagerAcademicYearState.current_system_academic_year）", font_weight="bold"),
            border="1px solid #ddd",
            padding="1em",
            margin="1em 0",
            border_radius="5px",
        ),
        rx.hstack(
            # rx.input(
            #     placeholder="輸入學年度 (例如：113-1)",
            #     value=ManagerAcademicYearState.new_academic_year_input,
            #     on_change=ManagerAcademicYearState.set_new_academic_year_input
            # ),
            # rx.button("設定新學年度", on_click=ManagerAcademicYearState.handle_set_new_year),
            rx.input(placeholder="輸入學年度 (例如：113-1) (TODO)"),
            rx.button("設定新學年度 (TODO)"),
            spacing="1em",
            margin_bottom="1em"
        ),
        rx.heading("學年度設定歷史記錄", size="md", margin_top="1.5em"),
        # rx.foreach(
        #     ManagerAcademicYearState.academic_year_history,
        #     lambda setting: rx.box(
        #         rx.text(f"學年度：{setting.academic_year}"),
        #         rx.text(f"設定時間：{setting.set_at.strftime('%Y-%m-%d %H:%M:%S') if setting.set_at else 'N/A'}"),
        #         rx.text(f"設定者：{setting.set_by or '未知'}"),
        #         border="1px solid #eee", padding="0.5em", margin="0.3em 0", border_radius="3px",
        #     )
        # ),
        rx.text("（TODO: 顯示 ManagerAcademicYearState.academic_year_history 列表）"),
        align_items="center",
        padding="2em",
        # on_mount=ManagerAcademicYearState.on_load # 頁面載入時觸發
    )

# 以下 TODO 函式應移至 ManagerAcademicYearState 中
# TODO: get_current_academic_year() -> ManagerAcademicYearState.current_system_academic_year (由 on_load 更新)
# TODO: set_new_academic_year() -> ManagerAcademicYearState.handle_set_new_year (處理輸入框綁定與提交)
