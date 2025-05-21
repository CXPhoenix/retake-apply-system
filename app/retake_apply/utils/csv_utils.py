from typing import List, Dict, Any, Optional
import csv
from io import StringIO
# import pandas as pd # 移除 pandas 依賴，盡量使用標準庫
from pydantic import BaseModel, ValidationError, Field as PydanticField # PydanticField to avoid conflict
from collections import defaultdict

from ..models.course import Course, CourseTimeSlot, VALID_PERIODS # 引入 VALID_PERIODS
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
    # 例如，驗證「是否開放選課」的布林轉換。

    def to_time_slot(self) -> CourseTimeSlot:
        """將 CSV 行中的時段資訊轉換為 CourseTimeSlot 物件。"""
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
    default_academic_year: str # 由系統當前學年度設定傳入
) -> Dict[str, List[str]]:
    """
    從 CSV 檔案內容匯入課程資料。
    處理同一課程多個上課時段的情況。
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
    """從 CSV 檔案內容匯入學生應重補修名單。"""
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
    """
    將學生報名資料匯出為 CSV 字串。
    欄位應符合規格 6.3 (參考「報名下載資料.csv」樣本)。
    """
    output = StringIO()
    # 欄位名稱需與「報名下載資料.csv」樣本一致
    # 範例欄位 (需根據實際樣本調整)
    fieldnames = [
        "報名日期", "學號", "學生姓名", "選課序號", "科目代碼", "科目名稱", 
        "學分數", "費用", "選課狀態", "繳費狀態", "授課教師", "上課時間" 
        # "上課時間" 可能需要特別處理，因為 CourseTimeSlot 是列表
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for i, enroll_obj in enumerate(enrollments):
        # 確保關聯的 User 和 Course 已被 fetch
        user = await enroll_obj.user_id.fetch() if enroll_obj.user_id else None
        course = await enroll_obj.course_id.fetch() if enroll_obj.course_id else None

        if not user or not course:
            # 記錄錯誤或跳過此筆記錄
            continue
        
        # 處理上課時間的表示 (可能需要合併多個時段為一個字串)
        time_slots_str_list = []
        if course.time_slots:
            for ts in course.time_slots:
                ts_str = f"W{ts.week_number or '-'}/D{ts.day_of_week}/{ts.period}({ts.start_time}-{ts.end_time})"
                if ts.location:
                    ts_str += f"@{ts.location}"
                time_slots_str_list.append(ts_str)
        time_slots_display = " | ".join(time_slots_str_list)


        row_data = {
            "報名日期": enroll_obj.enrolled_at.strftime("%Y-%m-%d %H:%M:%S") if enroll_obj.enrolled_at else "",
            "學號": user.student_id or "",
            "學生姓名": user.fullname or user.email, # 優先用 fullname
            "選課序號": str(i + 1), # 或使用 enroll_obj.id (PydanticObjectId)
            "科目代碼": course.course_code,
            "科目名稱": course.course_name,
            "學分數": course.credits,
            "費用": course.total_fee, # Course 模型應有 total_fee
            "選課狀態": enroll_obj.status.value if enroll_obj.status else "",
            "繳費狀態": enroll_obj.payment_status.value if enroll_obj.payment_status else "",
            "授課教師": course.instructor_name or "",
            "上課時間": time_slots_display
        }
        writer.writerow(row_data)

    return output.getvalue()
