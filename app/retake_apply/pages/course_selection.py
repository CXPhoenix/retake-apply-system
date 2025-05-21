"""學生選課頁面模組。

此模組定義了學生進行重補修課程選擇的 Reflex 頁面。
頁面會顯示目前開放選修的課程列表，並允許學生進行線上選課登記。
課程資訊以卡片形式展示，包含課程名稱、代碼、教師、學分、費用及上課時段等。
"""
import reflex as rx
from reflex_google_auth import require_google_login

from ..states.auth import require_group # 引入權限群組檢查裝飾器
from ..models.users import UserGroup # UserGroup Enum 用於角色定義與檢查
from ..models.course import Course # Course 模型用於類型提示
from ..components import navbar # 引入共用的導覽列元件
from ..states.course_selection_state import CourseSelectionState # 匯入此頁面專用的狀態管理類

def render_course_card(course: rx.Var[Course]) -> rx.Component: # course 參數是一個 Reflex Var 包裝的 Course 物件
    """渲染單個課程的資訊卡片元件。

    卡片包含課程的基本資訊、上課時段以及一個選課按鈕。
    按鈕的狀態（文字、是否可點擊）會根據課程是否已被選修以及登記是否開放而動態變化。

    Args:
        course (rx.Var[Course]): 一個 Reflex Var，其值為 `Course` 模型實例，
                                 代表要渲染的課程。

    Returns:
        rx.Component: 代表單個課程卡片的 Reflex UI 元件。
    """
    # 備註：在 Reflex 的 rx.foreach 迴圈中，傳遞給渲染函式的項目 (此處的 course)
    # 通常會被自動包裝成 rx.Var。因此，可以直接存取其屬性，如 course.id。
    # Reflex 會在後端處理 Var 的解析。

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
            rx.text(rx.cond(course.instructor_name, "授課教師: " + course.instructor_name, "授課教師: 未定"), size="2"), # type: ignore
            rx.text(f"學分數: {course.credits.to(str)}", size="2"), # type: ignore
            rx.text(f"總費用: NT$ {course.total_fee.to(str)}", weight="bold", size="2"), # type: ignore
            
            rx.cond(course.time_slots.length() > 0, # type: ignore
                rx.vstack(
                    rx.text("上課時段:", weight="medium", size="2", margin_top="0.5em"),
                    rx.foreach(
                        course.time_slots, # type: ignore
                        lambda ts: rx.hstack(
                            rx.text(f"星期{ts.day_of_week} {ts.period} ({ts.start_time}-{ts.end_time})"),
                            rx.cond(ts.location, rx.text(" @" + ts.location), rx.text("")),
                            rx.cond(ts.week_number, rx.text(" (W" + ts.week_number.to_string() + ")"), rx.text("")),
                            spacing="1",
                            align_items="center", # 確保 hstack 內的元素對齊
                            font_size="0.8em", # 調整字體大小以匹配原來的 size="1"
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
    on_load=CourseSelectionState.on_page_load # 頁面載入時觸發的事件
)
@require_google_login # 要求使用者必須先登入 Google 帳號
@require_group(allowed_groups=[UserGroup.AUTHENTICATED_USER]) # 所有已驗證使用者均可訪問此頁面
                                                              # 選課按鈕的可用性由 CourseSelectionState 內部邏輯控制
def course_selection_page() -> rx.Component:
    """學生課程選擇頁面的主元件。

    此頁面顯示當前學年度可供選擇的重補修課程列表。
    學生可以搜尋課程，並點擊課程卡片上的按鈕進行選課。
    頁面頂部會顯示目前的學年度以及登記時間的相關訊息。

    Returns:
        rx.Component: 組建完成的學生課程選擇頁面。
    """
    return rx.vstack(
        navbar(), # 頁面頂部導覽列
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
                            columns={"initial": "1", "sm": "1", "md": "2", "lg": "3"}, # 響應式欄數
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
