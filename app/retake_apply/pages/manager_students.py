"""課程管理者管理學生應重補修名單頁面模組。

此模組定義了供課程管理者（及系統管理者）新增、編輯、刪除及查詢
學生應重補修科目記錄的 Reflex 頁面。
功能包括手動輸入記錄、批次從 CSV 檔案匯入名單，以及展示記錄列表。
"""
import reflex as rx
from reflex_google_auth import require_google_login

from ..states.auth import require_group # 引入權限群組檢查裝飾器
from ..models.users import UserGroup # UserGroup Enum 用於角色定義與檢查
from ..components import navbar # 引入共用的導覽列元件
from ..states.manager_students_state import ManagerStudentsState # 匯入此頁面專用的狀態管理類

# --- 主頁面 ---
@rx.page(
    route="/manager/students",
    title="學生應重補修名單管理",
    on_load=ManagerStudentsState.on_page_load # 頁面載入時觸發的事件
)
@require_google_login # 要求使用者必須先登入 Google 帳號
@require_group(allowed_groups=[UserGroup.COURSE_MANAGER, UserGroup.SYSTEM_ADMIN]) # 課程管理者或系統管理者可訪問
def manager_students_page() -> rx.Component:
    """課程管理者管理學生應重補修名單的頁面元件。

    此頁面提供篩選、搜尋應重補修記錄列表的功能，允許管理者新增記錄
    （透過表單或 CSV 匯入）、編輯現有記錄，以及刪除記錄。

    Returns:
        rx.Component: 組建完成的學生應重補修名單管理頁面。
    """

    # --- 新增/編輯記錄 Modal 的表單部分 ---
    def record_form_fields() -> rx.Component:
        """內部輔助函式，渲染新增或編輯應重補修記錄表單中的共用欄位。

        這些欄位會綁定到 `ManagerStudentsState.form_data` 中的對應狀態變數。

        Returns:
            rx.Component: 包含應重補修記錄資訊輸入欄位的 VStack 元件。
        """
        return rx.vstack(
            rx.form.field(
                rx.form.label("學生識別碼 (學號或Email):"),
                rx.input(
                    value=ManagerStudentsState.form_data["user_identifier"], # type: ignore
                    on_change=lambda val: ManagerStudentsState.set_form_field_value("user_identifier", val), # type: ignore
                    placeholder="輸入學生學號或Email", required=True
                )
            ),
            rx.form.field(
                rx.form.label("不及格科目之學年度:"),
                rx.input(
                    value=ManagerStudentsState.form_data["academic_year_taken"], # type: ignore
                    on_change=lambda val: ManagerStudentsState.set_form_field_value("academic_year_taken", val), # type: ignore
                    placeholder="例如: 112-1", required=True
                )
            ),
            rx.form.field(
                rx.form.label("不及格科目代碼:"),
                rx.input(
                    value=ManagerStudentsState.form_data["course_code"], # type: ignore
                    on_change=lambda val: ManagerStudentsState.set_form_field_value("course_code", val), # type: ignore
                    placeholder="例如: MATH101", required=True
                )
            ),
            rx.form.field(
                rx.form.label("不及格科目名稱:"),
                rx.input(
                    value=ManagerStudentsState.form_data["course_name"], # type: ignore
                    on_change=lambda val: ManagerStudentsState.set_form_field_value("course_name", val), # type: ignore
                    placeholder="例如: 微積分(上)", required=True
                )
            ),
            rx.form.field(
                rx.form.label("不及格成績:"),
                rx.input(
                    value=ManagerStudentsState.form_data["original_grade"], # type: ignore
                    on_change=lambda val: ManagerStudentsState.set_form_field_value("original_grade", val), # type: ignore
                    placeholder="例如: 45 或 F", required=True
                )
            ),
            rx.form.field(
                rx.hstack(
                    rx.text("是否已完成重補修:"),
                    rx.switch(
                        checked=ManagerStudentsState.form_data["is_remedied"], # type: ignore
                        on_change=lambda checked: ManagerStudentsState.set_form_field_value("is_remedied", checked) # type: ignore
                    ),
                    align_items="center", spacing="2"
                )
            ),
            spacing="3", width="100%"
        )

    return rx.vstack(
        navbar(),
        rx.box(
            rx.heading("學生應重補修名單管理", size="7", margin_bottom="1em"),
            rx.hstack(
                rx.input(
                    placeholder="依學號/Email/姓名/科目搜尋...",
                    value=ManagerStudentsState.search_term,
                    on_change=ManagerStudentsState.handle_search_term_change, # type: ignore
                    # on_blur=ManagerStudentsState.load_records, # 可選：失焦時搜尋
                    width="300px"
                ),
                rx.button("搜尋", on_click=ManagerStudentsState.load_records, size="2"), # type: ignore
                rx.spacer(),
                rx.button("新增記錄", on_click=ManagerStudentsState.open_add_modal, size="2"), # type: ignore
                spacing="3",
                margin_bottom="1.5em",
                width="100%"
            ),

            # CSV 上傳區塊
            rx.card(
                rx.vstack(
                    rx.heading("從 CSV 檔案匯入學生應重補修名單", size="4"),
                    rx.upload(
                        rx.vstack(
                            rx.button("選擇 CSV 檔案", color_scheme="blue", variant="soft"),
                            rx.text("或將檔案拖曳至此處"),
                        ),
                        id="csv_upload_required_courses",
                        border="1px dashed #ccc", padding="2em", border_radius="var(--radius-3)",
                        width="100%", text_align="center" # type: ignore
                    ),
                    rx.button(
                        "開始匯入", 
                        on_click=lambda: ManagerStudentsState.handle_csv_upload(rx.upload_files(upload_id="csv_upload_required_courses")), # type: ignore
                        margin_top="1em", size="2"
                    ),
                    rx.cond(
                        ManagerStudentsState.csv_import_feedback != "",
                        rx.box(
                            rx.text("匯入結果:", weight="bold"),
                            rx.text(ManagerStudentsState.csv_import_feedback, white_space="pre-wrap", font_size="0.9em"),
                            padding="1em", margin_top="1em", border="1px solid var(--gray-a5)", border_radius="var(--radius-2)"
                        )
                    ),
                    spacing="3", width="100%"
                ),
                margin_bottom="1.5em"
            ),

            # 列表顯示區
            rx.cond(
                ManagerStudentsState.required_courses_list.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("學號"),
                            rx.table.column_header_cell("學生姓名"),
                            rx.table.column_header_cell("Email"),
                            rx.table.column_header_cell("不及格學年"),
                            rx.table.column_header_cell("科目代碼"),
                            rx.table.column_header_cell("科目名稱"),
                            rx.table.column_header_cell("原成績"),
                            rx.table.column_header_cell("已重補修"),
                            rx.table.column_header_cell("上傳時間"),
                            rx.table.column_header_cell("操作"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            ManagerStudentsState.required_courses_list,
                            lambda record: rx.table.row(
                                rx.table.cell(record.user_id.student_id if record.user_id else "N/A"), # type: ignore
                                rx.table.cell(record.user_id.fullname if record.user_id else "N/A"), # type: ignore
                                rx.table.cell(record.user_id.email if record.user_id else "N/A"), # type: ignore
                                rx.table.cell(record.academic_year_taken),
                                rx.table.cell(record.course_code),
                                rx.table.cell(record.course_name),
                                rx.table.cell(record.original_grade),
                                rx.table.cell(rx.badge("是", color_scheme="green") if record.is_remedied else rx.badge("否", color_scheme="gray")),
                                rx.table.cell(record.uploaded_at.strftime("%Y-%m-%d %H:%M") if record.uploaded_at else "N/A"),
                                rx.table.cell(
                                    rx.hstack(
                                        rx.button("編輯", on_click=lambda: ManagerStudentsState.open_edit_modal(record), size="1", variant="outline"), # type: ignore
                                        rx.alert_dialog.root(
                                            rx.alert_dialog.trigger(rx.button("刪除", color_scheme="red", size="1", variant="soft")),
                                            rx.alert_dialog.content(
                                                rx.alert_dialog.title("確認刪除記錄"),
                                                rx.alert_dialog.description(f"確定要刪除學生 {record.user_id.fullname if record.user_id else ''} 的科目 {record.course_name} 這筆應重補修記錄嗎？"), # type: ignore
                                                rx.flex(
                                                    rx.alert_dialog.cancel(rx.button("取消", variant="soft", color_scheme="gray")),
                                                    rx.alert_dialog.action(rx.button("確認刪除", color_scheme="red", on_click=lambda: ManagerStudentsState.handle_delete_record_confirmed(str(record.id)))), # type: ignore
                                                    spacing="3", margin_top="1em", justify="end",
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
                rx.text("找不到記錄或目前篩選條件下無記錄。", color_scheme="gray", margin_top="1em")
            ),

            # 新增/編輯 Modal
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(ManagerStudentsState.form_modal_title), # type: ignore
                    rx.form.root(
                        record_form_fields(),
                        rx.flex(
                            rx.dialog.close(rx.button("取消", on_click=ManagerStudentsState.close_form_modal, variant="soft", color_scheme="gray")), # type: ignore
                            rx.button("儲存", type="submit"), # type: ignore
                            spacing="3", margin_top="1em", justify="end"
                        ),
                        on_submit=ManagerStudentsState.handle_save_record, # type: ignore
                        width="100%"
                    ),
                    min_width="500px"
                ),
                open=ManagerStudentsState.show_form_modal, # type: ignore
                on_open_change=ManagerStudentsState.set_show_form_modal # type: ignore
            ),
            width="100%", padding_x="2em", padding_y="1em", max_width="container.xl", margin="0 auto"
        ),
        align_items="center", width="100%"
    )
