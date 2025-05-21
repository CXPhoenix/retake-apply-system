import reflex as rx
from reflex_google_auth import require_google_login

from ..states.auth import require_group
from ..models.users import UserGroup
# Enrollment, Course, User 模型在 State 中使用
from ..components import navbar
from ..states.manager_enrollments_state import ManagerEnrollmentsState # 匯入對應的 State
from ..utils.funcs import format_datetime_to_taipei_str # 匯入時間格式化函式

# --- 主頁面 ---
@rx.page(
    route="/manager/enrollments",
    title="學生報名資料管理",
    on_load=ManagerEnrollmentsState.on_page_load
)
@require_google_login
@require_group(allowed_groups=[UserGroup.COURSE_MANAGER, UserGroup.ADMIN])
def manager_enrollments_page() -> rx.Component:
    """課程管理者頁面，用於檢視、下載學生報名資料，並可進行現場報名。"""

    return rx.vstack(
        navbar(),
        rx.box(
            rx.heading("學生報名資料管理", size="7", margin_bottom="1em"),
            rx.hstack(
                rx.select.root(
                    rx.select.trigger(placeholder="篩選學年度"),
                    rx.select.content(
                        rx.foreach(
                            ManagerEnrollmentsState.academic_year_options, # type: ignore
                            lambda option: rx.select.item(option["label"], value=option["value"])
                        )
                    ),
                    value=ManagerEnrollmentsState.selected_academic_year,
                    on_change=ManagerEnrollmentsState.handle_academic_year_change, # type: ignore
                ),
                rx.input(
                    placeholder="依學號/Email/姓名/課程搜尋...",
                    value=ManagerEnrollmentsState.search_term,
                    on_change=ManagerEnrollmentsState.handle_search_term_change, # type: ignore
                    # on_blur=ManagerEnrollmentsState.load_enrollments_data, # 可選
                    width="300px"
                ),
                rx.button("搜尋", on_click=ManagerEnrollmentsState.load_enrollments_data, size="2"), # type: ignore
                rx.spacer(),
                rx.button("現場報名", on_click=ManagerEnrollmentsState.open_manual_enroll_modal, size="2", color_scheme="green"), # type: ignore
                rx.button("匯出CSV", on_click=ManagerEnrollmentsState.handle_csv_export, size="2", color_scheme="blue"), # type: ignore
                spacing="3",
                margin_bottom="1.5em",
                width="100%"
            ),

            # 報名資料列表
            rx.cond(
                ManagerEnrollmentsState.enrollments_list.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("報名時間"),
                            rx.table.column_header_cell("學號"),
                            rx.table.column_header_cell("學生姓名"),
                            rx.table.column_header_cell("Email"),
                            rx.table.column_header_cell("選課學年"),
                            rx.table.column_header_cell("科目代碼"),
                            rx.table.column_header_cell("科目名稱"),
                            rx.table.column_header_cell("選課狀態"),
                            rx.table.column_header_cell("繳費狀態"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            ManagerEnrollmentsState.enrollments_list,
                            lambda enroll: rx.table.row(
                                rx.table.cell(format_datetime_to_taipei_str(enroll.enrolled_at, "%Y-%m-%d %H:%M") if enroll.enrolled_at else "N/A"), # 使用輔助函式
                                rx.table.cell(enroll.user_id.student_id if enroll.user_id else "N/A"), # type: ignore
                                rx.table.cell(enroll.user_id.fullname if enroll.user_id else "N/A"), # type: ignore
                                rx.table.cell(enroll.user_id.email if enroll.user_id else "N/A"), # type: ignore
                                rx.table.cell(enroll.academic_year),
                                rx.table.cell(enroll.course_id.course_code if enroll.course_id else "N/A"), # type: ignore
                                rx.table.cell(enroll.course_id.course_name if enroll.course_id else "N/A"), # type: ignore
                                rx.table.cell(rx.badge(enroll.status.value if enroll.status else "N/A")),
                                rx.table.cell(rx.badge(enroll.payment_status.value if enroll.payment_status else "N/A")),
                            )
                        )
                    ),
                    variant="surface", width="100%"
                ),
                rx.text("找不到報名記錄或目前篩選條件下無記錄。", color_scheme="gray", margin_top="1em")
            ),

            # 現場報名 Modal
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("現場報名作業"),
                    rx.form.root(
                        rx.vstack(
                            rx.form.field(
                                rx.form.label("學生識別碼 (學號或Email):"),
                                rx.input(
                                    value=ManagerEnrollmentsState.manual_enroll_form_data["student_identifier"], # type: ignore
                                    on_change=lambda val: ManagerEnrollmentsState.set_manual_enroll_form_field_value("student_identifier", val), # type: ignore
                                    placeholder="輸入學生學號或Email", required=True
                                )
                            ),
                            rx.form.field(
                                rx.form.label("搜尋課程 (輸入課程代碼或名稱):"),
                                rx.input(
                                    value=ManagerEnrollmentsState.manual_enroll_course_search_term,
                                    on_change=ManagerEnrollmentsState.search_courses_for_manual_enroll, # type: ignore
                                    placeholder="輸入課程關鍵字搜尋"
                                )
                            ),
                            rx.cond(
                                ManagerEnrollmentsState.manual_enroll_course_search_results.length() > 0,
                                rx.box(
                                    rx.vstack(
                                        rx.foreach(
                                            ManagerEnrollmentsState.manual_enroll_course_search_results,
                                            lambda course: rx.button(
                                                f"{course.course_name} ({course.course_code}) - {course.academic_year}",
                                                on_click=lambda: ManagerEnrollmentsState.select_course_for_manual_enroll(course), # type: ignore
                                                variant="ghost", width="100%", text_align="left" # type: ignore
                                            )
                                        ),
                                        spacing="1", border="1px solid var(--gray-a5)", padding="0.5em", border_radius="var(--radius-2)", max_height="150px", overflow_y="auto"
                                    ),
                                    rx.text(f"已選擇課程: {ManagerEnrollmentsState.manual_enroll_selected_course_name}", margin_top="0.5em", color_scheme="green", weight="bold") # type: ignore
                                )
                            ),
                             rx.cond( # 如果已選課程，也顯示
                                (ManagerEnrollmentsState.manual_enroll_form_data["selected_course_id_to_enroll"] != None) & (ManagerEnrollmentsState.manual_enroll_course_search_results.length() == 0), # type: ignore
                                rx.text(f"已選擇課程: {ManagerEnrollmentsState.manual_enroll_selected_course_name}", margin_top="0.5em", color_scheme="green", weight="bold") # type: ignore
                            ),

                            rx.flex(
                                rx.dialog.close(rx.button("取消", on_click=ManagerEnrollmentsState.close_manual_enroll_modal, variant="soft", color_scheme="gray")), # type: ignore
                                rx.button("確認報名", type="submit"), # type: ignore
                                spacing="3", margin_top="1em", justify="end"
                            ),
                            spacing="3", width="100%"
                        ),
                        on_submit=ManagerEnrollmentsState.handle_manual_enroll_submit, # type: ignore
                        width="100%"
                    )
                ),
                open=ManagerEnrollmentsState.show_manual_enroll_modal, # type: ignore
                on_open_change=ManagerEnrollmentsState.set_show_manual_enroll_modal # type: ignore
            ),
            width="100%", padding_x="2em", padding_y="1em", max_width="container.xl", margin="0 auto"
        ),
        align_items="center", width="100%"
    )
