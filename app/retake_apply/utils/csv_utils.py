"""CSV 檔案處理工具模組。

此模組提供將 CSV 檔案內容匯入為 Beanie Document 模型，
以及將 Beanie Document 模型列表匯出為 CSV 格式字串的功能。
主要用於課程資料、學生應重補修名單的批次匯入，以及報名資料的匯出。
"""
from typing import List, Dict, Any, Optional
import csv
from io import StringIO
# 備註：已移除 pandas 依賴，改用標準庫 csv 進行處理。
from pydantic import BaseModel, ValidationError, Field as PydanticField # PydanticField 以避免與 Beanie Field 衝突
from collections import defaultdict

from ..models.course import Course, CourseTimeSlot, VALID_PERIODS # VALID_PERIODS 用於驗證
from ..models.required_course import RequiredCourse
from ..models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus
from ..models.users import User
from ..models.academic_year_setting import AcademicYearSetting # 用於獲取當前學年

# --- CSV 列對應的 Pydantic 模型 ---
class CourseCSVRow(BaseModel):
    """用於驗證開課課程 CSV 匯入資料的 Pydantic 模型。"""
    學年度: str
    科目代碼: str
    科目名稱: str
    學分數: float = PydanticField(..., ge=0)
    每學分費用: int = PydanticField(..., ge=0)
    上課時間_週次: Optional[int] = None
    上課時間_星期: int = PydanticField(..., ge=1, le=7)
    上課時間_節次代號: str
    上課時間_開始: str # HH:MM
    上課時間_結束: str # HH:MM
    授課教師: Optional[str] = None
    上課地點: Optional[str] = None
    人數上限: Optional[int] = PydanticField(default=None, ge=0)
    是否開放選課: Optional[str] = "是" # "是" 或 "否"

    # 可以在這裡加入 validator 來驗證節次代號和時間格式，
    # 但 CourseTimeSlot 模型本身已有驗證，這裡可以簡化。
    # 不過，為了在 CSV 驗證階段就提供明確錯誤，也可以保留部分驗證。
    # 備註：雖然 CourseTimeSlot 模型本身已有驗證，
    # 但在 CSV 驗證階段加入部分驗證（例如「是否開放選課」的布林轉換）
    # 可以更早地提供明確的錯誤回饋給使用者。

    def to_time_slot(self) -> CourseTimeSlot:
        """將 CSV 行資料中的上課時間相關欄位轉換為 `CourseTimeSlot` 物件。

        Returns:
            CourseTimeSlot: 根據 CSV 行資料建立的課程時間插槽物件。
        """
        return CourseTimeSlot(
            week_number=self.上課時間_週次,
            day_of_week=self.上課時間_星期,
            period=self.上課時間_節次代號,
            start_time=self.上課時間_開始,
            end_time=self.上課時間_結束,
            location=self.上課地點
        )

class RequiredCourseCSVRow(BaseModel):
    """用於驗證學生應重補修名單 CSV 匯入資料的 Pydantic 模型。"""
    學號: str
    學生姓名: str # 驗證用，不直接存入 RequiredCourse，除非 User 模型也需要
    不及格科目之學年度: str
    不及格科目代碼: str
    不及格科目名稱: str
    不及格成績: str
    學生GoogleEmail: Optional[str] = None # 優先使用 Email 關聯 User

# --- CSV 匯入功能 ---
async def import_courses_from_csv(
    file_content_bytes: bytes,
    default_academic_year: str
) -> Dict[str, List[str]]:
    """從 CSV 檔案內容匯入多筆課程資料至資料庫。

    此函式會讀取 CSV 檔案內容，驗證每一行資料，並將其轉換為 `Course` 物件。
    特別處理同一課程（相同學年度、科目代碼）在 CSV 中可能因不同上課時段而出現多行的情況，
    會將這些時段合併到單一 `Course` 物件的 `time_slots` 列表中。

    Args:
        file_content_bytes (bytes): CSV 檔案的原始位元組內容。
        default_academic_year (str): 當 CSV 中的學年度欄位為空時，使用的預設學年度。
                                     通常由系統當前的學年度設定傳入。

    Returns:
        Dict[str, List[str]]: 一個包含匯入結果的字典，
                                 鍵為 "success" 的列表包含成功匯入的訊息，
                                 鍵為 "errors" 的列表包含遇到的錯誤訊息。
    """
    results: Dict[str, List[str]] = {"success": [], "errors": []}
    raw_rows: List[Dict[str, Any]] = []
    
    try:
        # 將 bytes 解碼為字串，並使用 StringIO 模擬檔案物件
        csv_file_content = file_content_bytes.decode('utf-8-sig') # utf-8-sig 處理 BOM
        reader = csv.DictReader(StringIO(csv_file_content))
        raw_rows = list(reader)
    except Exception as e:
        results["errors"].append(f"CSV 檔案讀取或解碼失敗: {e}")
        return results

    parsed_course_rows: Dict[str, List[CourseCSVRow]] = defaultdict(list)
    temp_time_slots: Dict[str, List[CourseTimeSlot]] = defaultdict(list)

    for i, row_dict in enumerate(raw_rows):
        row_number = i + 2 # CSV 行號 (包含表頭)
        try:
            # 欄位名清理：移除可能的空格
            cleaned_row = {k.strip(): v for k, v in row_dict.items() if k}
            csv_row_obj = CourseCSVRow(**cleaned_row)

            # 使用 CSV 中的學年度，如果為空則使用預設學年度
            academic_year = csv_row_obj.學年度 or default_academic_year
            course_key = (academic_year, csv_row_obj.科目代碼)
            
            # 暫存 CourseCSVRow 物件，用於後續提取課程基本資訊
            # 只需為每個 course_key 儲存第一個遇到的 row (用於提取非時段資訊)
            if course_key not in parsed_course_rows:
                 parsed_course_rows[course_key].append(csv_row_obj) # 其實只需要一個代表

            # 將每個 CSV 行的時段資訊轉換並暫存
            time_slot = csv_row_obj.to_time_slot()
            temp_time_slots[course_key].append(time_slot)

        except ValidationError as e:
            for error in e.errors():
                results["errors"].append(f"第 {row_number} 行資料驗證失敗: 欄位 '{error['loc'][0]}' - {error['msg']}")
        except Exception as e:
            results["errors"].append(f"第 {row_number} 行處理失敗: {e}")

    # 組合課程並儲存
    for course_key, representative_rows in parsed_course_rows.items():
        academic_year, course_code = course_key
        # 取第一個代表性的 row 來獲取課程基本資訊
        base_info_row = representative_rows[0] 
        
        try:
            # 檢查課程是否已存在
            existing_course = await Course.find_one(
                Course.academic_year == academic_year,
                Course.course_code == course_code
            )
            if existing_course:
                results["errors"].append(f"課程已存在，跳過匯入: 學年 {academic_year}, 科目代碼 {course_code}")
                continue

            is_open_str = base_info_row.是否開放選課.lower() if base_info_row.是否開放選課 else "是"
            is_open = True if is_open_str == "是" else False

            course_obj = Course(
                academic_year=academic_year,
                course_code=course_code,
                course_name=base_info_row.科目名稱,
                credits=base_info_row.學分數,
                fee_per_credit=base_info_row.每學分費用,
                time_slots=temp_time_slots[course_key], # 使用收集到的所有時段
                instructor_name=base_info_row.授課教師,
                max_students=base_info_row.人數上限,
                is_open_for_registration=is_open
            )
            # total_fee 會由 Course 模型的 @computed_field 自動計算
            await course_obj.insert()
            results["success"].append(f"課程 '{course_obj.course_name}' ({course_obj.course_code}) 成功匯入。")
        except Exception as e:
            results["errors"].append(f"儲存課程 '{base_info_row.科目名稱}' ({base_info_row.科目代碼}) 失敗: {e}")
            
    return results

async def import_required_courses_from_csv(
    file_content_bytes: bytes
) -> Dict[str, List[str]]:
    """從 CSV 檔案內容匯入多筆學生應重補修科目記錄至資料庫。

    此函式會讀取 CSV 檔案內容，驗證每一行資料，
    並嘗試根據提供的學生 Google Email 或學號找到對應的 `User` 物件，
    然後創建 `RequiredCourse` 物件。

    Args:
        file_content_bytes (bytes): CSV 檔案的原始位元組內容。

    Returns:
        Dict[str, List[str]]: 一個包含匯入結果的字典，
                                 鍵為 "success" 的列表包含成功匯入的訊息，
                                 鍵為 "errors" 的列表包含遇到的錯誤訊息。
    """
    results: Dict[str, List[str]] = {"success": [], "errors": []}
    raw_rows: List[Dict[str, Any]] = []

    try:
        csv_file_content = file_content_bytes.decode('utf-8-sig')
        reader = csv.DictReader(StringIO(csv_file_content))
        raw_rows = list(reader)
    except Exception as e:
        results["errors"].append(f"CSV 檔案讀取或解碼失敗: {e}")
        return results

    for i, row_dict in enumerate(raw_rows):
        row_number = i + 2
        try:
            cleaned_row = {k.strip(): v for k, v in row_dict.items() if k}
            csv_row_obj = RequiredCourseCSVRow(**cleaned_row)
            
            user = None
            if csv_row_obj.學生GoogleEmail:
                user = await User.find_one(User.email == csv_row_obj.學生GoogleEmail)
            if not user and csv_row_obj.學號: # 如果 Email 找不到，嘗試用學號
                user = await User.find_one(User.student_id == csv_row_obj.學號)

            if not user:
                results["errors"].append(f"第 {row_number} 行錯誤: 找不到學生 (Email: {csv_row_obj.學生GoogleEmail}, 學號: {csv_row_obj.學號})")
                continue
            
            # 檢查是否已存在相同的應重補修記錄
            existing_req = await RequiredCourse.find_one(
                RequiredCourse.user_id.id == user.id, # type: ignore
                RequiredCourse.academic_year_taken == csv_row_obj.不及格科目之學年度,
                RequiredCourse.course_code == csv_row_obj.不及格科目代碼
            )
            if existing_req:
                results["errors"].append(f"第 {row_number} 行錯誤: 學生 {user.email} 的科目 {csv_row_obj.不及格科目代碼} ({csv_row_obj.不及格科目之學年度}) 應重補修記錄已存在。")
                continue

            required_course_obj = RequiredCourse(
                user_id=user.id, # type: ignore
                academic_year_taken=csv_row_obj.不及格科目之學年度,
                course_code=csv_row_obj.不及格科目代碼,
                course_name=csv_row_obj.不及格科目名稱,
                original_grade=csv_row_obj.不及格成績,
                # is_remedied 預設為 False
            )
            await required_course_obj.insert()
            results["success"].append(f"學生 {user.email} 的科目 {required_course_obj.course_name} 應重補修記錄成功匯入。")

        except ValidationError as e:
            for error in e.errors():
                 results["errors"].append(f"第 {row_number} 行資料驗證失敗: 欄位 '{error['loc'][0]}' - {error['msg']}")
        except Exception as e:
            results["errors"].append(f"第 {row_number} 行處理失敗: {e}")
            
    return results

async def export_enrollments_to_csv(enrollments: List[Enrollment]) -> str:
    """將提供的學生選課記錄列表轉換為 CSV 格式的字串。

    輸出的 CSV 欄位將符合專案規格 6.3 中定義的「報名下載資料.csv」樣本格式。
    這包括從關聯的 `User` 和 `Course` 模型中獲取必要資訊，
    並特別處理上課時間 (`time_slots`) 的顯示格式。

    Args:
        enrollments (List[Enrollment]): 包含待匯出選課記錄的列表。
                                        每個 `Enrollment` 物件應已預先載入 (fetch)
                                        其 `user_id` 和 `course_id` 關聯。

    Returns:
        str: 代表選課記錄的 CSV 格式字串。若輸入列表為空，則回傳僅包含表頭的 CSV 字串。
    """
    output = StringIO()
    # 欄位名稱需與「報名下載資料.csv」樣本一致
    # 實際欄位順序和名稱應嚴格參照規格文件或樣本 CSV。
    fieldnames = [
        "報名日期", "學號", "學生姓名", "選課序號", "科目代碼", "科目名稱",
        "學分數", "費用", "選課狀態", "繳費狀態", "授課教師", "上課時間"
        # "上課時間" 欄位會將課程的多個 CourseTimeSlot 合併顯示。
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for i, enroll_obj in enumerate(enrollments):
        # 假設 enroll_obj.user_id 和 enroll_obj.course_id 已經被 fetch
        # 在呼叫此函式前，應確保關聯資料已載入，以避免在迴圈中大量異步 I/O。
        user = enroll_obj.user_id
        course = enroll_obj.course_id

        if not isinstance(user, User) or not isinstance(course, Course):
            # 若關聯資料未正確載入，可以選擇記錄錯誤並跳過，或拋出異常。
            # logging.warning(f"Skipping enrollment export due to missing user/course data: {enroll_obj.id}")
            continue
        
        # 處理上課時間的表示 (合併多個時段為一個字串)
        time_slots_str_list = []
        if course.time_slots:
            for ts in course.time_slots:
                # 格式範例: W10/D1/D1(08:00-08:50)@RoomA
                ts_str = f"W{ts.week_number or '-'}/D{ts.day_of_week}/{ts.period}({ts.start_time}-{ts.end_time})"
                if ts.location:
                    ts_str += f"@{ts.location}"
                time_slots_str_list.append(ts_str)
        time_slots_display = " | ".join(time_slots_str_list) if time_slots_str_list else "未指定"


        row_data = {
            "報名日期": enroll_obj.enrolled_at.strftime("%Y-%m-%d %H:%M:%S") if enroll_obj.enrolled_at else "",
            "學號": user.student_id if user.student_id else "N/A",
            "學生姓名": user.fullname if user.fullname else user.email, # 優先使用 fullname
            "選課序號": str(i + 1), # 使用迴圈索引作為序號，或可考慮使用 enroll_obj.id
            "科目代碼": course.course_code,
            "科目名稱": course.course_name,
            "學分數": str(course.credits) if course.credits is not None else "",
            "費用": str(course.total_fee) if course.total_fee is not None else "", # Course 模型應有 total_fee
            "選課狀態": enroll_obj.status.value if enroll_obj.status else "",
            "繳費狀態": enroll_obj.payment_status.value if enroll_obj.payment_status else "",
            "授課教師": course.instructor_name if course.instructor_name else "未指定",
            "上課時間": time_slots_display
        }
        writer.writerow(row_data)

    return output.getvalue()
