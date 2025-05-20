import reflex as rx
from reflex_google_auth import require_google_login
from ..states.auth import AuthState, authorize_by_groups
from ..models.users import UserGroup
from ..models.course import Course
from ..components import navbar

# TODO: 建立 ManagerCoursesState，繼承 AuthState，用於管理此頁面的所有邏輯。
#       應包含：
#       - courses_list: rx.Var[list[Course]] (顯示的課程列表)
#       - search_term: rx.Var[str]
#       - show_add_modal: rx.Var[bool]
#       - show_edit_modal: rx.Var[bool]
#       - current_course_for_edit: rx.Var[Course] (或其 ID)
#       - add_course_form_data: rx.Var[dict] (用於綁定新增表單)
#       - edit_course_form_data: rx.Var[dict] (用於綁定編輯表單)
#       - async def load_courses(self): (載入/篩選課程)
#       - async def handle_add_course(self, form_data: dict):
#       - async def handle_edit_course(self, course_id: str, form_data: dict):
#       - async def handle_delete_course(self, course_id: str):
#       - async def handle_csv_upload(self, file: rx.UploadFile):
#       - 事件處理器來控制 modal 的顯示/隱藏

# class ManagerCoursesState(AuthState):
    # courses_list: rx.Var[list[Course]] = []
    # search_term: rx.Var[str] = ""
    # show_add_modal: rx.Var[bool] = False
    # # ... 其他 rx.Var 和事件處理器 ...
    #
    # @rx.background
    # async def initial_load(self):
    #     async with self:
    #         # self.courses_list = await Course.find_all().to_list() # 範例
    #         print("TODO: ManagerCoursesState.initial_load 載入課程")
    #
    # async def handle_delete_course_confirmed(self, course_id_str: str):
    #     # obj_id = PydanticObjectId(course_id_str)
    #     # course_to_delete = await Course.get(obj_id)
    #     # if course_to_delete:
    #     #     # TODO: 檢查是否有相關選課記錄 (Enrollment)
    #     #     # enrollments_exist = await Enrollment.find(Enrollment.course_id == obj_id).count() > 0
    #     #     # if enrollments_exist:
    #     #     #     return rx.window_alert("無法刪除：此課程已有學生選課記錄。")
    #     #     await course_to_delete.delete()
    #     #     await self.load_courses() # 重新載入列表
    #     #     return rx.window_alert("課程已刪除。")
    #     # return rx.window_alert("找不到要刪除的課程。")
    #     print(f"TODO: ManagerCoursesState.handle_delete_course_confirmed for {course_id_str}")
    #
    # def confirm_delete_course(self, course_id: str):
    #     return rx.window_confirm(
    #         f"確定要刪除課程 (ID: {course_id}) 嗎？此操作無法復原。",
    #         on_yes=ManagerCoursesState.handle_delete_course_confirmed(course_id),
    #     )
    #
    # # TODO: 實作其他 CRUD 和 CSV 上傳的事件處理器

@rx.page(route="/manager-courses", title="課程管理") # 路由根據 dashboard.py 中的連結調整
@require_google_login
# @authorize_by_groups(required_groups=[UserGroup.COURSE_MANAGER]) # 改由 State 控制權限
def manager_courses() -> rx.Component:
    """
    課程管理者頁面，用於管理重補修課程，包括新增、修改、刪除與查詢課程。
    TODO: 此頁面應綁定到 ManagerCoursesState。
    """
    # TODO: 根據 ManagerCoursesState 實現新增/編輯課程的 Modal (rx.modal)
    #       Modal 中應包含表單，表單欄位需對應 Course 模型。
    #       CourseTimeSlot 也需要能在表單中動態增刪。

    # TODO: 實現 CSV 上傳課程的 UI (rx.upload) 並綁定到 State 的事件處理器。
    #       規格 3.1: 批次匯入：支援透過 CSV 檔案格式批次上傳多筆開課課程資料。
    #       規格 6.1: 開課課程資料批次匯入格式。

    return rx.vstack(
        navbar(),
        rx.heading("重補修課程管理", size="lg", margin_bottom="1em"),
        rx.text("（TODO: 此頁面應綁定到 ManagerCoursesState）"),
        rx.hstack(
            # rx.button("新增課程", on_click=ManagerCoursesState.set_show_add_modal(True)),
            # rx.input(placeholder="搜尋課程...", on_change=ManagerCoursesState.set_search_term),
            rx.button("新增課程 (TODO)"),
            rx.button("上傳 CSV (TODO)"), # CSV 上傳按鈕
            rx.input(placeholder="搜尋課程... (TODO)"),
            spacing="1em",
            margin_bottom="1em"
        ),
        # rx.foreach(
        #     ManagerCoursesState.courses_list, # 綁定到 State
        #     lambda course: rx.box(
        #         rx.text(f"課程名稱：{course.course_name}"),
        #         rx.text(f"科目代碼：{course.course_code}"),
        #         rx.text(f"學年度：{course.academic_year}"),
        #         # ... 其他欄位 ...
        #         rx.hstack(
        #             # rx.button("修改", on_click=lambda: ManagerCoursesState.start_edit_course(course)),
        #             # rx.button("刪除", on_click=ManagerCoursesState.confirm_delete_course(str(course.id)), color_scheme="red"),
        #             rx.button("修改 (TODO)"),
        #             rx.button("刪除 (TODO)", color_scheme="red"),
        #             spacing="0.5em"
        #         ),
        #         # ...
        #     )
        # ),
        rx.text("（TODO: 課程列表顯示區，應使用 rx.data_table 或 rx.foreach 綁定 ManagerCoursesState.courses_list）"),
        
        # TODO: 新增課程 Modal
        # rx.modal(
        #     rx.modal_overlay(
        #         rx.modal_content(
        #             rx.modal_header("新增課程"),
        #             rx.modal_body(
        #                 # TODO: 新增課程表單
        #                 rx.text("表單內容待實作")
        #             ),
        #             rx.modal_footer(
        #                 rx.button("取消", on_click=ManagerCoursesState.set_show_add_modal(False)),
        #                 rx.button("儲存", on_click=ManagerCoursesState.handle_add_new_course),
        #             ),
        #         )
        #     ),
        #     is_open=ManagerCoursesState.show_add_modal,
        # ),

        # TODO: 修改課程 Modal (類似新增)

        align_items="center",
        padding="2em",
        # on_mount=ManagerCoursesState.initial_load # 頁面載入時觸發
    )

# 以下 TODO 函式應移至 ManagerCoursesState 中作為事件處理器或輔助方法
# TODO: show_add_course_form() -> ManagerCoursesState.set_show_add_modal(True)
# TODO: filter_courses(value) -> ManagerCoursesState.set_search_term(value) and call load_courses
# TODO: show_edit_course_form(course_id) -> ManagerCoursesState.start_edit_course(course_id)
# TODO: delete_course(course_id) -> ManagerCoursesState.confirm_delete_course(course_id)
