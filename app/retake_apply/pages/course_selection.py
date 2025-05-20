import reflex as rx
from reflex_google_auth import require_google_login
from ..states.auth import AuthState, authorize_by_groups
from ..models.users import UserGroup
from ..models.course import Course
from ..components import navbar

# TODO: 建立 CourseSelectionState，繼承 AuthState，用於管理此頁面的所有邏輯。
#       規格文件：「業務邏輯封裝 (BUSINESS_LOGIC_ENCAPSULATION): 將相關的業務邏輯和資料庫操作封裝在 rx.State 的方法中。」
#       應包含以下 rx.Var 和事件處理器：
#       - available_courses: rx.Var[list[Course]] (用於顯示的課程列表)
#       - search_term: rx.Var[str] (搜尋關鍵字)
#       - async def load_available_courses(self): (載入或篩選課程，更新 available_courses)
#       - async def handle_select_course(self, course_id: str): (處理選課邏輯，包含衝堂檢查)
#       - (可選) current_academic_year: rx.Var[str] (從 AcademicYearSetting 載入)

# class CourseSelectionState(AuthState):
#     available_courses: rx.Var[list[Course]] = rx.Var([])
#     search_term: rx.Var[str] = ""
#     # TODO: (可選) current_academic_year: rx.Var[str]
#
#     async def on_load_courses(self): # 或 on_page_load
#         """載入當前學年度開放選課的課程"""
#         # TODO: 獲取當前學年度 (current_academic_year)
#         # courses = await Course.find(
#         #     Course.is_open_for_registration == True,
#         #     Course.academic_year == self.current_academic_year, # 篩選當前學年度
#         #     Course.course_name.ilike(f"%{self.search_term}%") if self.search_term else True
#         # ).to_list()
#         # self.available_courses = courses
#         rx.window_alert("TODO: CourseSelectionState.on_load_courses 尚未完整實作")
#
#     async def handle_search_term_change(self, term: str):
#         self.search_term = term
#         await self.on_load_courses() # 重新載入課程
#
#     async def handle_select_course(self, course_id_str: str):
#         """處理學生選課邏輯，包括衝堂檢查等"""
#         # from ..models.enrollment import Enrollment, EnrollmentStatus
#         # from ..models.users import User
#         # from ..utils.funcs import check_course_conflict # 假設此函式已根據規格文件 2.4 完整實作
#         # from beanie.odm.fields import PydanticObjectId
#
#         # if not self.token_is_valid or not self.current_user_google_id:
#         #     return rx.window_alert("請先登入。")
#
#         # current_user_db = await User.find_one(User.google_sub == self.current_user_google_id)
#         # if not current_user_db:
#         #     return rx.window_alert("無法找到您的使用者資訊，請重新登入。")
#
#         # try:
#         #     obj_course_id = PydanticObjectId(course_id_str)
#         # except Exception:
#         #     return rx.window_alert("無效的課程 ID。")
#
#         # selected_course = await Course.get(obj_course_id)
#         # if not selected_course:
#         #     return rx.window_alert("無法找到該課程，請重試。")
#
#         # if not selected_course.is_open_for_registration:
#         #     return rx.window_alert("該課程目前不開放選課。")
#
#         # # 獲取使用者已選課程 (僅限當前學年度成功或待處理的選課)
#         # existing_enrollments = await Enrollment.find(
#         #     Enrollment.user_id == current_user_db.id,
#         #     Enrollment.academic_year == selected_course.academic_year, # 確保是同學年度
#         #     Enrollment.status.in_([EnrollmentStatus.SUCCESS, EnrollmentStatus.PENDING]) # 只考慮有效選課
#         # ).project(Enrollment.course_id).to_list()
#
#         # enrolled_course_ids = [enroll.course_id.id for enroll in existing_enrollments if enroll.course_id]
#         # enrolled_courses_details = await Course.find(Course.id.in_(enrolled_course_ids)).to_list()
#
#         # # TODO: 仔細檢查 check_course_conflict 是否符合規格 2.4 的兩個定義
#         # # 1. 時間重疊
#         # # 2. 同課程不同時段 (若已選 A 課程的 X 時段，則 A 課程的 Y 時段也算衝堂)
#         # conflict_reason = check_course_conflict(selected_course, enrolled_courses_details, current_user_db.id) # 假設函式返回衝突原因字串或 None
#         # if conflict_reason:
#         #     return rx.window_alert(f"選課失敗：{conflict_reason}")
#
#         # # 檢查是否已選過此課程 (不同時段也算)
#         # for enrolled_c_id in enrolled_course_ids:
#         #    if selected_course.id == enrolled_c_id: # 這裡可能需要更細緻的比對，例如課程代碼
#         #        # 如果允許重選不同時段，則此檢查可能不需要或需調整
#         #        return rx.window_alert("您已選修過此課程或此課程的其他時段。")
#
#         # new_enrollment = Enrollment(
#         #     user_id=current_user_db.id, # type: ignore
#         #     course_id=selected_course.id, # type: ignore
#         #     academic_year=selected_course.academic_year,
#         #     status=EnrollmentStatus.SUCCESS # 或 PENDING，視流程而定
#         # )
#         # await new_enrollment.insert()
#         # await self.on_load_courses() # 重新載入課程列表 (可能某些課程因人數上限等不再顯示)
#         # return rx.window_alert("選課成功！")
#         rx.window_alert("TODO: CourseSelectionState.handle_select_course 尚未完整實作")


@rx.page(route="/course-selection", title="課程選擇")
@require_google_login
# @authorize_by_groups(required_groups=[UserGroup.STUDENT]) # 改由 CourseSelectionState.on_load 控制權限
def course_selection() -> rx.Component:
    """
    學生課程選擇頁面，顯示可選的重補修課程並允許學生進行選課。
    TODO: 此頁面應綁定到 CourseSelectionState。
    """
    # TODO: 移除 display_time_slots，將其邏輯整合到課程卡片元件中或 CourseSelectionState。
    def display_time_slots(time_slots):
        return rx.vstack(
            *[rx.text(f"星期 {slot.day_of_week}，節次 {slot.period} ({slot.start_time}-{slot.end_time})，地點：{slot.location or '未指定'}") for slot in time_slots],
            spacing="0.3em"
        )
    
    return rx.vstack(
        navbar(),
        rx.heading("重補修課程選擇", size="lg", margin_bottom="1em"),
        rx.text("（TODO: 此頁面應綁定到 CourseSelectionState）"),
        rx.text("（TODO: 應顯示當前學年度）"),
        rx.hstack(
            # TODO: rx.input 的 on_change 應綁定到 CourseSelectionState.handle_search_term_change
            #       或直接綁定 search_term: rx.Var[str] 並使用 debounce
            rx.input(placeholder="搜尋科目名稱...", on_change=lambda value: print(f"Search: {value}")), # Placeholder
            spacing="1em",
            margin_bottom="1em"
        ),
        # TODO: rx.foreach 應綁定到 CourseSelectionState.available_courses
        rx.foreach(
            # Course.find(Course.is_open_for_registration == True), # 應從 State 獲取
            [], # Placeholder for CourseSelectionState.available_courses
            lambda course: rx.box(
                rx.text(f"課程名稱：{course.course_name}"),
                rx.text(f"科目代碼：{course.course_code}"),
                rx.text(f"授課教師：{course.instructor_name or '未指定'}"),
                rx.text(f"上課時間："),
                # display_time_slots(course.time_slots), # 應在 State 或元件內部處理
                rx.text(f"學分數：{course.credits}"),
                rx.text(f"總費用：{course.total_fee}"), # 應確保 total_fee 已被計算
                # TODO: rx.button 的 on_click 應綁定到 CourseSelectionState.handle_select_course(course.id)
                rx.button("選課", on_click=lambda: print(f"Select course: {course.id}")), # Placeholder
                border="1px solid #ddd",
                padding="1em",
                margin="0.5em 0",
                border_radius="5px",
            )
        ),
        align_items="center",
        padding="2em",
        # on_mount=CourseSelectionState.on_load_courses # 頁面載入時觸發事件
    )

# TODO: 移除 filter_courses 函式，其邏輯應整合到 CourseSelectionState.on_load_courses。
# def filter_courses(search_term: str):
#     """根據搜尋詞過濾課程列表"""
#     if not search_term:
#         return Course.find(Course.is_open_for_registration == True)
#     search_term = search_term.lower()
#     return Course.find(
#         Course.is_open_for_registration == True,
#         Course.course_name.ilike(f"%{search_term}%")
#     )

# TODO: 移除 handle_course_selection 函式，其邏輯應整合到 CourseSelectionState.handle_select_course。
# async def handle_course_selection(course_id: str):
#     """處理學生選課邏輯，包括衝堂檢查等"""
#     from ..states.auth import AuthState
#     from ..models.course import Course
#     from ..models.enrollment import Enrollment
#     from ..models.users import User
#     from ..utils.funcs import check_course_conflict # 假設此函式已根據規格文件 2.4 完整實作
    
#     # 獲取當前使用者
#     # current_user = await User.find_one(User.google_sub == AuthState.current_user_google_id)
#     # if not current_user:
#     #     return rx.window_alert("無法找到您的使用者資訊，請重新登入。")
    
#     # # 獲取欲選課程
#     # selected_course = await Course.find_one(Course.id == course_id)
#     # if not selected_course:
#     #     return rx.window_alert("無法找到該課程，請重試。")
    
#     # if not selected_course.is_open_for_registration:
#     #     return rx.window_alert("該課程目前不開放選課。")
    
#     # # 獲取使用者已選課程
#     # enrollments = await Enrollment.find(Enrollment.user_id.id == current_user.id).to_list()
#     # enrolled_courses = []
#     # for enrollment in enrollments:
#     #     course = await Course.find_one(Course.id == enrollment.course_id.id)
#     #     if course:
#     #         enrolled_courses.append(course)
    
#     # # 檢查衝堂
#     # # TODO: 仔細檢查 check_course_conflict 是否符合規格 2.4 的兩個定義
#     # if check_course_conflict(selected_course, enrolled_courses):
#     #     return rx.window_alert("選課失敗：該課程與您已選課程衝堂。")
    
#     # # 創建選課記錄
#     # new_enrollment = Enrollment(
#     #     user_id=current_user,
#     #     course_id=selected_course,
#     #     academic_year=selected_course.academic_year
#     # )
#     # await new_enrollment.insert()
    
#     return rx.window_alert("選課成功！")
