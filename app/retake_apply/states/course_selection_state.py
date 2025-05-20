import reflex as rx
from typing import List
from beanie.odm.fields import PydanticObjectId

from .auth import AuthState
from ..models.course import Course
from ..models.enrollment import Enrollment, EnrollmentStatus
from ..models.users import User, UserGroup # 匯入 UserGroup
from ..models.academic_year_setting import AcademicYearSetting # 用於獲取當前學年度
# from ..utils.funcs import check_course_conflict # 假設此函式已根據規格文件 2.4 完整實作

# TODO: 根據 .clinerules/CODEING_STYLE_RULE.md 文件，完整實作衝堂檢查邏輯 (check_course_conflict)
#       於 app/retake_apply/utils/funcs.py 中，需包含：
#       - 定義一：時間重疊檢查。
#       - 定義二：同課程不同時段檢查 (若學生已選某課程的一個時段，則該課程的其他時段也應視為衝堂)。

class CourseSelectionState(AuthState):
    """管理學生課程選擇頁面的狀態與邏輯"""

    # 當前開放選課的課程列表
    available_courses: rx.Var[List[Course]] = rx.Var([])
    # 搜尋關鍵字
    search_term: rx.Var[str] = ""
    # 當前系統運作的學年度
    current_academic_year: rx.Var[str] = ""
    # 載入狀態，防止重複載入或顯示 loading spinner
    is_loading: rx.Var[bool] = False

    @rx.cached_var
    def has_student_role(self) -> bool:
        """檢查當前使用者是否為學生"""
        return UserGroup.STUDENT in self.current_user_groups

    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            # 等待 AuthState 水合完成或確保已登入
            return

        if not self.has_student_role:
            # 如果不是學生，可以考慮重導向或顯示錯誤訊息
            # 例如: return rx.redirect("/unauthorized")
            # 目前暫不處理，由頁面裝飾器 @authorize_by_groups 控制
            pass

        await self._load_current_academic_year()
        await self.load_available_courses()

    async def _load_current_academic_year(self):
        """載入當前系統設定的學年度"""
        # TODO: 從 AcademicYearSetting 模型獲取最新的學年度設定
        #       應參考 academic_year_setting.py 中的 TODO: 實現獲取當前學年度的方法
        #       setting = await AcademicYearSetting.get_current()
        #       if setting:
        #           self.current_academic_year = setting.academic_year
        #       else:
        #           self.current_academic_year = "未設定" # 或一個預設值
        #           rx.window_alert("系統尚未設定當前學年度，請聯繫課程管理者。")
        self.current_academic_year = "113-1" # 暫時硬編碼，待實現
        print(f"TODO: _load_current_academic_year 尚未從資料庫載入，使用暫定值: {self.current_academic_year}")


    async def load_available_courses(self):
        """根據目前學年度和搜尋條件載入可選課程"""
        if not self.current_academic_year or self.current_academic_year == "未設定":
            self.available_courses = []
            # rx.window_alert("無法載入課程，因為尚未設定當前學年度。")
            print("無法載入課程，因為尚未設定當前學年度。")
            return

        self.is_loading = True
        query_conditions = {
            "academic_year": self.current_academic_year,
            "is_open_for_registration": True,
        }
        if self.search_term:
            # 使用 MongoDB 的 $regex 操作符進行模糊查詢，i 表示不區分大小寫
            query_conditions["course_name"] = {"$regex": self.search_term, "$options": "i"}
        
        # courses = await Course.find(query_conditions).to_list()
        # self.available_courses = courses
        self.is_loading = False
        print(f"TODO: load_available_courses 尚未從資料庫載入，搜尋條件: {query_conditions}")
        # 模擬載入一些課程資料
        # self.available_courses = [
        #     Course(id=PydanticObjectId(), academic_year="113-1", course_code="C001", course_name="範例課程一", credits=2.0, fee_per_credit=240, total_fee=480, is_open_for_registration=True),
        #     Course(id=PydanticObjectId(), academic_year="113-1", course_code="C002", course_name="範例課程二", credits=3.0, fee_per_credit=240, total_fee=720, is_open_for_registration=True),
        # ]


    async def handle_search_term_change(self, term: str):
        """處理搜尋關鍵字變更"""
        self.search_term = term
        await self.load_available_courses()

    async def handle_select_course(self, course_id_str: str):
        """
        處理學生選課邏輯，包括衝堂檢查等。
        規格文件 2.3. 課程登記流程 & 2.4. 衝堂檢查機制
        """
        if not self.token_is_valid or not self.current_user_google_id:
            return rx.window_alert("請先登入。")

        current_user_db = await User.find_one(User.google_sub == self.current_user_google_id)
        if not current_user_db:
            return rx.window_alert("無法找到您的使用者資訊，請重新登入。")

        try:
            obj_course_id = PydanticObjectId(course_id_str)
        except Exception:
            return rx.window_alert("無效的課程 ID。")

        selected_course = await Course.get(obj_course_id) # type: ignore
        if not selected_course:
            return rx.window_alert("無法找到該課程，請重試。")

        if not selected_course.is_open_for_registration:
            return rx.window_alert("該課程目前不開放選課。")

        # 獲取使用者已選課程 (僅限當前學年度成功或待處理的選課)
        # TODO: 確保 academic_year 的比較是基於 self.current_academic_year
        existing_enrollments = await Enrollment.find(
            Enrollment.user_id == current_user_db.id, # type: ignore
            Enrollment.academic_year == self.current_academic_year,
            Enrollment.status.in_([EnrollmentStatus.SUCCESS, EnrollmentStatus.PENDING])
        ).project(Enrollment.course_id).to_list()

        enrolled_course_ids = [enroll.course_id.id for enroll in existing_enrollments if enroll.course_id] # type: ignore
        enrolled_courses_details = await Course.find(Course.id.in_(enrolled_course_ids)).to_list() # type: ignore

        # TODO: 呼叫 app/retake_apply/utils/funcs.py 中的 check_course_conflict 函式
        #       該函式需要根據規格文件 2.4 的兩個定義 (時間重疊、同課程不同時段) 完整實作。
        #       conflict_reason = await check_course_conflict(selected_course, enrolled_courses_details, current_user_db.id)
        #       if conflict_reason:
        #           return rx.window_alert(f"選課失敗：{conflict_reason}")
        print(f"TODO: 衝堂檢查 (check_course_conflict) 尚未實作。假設目前無衝堂。")

        # 檢查是否已選過此課程 (如果衝堂檢查已包含此邏輯，則可省略)
        # 規格 2.4 定義二：同課程不同時段，選過一個就算衝堂。
        # 這裡的檢查是確保不會重複插入同一門課的 Enrollment 記錄 (即使衝堂檢查允許)。
        # Beanie 的 Enrollment 模型中 (user_id, course_id) 應有複合唯一索引防止重複。
        is_already_enrolled = await Enrollment.find_one(
            Enrollment.user_id == current_user_db.id, # type: ignore
            Enrollment.course_id == selected_course.id # type: ignore
        )
        if is_already_enrolled:
             return rx.window_alert("您已經選修過此課程。")

        new_enrollment = Enrollment(
            user_id=current_user_db.id, # type: ignore
            course_id=selected_course.id, # type: ignore
            academic_year=selected_course.academic_year, # 應為 self.current_academic_year
            status=EnrollmentStatus.SUCCESS # 或 PENDING，視流程而定
        )
        await new_enrollment.insert()
        
        # 選課成功後，可以考慮更新 available_courses (例如人數上限) 或使用者已選課程列表
        await self.load_available_courses() 
        # TODO: 可能需要一個方式通知 DashboardState 更新已選課程列表
        return rx.window_alert("選課成功！")
