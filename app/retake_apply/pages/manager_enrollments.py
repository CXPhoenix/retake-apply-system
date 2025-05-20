import reflex as rx
from reflex_google_auth import require_google_login
from ..states.auth import AuthState, authorize_by_groups
from ..models.users import UserGroup
from ..models.enrollment import Enrollment
from ..models.course import Course
from ..models.users import User
from ..components import navbar

# TODO: 建立 ManagerEnrollmentsState，繼承 AuthState。
#       應包含：
#       - enrollments_list: rx.Var[list[Enrollment]]
#       - search_term: rx.Var[str]
#       - selected_academic_year: rx.Var[str] (用於篩選)
#       - academic_year_options: rx.Var[list[str]] (動態載入)
#       - show_manual_enroll_modal: rx.Var[bool]
#       - manual_enroll_form_data: rx.Var[dict] (學號/Email, 課程ID)
#       - async def load_enrollments(self):
#       - async def handle_csv_download(self):
#       - async def handle_manual_enroll(self, form_data: dict): (現場報名)

# class ManagerEnrollmentsState(AuthState):
#     enrollments_list: rx.Var[list[Enrollment]] = []
#     search_term: rx.Var[str] = ""
#     selected_academic_year: rx.Var[str] = "ALL" # "ALL" 代表全部學年度
#     academic_year_options: rx.Var[list[str]] = ["ALL"] # 預設包含 "全部學年度"
#     # ... 其他 rx.Var 和事件處理器 ...
#
#     async def on_load(self):
#         # 載入學年度選項
#         # settings = await AcademicYearSetting.find_all(sort=[("academic_year", -1)]).to_list()
#         # self.academic_year_options = ["ALL"] + [s.academic_year for s in settings]
#         # await self.load_enrollments_data()
#         print("TODO: ManagerEnrollmentsState.on_load 載入學年度選項及報名資料")
#
#     async def load_enrollments_data(self):
#         # query = {}
#         # if self.selected_academic_year != "ALL":
#         #     query["academic_year"] = self.selected_academic_year
#         # if self.search_term:
#         #     # TODO: 構建複雜搜尋邏輯 (學生姓名/學號, 課程名稱/代碼)
#         #     pass
#         # self.enrollments_list = await Enrollment.find(query, fetch_links=True).to_list() # fetch_links for User and Course
#         print(f"TODO: ManagerEnrollmentsState.load_enrollments_data 載入報名資料 (學年: {self.selected_academic_year}, 搜尋: {self.search_term})")
#
#     async def handle_csv_export(self):
#         # TODO: 根據目前篩選條件 (self.enrollments_list) 產生 CSV 內容
#         #       需符合規格 6.3 (學生報名資料匯出格式)
#         #       使用 rx.download(data=..., filename="報名資料.csv")
#         # csv_data = "報名日期,學號,學生姓名,選課序號,科目代碼,科目名稱,學分數,費用\n" # Header
#         # for enroll in self.enrollments_list:
#         #     # 提取並格式化資料...
#         #     # user = enroll.user_id
#         #     # course = enroll.course_id
#         #     # csv_data += f"{enroll.enrolled_at.strftime('%Y/%m/%d')},{user.student_id if user else ''},...\n"
#         # return rx.download(data=csv_data, filename="報名資料.csv")
#         print("TODO: ManagerEnrollmentsState.handle_csv_export 匯出 CSV")
#
#     # TODO: 現場報名相關的 Modal 控制與事件處理器

@rx.page(route="/manager-enrollments", title="報名管理") # 路由根據 dashboard.py 中的連結調整
@require_google_login
# @authorize_by_groups(required_groups=[UserGroup.COURSE_MANAGER]) # 改由 State 控制權限
def manager_enrollments() -> rx.Component:
    """
    課程管理者頁面，用於檢視與下載學生報名資料。
    TODO: 此頁面應綁定到 ManagerEnrollmentsState。
    """
    # TODO: 實現現場報名 Modal (規格 3.4)
    #       表單應包含：學生識別 (學號/Email)、課程選擇 (可搜尋)
    #       提交後執行選課邏輯 (含衝堂檢查)，並可選擇是否立即產生繳費資訊 (規格 5.1)

    return rx.vstack(
        navbar(),
        rx.heading("學生報名資料管理", size="lg", margin_bottom="1em"),
        rx.text("（TODO: 此頁面應綁定到 ManagerEnrollmentsState）"),
        rx.hstack(
            # rx.input(placeholder="搜尋學生或課程...", value=ManagerEnrollmentsState.search_term, on_change=ManagerEnrollmentsState.set_search_term),
            # rx.select(
            #     ManagerEnrollmentsState.academic_year_options,
            #     value=ManagerEnrollmentsState.selected_academic_year,
            #     placeholder="選擇學年度",
            #     on_change=ManagerEnrollmentsState.set_selected_academic_year
            # ),
            # rx.button("查詢", on_click=ManagerEnrollmentsState.load_enrollments_data),
            # rx.button("下載 CSV", on_click=ManagerEnrollmentsState.handle_csv_export),
            # rx.button("現場報名", on_click=ManagerEnrollmentsState.open_manual_enroll_modal),
            rx.input(placeholder="搜尋... (TODO)"),
            rx.select(["全部學年度", "113-1 (TODO)"], placeholder="選擇學年度 (TODO)"),
            rx.button("查詢 (TODO)"),
            rx.button("下載 CSV (TODO)"),
            rx.button("現場報名 (TODO)"),
            spacing="1em",
            margin_bottom="1em"
        ),
        # rx.foreach(
        #     ManagerEnrollmentsState.enrollments_list,
        #     lambda enrollment: rx.box(
        #         # 需確保 user_id 和 course_id 已 fetch_link
        #         rx.text(f"學生：{enrollment.user_id.fullname if enrollment.user_id else 'N/A'} ({enrollment.user_id.student_id if enrollment.user_id else 'N/A'})"),
        #         rx.text(f"課程：{enrollment.course_id.course_name if enrollment.course_id else 'N/A'} ({enrollment.course_id.course_code if enrollment.course_id else 'N/A'})"),
        #         # ... 其他欄位 ...
        #     )
        # ),
        rx.text("（TODO: 報名資料列表顯示區，應使用 rx.data_table 或 rx.foreach）"),
        
        # TODO: 現場報名 Modal

        align_items="center",
        padding="2em",
        # on_mount=ManagerEnrollmentsState.on_load
    )

# 以下 TODO 函式應移至 ManagerEnrollmentsState 中
# TODO: filter_enrollments(value) -> ManagerEnrollmentsState.set_search_term(value)
# TODO: filter_by_academic_year(value) -> ManagerEnrollmentsState.set_selected_academic_year(value)
# TODO: download_enrollments_csv() -> ManagerEnrollmentsState.handle_csv_export()
