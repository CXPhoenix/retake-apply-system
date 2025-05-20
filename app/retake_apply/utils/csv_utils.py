from typing import List, Dict, Any, Optional
import csv
from io import StringIO
import pandas as pd
from pydantic import BaseModel, ValidationError
from ..models.course import Course, CourseTimeSlot
from ..models.required_course import RequiredCourse
from ..models.enrollment import Enrollment
from ..models.users import User

class CourseCSVRow(BaseModel):
    """
    用於驗證開課課程 CSV 匯入資料的 Pydantic 模型。
    對應 CSV 欄位名稱為中文，與資料庫欄位進行轉換。
    """
    學年度: str
    科目代碼: str
    科目名稱: str
    學分數: float
    每學分費用: int
    上課時間_週次: Optional[int] = None
    上課時間_星期: int
    上課時間_節次代號: str
    上課時間_開始: str
    上課時間_結束: str
    授課教師: Optional[str] = None
    上課地點: Optional[str] = None
    人數上限: Optional[int] = None

    def to_course(self) -> Course:
        """將 CSV 資料轉換為 Course 模型實例"""
        time_slot = CourseTimeSlot(
            week_number=self.上課時間_週次,
            day_of_week=self.上課時間_星期,
            period=self.上課時間_節次代號,
            start_time=self.上課時間_開始,
            end_time=self.上課時間_結束,
            location=self.上課地點
        )
        return Course(
            academic_year=self.學年度,
            course_code=self.科目代碼,
            course_name=self.科目名稱,
            credits=self.學分數,
            fee_per_credit=self.每學分費用,
            total_fee=int(self.學分數 * self.每學分費用),
            time_slots=[time_slot],
            instructor_name=self.授課教師,
            max_students=self.人數上限
        )

class RequiredCourseCSVRow(BaseModel):
    """
    用於驗證學生應重補修名單 CSV 匯入資料的 Pydantic 模型。
    對應 CSV 欄位名稱為中文，與資料庫欄位進行轉換。
    """
    學號: str
    學生姓名: str
    不及格科目之學年度: str
    不及格科目代碼: str
    不及格科目名稱: str
    不及格成績: str
    學生GoogleEmail: Optional[str] = None

    def to_required_course(self, user: Optional[User] = None) -> RequiredCourse:
        """將 CSV 資料轉換為 RequiredCourse 模型實例"""
        return RequiredCourse(
            user_id=user,  # 需要在匯入時根據學號或 Email 關聯到 User
            academic_year_taken=self.不及格科目之學年度,
            course_code=self.不及格科目代碼,
            course_name=self.不及格科目名稱,
            original_grade=self.不及格成績
        )

# TODO: 實現 CSV 匯入課程資料的功能 (async def import_courses_from_csv(file_content: str) -> Dict[str, List[str]])
#       - 應讀取 CSV 檔案內容，使用 CourseCSVRow 驗證每一行。
#       - 關鍵：處理一門課程可能有多個上課時段的情況 (規格 6.1)。
#         CSV 中同一課程的多個時段可能表示為多行，僅科目代碼、學年度等核心資訊相同，時段資訊不同。
#         匯入邏輯需要能識別這些行屬於同一課程，並將所有 CourseTimeSlot 合併到一個 Course 物件的 time_slots 列表中。
#         可能需要先將所有行解析為 CourseCSVRow 列表，然後再進行分組和合併。
#       - 返回處理結果，例如 { "success": ["課程A導入成功"], "errors": ["課程B第3行格式錯誤"] }

# TODO: 實現 CSV 匯入學生應重補修名單的功能
# 應提供函數，讀取 CSV 檔案內容，驗證資料格式，並轉換為 RequiredCourse 模型進行儲存。
# 例如：async def import_required_courses_from_csv(file_content: str) -> List[RequiredCourse]
# 需根據學號或 Google Email 關聯到正確的 User 模型，若找不到使用者應記錄錯誤。

# TODO: 實現 CSV 匯出學生報名資料的功能
# 應提供函數，根據查詢條件生成報名資料的 CSV 檔案內容。
# 例如：async def export_enrollments_to_csv(academic_year: str) -> str
# 欄位應包含報名日期、學號、學生姓名、選課序號、科目代碼、科目名稱、學分數、費用等。
# 參考規格中的「報名下載資料.csv」樣本格式。

# TODO: 實現 CSV 資料驗證與錯誤處理邏輯
# 應在匯入時驗證 CSV 檔案格式與欄位內容是否正確，若有錯誤應提供詳細錯誤訊息。
# 例如：若欄位缺失或格式不符，應記錄具體錯誤行與欄位資訊，方便管理者修正。
