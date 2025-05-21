import reflex as rx
from reflex_google_auth import require_google_login

from ..states.auth import require_group
from ..models.users import UserGroup
from ..models.course import Course # Course 模型用於類型提示
from ..components import navbar
from ..states.course_selection_state import CourseSelectionState # 匯入對應的 State

def render_course_card(course: rx.Var[Course]) -> rx.Component: # course is a Var[Course]
    """渲染單個課程卡片"""
    # course_id_str = course.id.to(str) # type: ignore # Accessing .id on a Var needs .get() or direct use if allowed
    # For simplicity in template, assume course is a dict-like structure or direct access works.
    # If course is a Var[Course], direct access to its attributes like course.id should work in rx.cond/rx.foreach.

    is_enrolled = CourseSelectionState.enrolled_course_ids_this_year.contains(course.id.to(str)) # type: ignore
    
    button_text = rx.cond(
        is_enrolled,
        "已選修",
        rx.cond(
            CourseSelectionState.is_registration_open,
            "我要選課",
            "未開放登記" 
        )
    )
    
    # 禁用按鈕的條件:
    # 1. 登記未開放
    # 2. 已選修此課程
    # 3. 當前使用者不是學生 (如果需要嚴格限制只有學生能點擊)
    button_disabled = rx.cond(
        ~CourseSelectionState.is_registration_open,
        True, # 登記未開放則禁用
        rx.cond(
            is_enrolled,
            True, # 已選修則禁用
            ~CourseSelectionState.has_student_role # 如果不是學生角色，則禁用 (可選)
        )
    )

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(course.course_name, size="4"), # type: ignore
                rx.spacer(),
                rx.badge(f"{course.academic_year} 學年", color_scheme="gray"), # type: ignore
                align_items="center"
            ),
            rx.text(f"科目代碼: {course.course_code}", color_scheme="gray", size="2"), # type: ignore
            rx.text(f"授課教師: {course.instructor_name or '未定'}", size="2"), # type: ignore
            rx.text(f"學分數: {course.credits.to(str)}", size="2"), # type: ignore
            rx.text(f"總費用: NT$ {course.total_fee.to(str)}", weight="bold", size="2"), # type: ignore
            
            rx.cond(course.time_slots.length() > 0, # type: ignore
                rx.vstack(
                    rx.text("上課時段:", weight="medium", size="2", margin_top="0.5em"),
                    rx.foreach(
                        course.time_slots, # type: ignore
                        lambda ts: rx.text(
                            f"星期{ts.day_of_week} {ts.period} ({ts.start_time}-{ts.end_time}) " +
                            f"{'@'+ts.location if ts.location else ''} " +
                            f"{'(W'+ts.week_number.to(str)+')' if ts.week_number else ''}",
                            size="1"
                        )
                    ),
                    align_items="start",
                    spacing="1",
                ),
                rx.text("上課時段未定", size="1", color_scheme="gray")
            ),
            rx.button(
                button_text,
                on_click=lambda: CourseSelectionState.handle_select_course(course.id.to(str)), # type: ignore
                is_disabled=button_disabled, # type: ignore
                width="100%",
                margin_top="1em",
                size="2"
            ),
            spacing="2",
            align_items="stretch", # 使卡片內容撐開
        )
    )

# --- 主頁面 ---
@rx.page(
    route="/course-selection", 
    title="課程選擇",
    on_load=CourseSelectionState.on_page_load
)
@require_google_login # 必須登入才能訪問
@require_group(allowed_groups=[UserGroup.AUTHENTICATED_USER]) # 所有已登入者可見，選課按鈕由State邏輯控制
def course_selection_page() -> rx.Component:
    """學生課程選擇頁面，顯示可選的重補修課程並允許學生進行選課。"""
    return rx.vstack(
        navbar(),
        rx.box(
            rx.heading("重補修課程選擇", size="7", margin_bottom="0.25em"),
            rx.text(f"學年度: {CourseSelectionState.current_academic_year}", color_scheme="gray", margin_bottom="0.25em"),
            rx.text(CourseSelectionState.registration_time_message, weight="bold", margin_bottom="1em"), # type: ignore

            rx.input(
                placeholder="搜尋科目名稱、代碼或教師...",
                value=CourseSelectionState.search_term,
                on_change=CourseSelectionState.handle_search_term_change, # type: ignore
                margin_bottom="1.5em",
                width="100%",
                max_width="500px"
            ),

            rx.cond(
                CourseSelectionState.is_loading, # type: ignore
                rx.center(rx.spinner(size="3"), padding_y="3em"),
                rx.cond(
                    CourseSelectionState.is_registration_open, # type: ignore
                    rx.cond(
                        CourseSelectionState.available_courses.length() > 0, # type: ignore
                        rx.grid(
                            rx.foreach(
                                CourseSelectionState.available_courses,
                                render_course_card
                            ),
                            columns=["1", "1", "2", "3"], # 響應式欄數
                            spacing="3",
                            width="100%"
                        ),
                        rx.center(
                            rx.text("目前無開放選修的課程，或無符合篩選條件的課程。", color_scheme="gray"),
                            padding_y="2em"
                        )
                    ),
                    # 如果登記未開放，顯示登記時間訊息
                    rx.center(
                        rx.text(CourseSelectionState.registration_time_message, color_scheme="orange", weight="bold"), # type: ignore
                        padding_y="2em"
                    )
                )
            ),
            width="100%",
            padding_x="2em",
            padding_y="1em",
            max_width="container.xl",
            margin="0 auto",
        ),
        align_items="center",
        width="100%",
    )
