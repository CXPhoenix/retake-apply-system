import reflex as rx
from reflex_google_auth import require_google_login
from typing import Dict, Any # List for type hint

from ..states.auth import require_group
from ..models.users import UserGroup
from ..models.course import VALID_PERIODS # Course 模型在 State 中使用
from ..components import navbar
from ..states.manager_courses_state import ManagerCoursesState, EMPTY_TIME_SLOT_DICT # 匯入對應的 State

# --- Helper function to render time slot form ---
def render_time_slot_form(ts_data: rx.Var[Dict], index: rx.Var[int], form_type: str) -> rx.Component:
    """渲染單個課程時段的表單。 form_type: 'add' 或 'edit'"""
    state_method_prefix = "update_add_form_time_slot" if form_type == "add" else "update_edit_form_time_slot"
    remove_method = ManagerCoursesState.remove_time_slot_from_add_form if form_type == "add" else ManagerCoursesState.remove_time_slot_from_edit_form
    
    day_options = [{"label": f"星期{i}", "value": str(i)} for i in range(1, 8)]
    period_options = [{"label": p, "value": p} for p in VALID_PERIODS]

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.form.field(
                    rx.form.label("週次(可選):"),
                    rx.input(
                        type="number",
                        value=ts_data["week_number"], # type: ignore
                        on_change=lambda val: getattr(ManagerCoursesState, state_method_prefix)(index, "week_number", val), # type: ignore
                    ),
                    width="50%"
                ),
                rx.form.field(
                    rx.form.label("星期:"),
                    rx.select.root(
                        rx.select.trigger(placeholder="選擇星期"),
                        rx.select.content(
                            rx.foreach(day_options, lambda opt: rx.select.item(opt["label"], value=opt["value"])) # type: ignore
                        ),
                        value=ts_data["day_of_week"].to(str), # type: ignore
                        on_change=lambda val: getattr(ManagerCoursesState, state_method_prefix)(index, "day_of_week", val), # type: ignore
                    ),
                    width="50%"
                ),
                spacing="3", width="100%"
            ),
            rx.hstack(
                rx.form.field(
                    rx.form.label("節次:"),
                     rx.select.root(
                        rx.select.trigger(placeholder="選擇節次"),
                        rx.select.content(
                            rx.foreach(period_options, lambda opt: rx.select.item(opt["label"], value=opt["value"])) # type: ignore
                        ),
                        value=ts_data["period"], # type: ignore
                        on_change=lambda val: getattr(ManagerCoursesState, state_method_prefix)(index, "period", val), # type: ignore
                    ),
                    width="33%"
                ),
                rx.form.field(
                    rx.form.label("開始時間 (HH:MM):"),
                    rx.input(
                        type="time",
                        value=ts_data["start_time"], # type: ignore
                        on_change=lambda val: getattr(ManagerCoursesState, state_method_prefix)(index, "start_time", val), # type: ignore
                    ),
                    width="33%"
                ),
                rx.form.field(
                    rx.form.label("結束時間 (HH:MM):"),
                    rx.input(
                        type="time",
                        value=ts_data["end_time"], # type: ignore
                        on_change=lambda val: getattr(ManagerCoursesState, state_method_prefix)(index, "end_time", val), # type: ignore
                    ),
                    width="33%"
                ),
                spacing="3", width="100%"
            ),
            rx.form.field(
                rx.form.label("上課地點 (可選):"),
                rx.input(
                    placeholder="例如: 圖書館三樓會議室",
                    value=ts_data["location"], # type: ignore
                    on_change=lambda val: getattr(ManagerCoursesState, state_method_prefix)(index, "location", val), # type: ignore
                ),
                width="100%"
            ),
            rx.button("移除此時段", on_click=lambda: remove_method(index), size="1", color_scheme="red", variant="soft", margin_top="0.5em"), # type: ignore
            spacing="2",
            width="100%"
        ),
        width="100%",
        margin_bottom="0.5em"
    )

# --- 主頁面 ---
@rx.page(
    route="/manager/courses",
    title="課程管理",
    on_load=ManagerCoursesState.on_page_load
)
@require_google_login
@require_group(allowed_groups=[UserGroup.COURSE_MANAGER, UserGroup.ADMIN])
def manager_courses_page() -> rx.Component:
    """課程管理者頁面，用於管理重補修課程。"""
    
    # --- 新增/編輯課程 Modal 的共用表單部分 ---
    def course_form_fields(form_data_var: rx.Var[Dict[str, Any]], form_type: str) -> rx.Component:
        # form_type is "add" or "edit"
        time_slots_list_var = form_data_var[form_type + "_course_form_data"]["time_slots"] # type: ignore
        add_ts_method = getattr(ManagerCoursesState, f"add_new_time_slot_to_{form_type}_form")
        
        return rx.vstack(
            rx.form.field(
                rx.form.label("學年度:"),
                rx.input(
                    value=form_data_var[form_type + "_course_form_data"]["academic_year"], # type: ignore
                    on_change=lambda val: ManagerCoursesState.set_state_var(form_type + "_course_form_data", "academic_year", val), # type: ignore
                    placeholder="例如: 113-1", required=True
                )
            ),
            rx.form.field(
                rx.form.label("科目代碼:"),
                rx.input(
                    value=form_data_var[form_type + "_course_form_data"]["course_code"], # type: ignore
                    on_change=lambda val: ManagerCoursesState.set_state_var(form_type + "_course_form_data", "course_code", val), # type: ignore
                    placeholder="例如: CHN101", required=True
                )
            ),
            rx.form.field(
                rx.form.label("科目名稱:"),
                rx.input(
                    value=form_data_var[form_type + "_course_form_data"]["course_name"], # type: ignore
                    on_change=lambda val: ManagerCoursesState.set_state_var(form_type + "_course_form_data", "course_name", val), # type: ignore
                    placeholder="例如: 高一國文", required=True
                )
            ),
            rx.hstack(
                rx.form.field(rx.form.label("學分數:"), rx.input(type="number", step="0.1", value=form_data_var[form_type + "_course_form_data"]["credits"].to(str), on_change=lambda val: ManagerCoursesState.set_state_var(form_type + "_course_form_data", "credits", val), width="100%")), # type: ignore
                rx.form.field(rx.form.label("每學分費用:"), rx.input(type="number", value=form_data_var[form_type + "_course_form_data"]["fee_per_credit"].to(str), on_change=lambda val: ManagerCoursesState.set_state_var(form_type + "_course_form_data", "fee_per_credit", val), width="100%")), # type: ignore
                spacing="3", width="100%"
            ),
            rx.form.field(rx.form.label("授課教師:"), rx.input(value=form_data_var[form_type + "_course_form_data"]["instructor_name"], on_change=lambda val: ManagerCoursesState.set_state_var(form_type + "_course_form_data", "instructor_name", val))), # type: ignore
            rx.form.field(rx.form.label("人數上限 (可選):"), rx.input(type="number", value=form_data_var[form_type + "_course_form_data"]["max_students"].to(str), on_change=lambda val: ManagerCoursesState.set_state_var(form_type + "_course_form_data", "max_students", val))), # type: ignore
            rx.form.field(
                rx.hstack(
                    rx.text("是否開放選課:"),
                    rx.switch(
                        checked=form_data_var[form_type + "_course_form_data"]["is_open_for_registration"] == "是", # type: ignore
                        on_change=lambda checked: ManagerCoursesState.set_state_var(form_type + "_course_form_data", "is_open_for_registration", "是" if checked else "否") # type: ignore
                    ),
                    align_items="center", spacing="2"
                )
            ),
            rx.heading("上課時段", size="3", margin_top="1em", margin_bottom="0.5em"),
            rx.foreach(
                time_slots_list_var, # type: ignore
                lambda ts, index: render_time_slot_form(ts, index, form_type) # type: ignore
            ),
            rx.button("新增上課時段", on_click=add_ts_method, variant="outline", margin_top="0.5em", size="2"), # type: ignore
            spacing="3", width="100%"
        )

    # --- 頁面主要結構 ---
    return rx.vstack(
        navbar(),
        rx.box(
            rx.heading("課程管理", size="7", margin_bottom="1em"),
            rx.hstack(
                rx.select.root(
                    rx.select.trigger(placeholder="篩選學年度"),
                    rx.select.content(
                        rx.foreach(
                            ManagerCoursesState.academic_year_options, # type: ignore
                            lambda option: rx.select.item(option["label"], value=option["value"])
                        )
                    ),
                    value=ManagerCoursesState.filter_academic_year,
                    on_change=ManagerCoursesState.set_filter_academic_year_and_load, # type: ignore
                ),
                rx.input(
                    placeholder="依課程名稱/代碼/教師搜尋...",
                    value=ManagerCoursesState.search_term,
                    on_change=ManagerCoursesState.set_search_term, # type: ignore
                    on_blur=ManagerCoursesState.handle_search_term_change_and_load, # type: ignore
                    width="300px"
                ),
                rx.button("搜尋", on_click=ManagerCoursesState.load_courses, size="2"), # type: ignore
                rx.spacer(),
                rx.button("新增課程", on_click=ManagerCoursesState.open_add_course_modal, size="2"), # type: ignore
                spacing="3",
                margin_bottom="1.5em",
                width="100%"
            ),

            # CSV 上傳區塊
            rx.card(
                rx.vstack(
                    rx.heading("從 CSV 檔案匯入課程", size="4"),
                    rx.upload(
                        rx.vstack(
                            rx.button("選擇 CSV 檔案", color_scheme="blue", variant="soft"),
                            rx.text("或將檔案拖曳至此處"),
                        ),
                        id="csv_upload_courses",
                        border="1px dashed #ccc",
                        padding="2em",
                        border_radius="var(--radius-3)",
                        width="100%",
                        text_align="center" # type: ignore
                    ),
                    rx.button(
                        "開始匯入", 
                        on_click=lambda: ManagerCoursesState.handle_csv_upload(rx.upload_files(upload_id="csv_upload_courses")), # type: ignore
                        margin_top="1em",
                        is_loading=False, # TODO: 可以綁定一個 loading 狀態
                        size="2"
                    ),
                    rx.cond(
                        ManagerCoursesState.csv_import_feedback != "",
                        rx.box(
                            rx.text("匯入結果:", weight="bold"),
                            rx.text(ManagerCoursesState.csv_import_feedback, white_space="pre-wrap", font_size="0.9em"),
                            padding="1em", margin_top="1em", border="1px solid var(--gray-a5)", border_radius="var(--radius-2)"
                        )
                    ),
                    spacing="3",
                    width="100%"
                ),
                margin_bottom="1.5em"
            ),

            # 課程列表
            rx.cond(
                ManagerCoursesState.courses_list.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("學年"),
                            rx.table.column_header_cell("代碼"),
                            rx.table.column_header_cell("名稱"),
                            rx.table.column_header_cell("學分"),
                            rx.table.column_header_cell("費用/學分"),
                            rx.table.column_header_cell("總費用"),
                            rx.table.column_header_cell("教師"),
                            rx.table.column_header_cell("人數上限"),
                            rx.table.column_header_cell("開放選課"),
                            rx.table.column_header_cell("時段"),
                            rx.table.column_header_cell("操作"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            ManagerCoursesState.courses_list,
                            lambda course: rx.table.row(
                                rx.table.cell(course.academic_year),
                                rx.table.cell(course.course_code),
                                rx.table.cell(course.course_name),
                                rx.table.cell(course.credits.to_string()), # type: ignore
                                rx.table.cell(course.fee_per_credit.to_string()), # type: ignore
                                rx.table.cell(course.total_fee.to_string()), # type: ignore
                                rx.table.cell(course.instructor_name or "N/A"),
                                rx.table.cell(course.max_students.to_string() if course.max_students is not None else "無限制"), # type: ignore
                                rx.table.cell(rx.badge("是", color_scheme="green") if course.is_open_for_registration else rx.badge("否", color_scheme="red")),
                                rx.table.cell(
                                    rx.vstack(
                                        rx.foreach(
                                            course.time_slots,
                                            lambda ts: rx.text(f"W{ts.week_number or '-'}/D{ts.day_of_week}/{ts.period} ({ts.start_time}-{ts.end_time}) @{ts.location or '-'}", font_size="0.8em")
                                        ),
                                        spacing="0", align_items="start"
                                    )
                                ),
                                rx.table.cell(
                                    rx.hstack(
                                        rx.button("編輯", on_click=lambda: ManagerCoursesState.start_edit_course(course), size="1", variant="outline"), # type: ignore
                                        rx.alert_dialog.root(
                                            rx.alert_dialog.trigger(rx.button("刪除", color_scheme="red", size="1", variant="soft")),
                                            rx.alert_dialog.content(
                                                rx.alert_dialog.title("確認刪除課程"),
                                                rx.alert_dialog.description(f"您確定要刪除課程 '{course.course_name}' ({course.course_code}) 嗎？此操作無法復原。"),
                                                rx.flex(
                                                    rx.alert_dialog.cancel(rx.button("取消", variant="soft", color_scheme="gray")),
                                                    rx.alert_dialog.action(rx.button("確認刪除", color_scheme="red", on_click=lambda: ManagerCoursesState.handle_delete_course_confirmed(str(course.id)))), # type: ignore
                                                    spacing="3",
                                                    margin_top="1em",
                                                    justify="end",
                                                ),
                                            ),
                                        ),
                                        spacing="2"
                                    )
                                ),
                            )
                        )
                    ),
                    variant="surface", width="100%"
                ),
                rx.text("找不到課程或目前篩選條件下無課程。", color_scheme="gray", margin_top="1em")
            ),

            # 新增課程 Modal
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("新增課程"),
                    rx.form.root(
                        course_form_fields(ManagerCoursesState, "add"), # type: ignore
                        rx.flex(
                            rx.dialog.close(rx.button("取消", on_click=ManagerCoursesState.close_add_course_modal, variant="soft", color_scheme="gray")), # type: ignore
                            rx.button("儲存新課程", type="submit"), # type: ignore
                            spacing="3", margin_top="1em", justify="end"
                        ),
                        on_submit=ManagerCoursesState.handle_add_new_course, # type: ignore
                        width="100%"
                    ),
                    min_width="700px" # 讓 Modal 寬一點
                ),
                open=ManagerCoursesState.show_add_modal, # type: ignore
                on_open_change=ManagerCoursesState.set_show_add_modal # type: ignore
            ),

            # 編輯課程 Modal
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(f"編輯課程 - {ManagerCoursesState.edit_course_form_data['course_name'] if ManagerCoursesState.edit_course_form_data.contains('course_name') else ''}"), # type: ignore
                    rx.form.root(
                        course_form_fields(ManagerCoursesState, "edit"), # type: ignore
                        rx.flex(
                            rx.dialog.close(rx.button("取消", on_click=ManagerCoursesState.close_edit_course_modal, variant="soft", color_scheme="gray")), # type: ignore
                            rx.button("儲存變更", type="submit"), # type: ignore
                            spacing="3", margin_top="1em", justify="end"
                        ),
                        on_submit=ManagerCoursesState.handle_save_edited_course, # type: ignore
                        width="100%"
                    ),
                     min_width="700px"
                ),
                open=ManagerCoursesState.show_edit_modal, # type: ignore
                on_open_change=ManagerCoursesState.set_show_edit_modal # type: ignore
            ),
            width="100%", padding_x="2em", padding_y="1em", max_width="container.xl", margin="0 auto"
        ),
        align_items="center", width="100%"
    )
