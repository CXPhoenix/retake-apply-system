import reflex as rx
from reflex_google_auth import require_google_login
from ..states.auth import AuthState, authorize_by_groups
from ..models.users import UserGroup, User
from ..models.required_course import RequiredCourse
from ..components import navbar

# TODO: 建立 ManagerStudentsState，繼承 AuthState，用於管理此頁面的所有邏輯。
#       應包含：
#       - required_courses_list: rx.Var[list[RequiredCourse]] (顯示的列表)
#       - search_term: rx.Var[str]
#       - show_add_modal: rx.Var[bool]
#       - show_edit_modal: rx.Var[bool]
#       - current_record_for_edit: rx.Var[RequiredCourse] (或其 ID)
#       - add_form_data: rx.Var[dict] (用於綁定新增表單)
#       - edit_form_data: rx.Var[dict] (用於綁定編輯表單)
#       - async def load_records(self): (載入/篩選記錄)
#       - async def handle_add_record(self, form_data: dict):
#       - async def handle_edit_record(self, record_id: str, form_data: dict):
#       - async def handle_delete_record(self, record_id: str):
#       - async def handle_csv_upload(self, file: rx.UploadFile):

# class ManagerStudentsState(AuthState):
    # required_courses_list: rx.Var[list[RequiredCourse]] = []
    # # ... 其他 rx.Var 和事件處理器 ...
    #
    # @rx.background
    # async def initial_load(self):
    #     async with self:
    #         # self.required_courses_list = await RequiredCourse.find_all(fetch_links=True).to_list() # fetch_links 以取得 User 資訊
    #         print("TODO: ManagerStudentsState.initial_load 載入學生應重補修名單")
    #
    # async def handle_delete_record_confirmed(self, record_id_str: str):
    #     # obj_id = PydanticObjectId(record_id_str)
    #     # record_to_delete = await RequiredCourse.get(obj_id)
    #     # if record_to_delete:
    #     #     await record_to_delete.delete()
    #     #     await self.load_records() # 重新載入列表
    #     #     return rx.window_alert("記錄已刪除。")
    #     # return rx.window_alert("找不到要刪除的記錄。")
    #     print(f"TODO: ManagerStudentsState.handle_delete_record_confirmed for {record_id_str}")
    #
    # def confirm_delete_record(self, record_id: str):
    #     return rx.window_confirm(
    #         f"確定要刪除此筆應重補修記錄 (ID: {record_id}) 嗎？",
    #         on_yes=ManagerStudentsState.handle_delete_record_confirmed(record_id),
    #     )
    #
    # # TODO: 實作其他 CRUD 和 CSV 上傳的事件處理器 (需處理 User 關聯)

@rx.page(route="/manager-students", title="學生名單管理") # 路由根據 dashboard.py 中的連結調整
@require_google_login
# @authorize_by_groups(required_groups=[UserGroup.COURSE_MANAGER]) # 改由 State 控制權限
def manager_students() -> rx.Component:
    """
    課程管理者頁面，用於管理學生應重補修名單，包括新增、修改、刪除與查詢學生名單。
    TODO: 此頁面應綁定到 ManagerStudentsState。
    """
    # TODO: 根據 ManagerStudentsState 實現新增/編輯記錄的 Modal (rx.modal)
    #       Modal 中應包含表單，表單欄位需對應 RequiredCourse 模型。
    #       需要一個方式來查找並關聯 User (例如透過學號或 Email)。

    # TODO: 實現 CSV 上傳學生應重補修名單的 UI (rx.upload) 並綁定到 State 的事件處理器。
    #       規格 3.2: 批次匯入：支援透過 CSV 檔案格式批次上傳多筆學生應重補修名單。
    #       規格 6.2: 學生應重補修名單批次匯入格式 (包含學生GoogleEmail)。

    return rx.vstack(
        navbar(),
        rx.heading("學生應重補修名單管理", size="lg", margin_bottom="1em"),
        rx.text("（TODO: 此頁面應綁定到 ManagerStudentsState）"),
        rx.hstack(
            # rx.button("新增記錄", on_click=ManagerStudentsState.set_show_add_modal(True)),
            # rx.input(placeholder="搜尋學生、學號、科目...", on_change=ManagerStudentsState.set_search_term),
            rx.button("新增記錄 (TODO)"),
            rx.button("上傳 CSV (TODO)"), # CSV 上傳按鈕
            rx.input(placeholder="搜尋... (TODO)"),
            spacing="1em",
            margin_bottom="1em"
        ),
        # rx.foreach(
        #     ManagerStudentsState.required_courses_list, # 綁定到 State
        #     lambda req_course: rx.box(
        #         # 需確保 req_course.user_id 已 fetch_link
        #         rx.text(f"學生：{req_course.user_id.fullname if req_course.user_id else '未關聯'} ({req_course.user_id.student_id if req_course.user_id else 'N/A'})"),
        #         rx.text(f"科目：{req_course.course_name} ({req_course.course_code})"),
        #         # ... 其他欄位 ...
        #         rx.hstack(
        #             # rx.button("修改", on_click=lambda: ManagerStudentsState.start_edit_record(req_course)),
        #             # rx.button("刪除", on_click=ManagerStudentsState.confirm_delete_record(str(req_course.id)), color_scheme="red"),
        #             rx.button("修改 (TODO)"),
        #             rx.button("刪除 (TODO)", color_scheme="red"),
        #             spacing="0.5em"
        #         ),
        #         # ...
        #     )
        # ),
        rx.text("（TODO: 學生應重補修列表顯示區，應使用 rx.data_table 或 rx.foreach）"),
        
        # TODO: 新增/修改記錄的 Modal

        align_items="center",
        padding="2em",
        # on_mount=ManagerStudentsState.initial_load # 頁面載入時觸發
    )

# 以下 TODO 函式應移至 ManagerStudentsState 中
# TODO: show_add_student_course_form() -> ManagerStudentsState.set_show_add_modal(True)
# TODO: filter_student_courses(value) -> ManagerStudentsState.set_search_term(value) and call load_records
# TODO: show_edit_student_course_form(record_id) -> ManagerStudentsState.start_edit_record(record_id)
# TODO: delete_student_course(record_id) -> ManagerStudentsState.confirm_delete_record(record_id)
