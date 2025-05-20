import reflex as rx
from typing import List, Optional, Dict, Any
from beanie.odm.fields import PydanticObjectId # 確保匯入

from .auth import AuthState
from ..models.users import User, UserGroup
from ..models.course import Course
from ..models.enrollment import Enrollment, EnrollmentStatus
from ..models.academic_year_setting import AcademicYearSetting
# from ..utils.csv_utils import export_enrollments_to_csv # 假設的 CSV 工具
# from ..utils.funcs import check_course_conflict # 衝堂檢查

class ManagerEnrollmentsState(AuthState):
    """管理課程管理者操作報名資料的狀態與邏輯"""

    enrollments_list: rx.Var[List[Enrollment]] = rx.Var([])
    search_term: rx.Var[str] = ""
    selected_academic_year: rx.Var[str] = "ALL" # "ALL" 代表全部學年度
    academic_year_options: rx.Var[List[Dict[str, str]]] = rx.Var([{"label": "全部學年度", "value": "ALL"}])

    # 現場報名 Modal 控制
    show_manual_enroll_modal: rx.Var[bool] = False
    # TODO: 設計現場報名表單的資料結構
    #       可能需要：student_identifier (學號/Email), course_search_term, selected_course_id
    manual_enroll_form_data: rx.Var[Dict[str, Any]] = rx.Var({
        "student_identifier": "",
        "course_id_to_enroll": None, 
        # 可以考慮加入課程搜尋結果列表 rx.Var[List[Course]] 以供選擇
    })
    
    # 用於現場報名時搜尋課程
    manual_enroll_course_search_results: rx.Var[List[Course]] = rx.Var([])
    manual_enroll_course_search_term: rx.Var[str] = ""


    async def on_page_load(self):
        """頁面載入時執行的操作"""
        if not self.is_hydrated or not self.token_is_valid:
            return
        if UserGroup.COURSE_MANAGER not in self.current_user_groups:
            # return rx.redirect("/unauthorized")
            pass
        await self._load_academic_year_options()
        await self.load_enrollments_data()

    async def _load_academic_year_options(self):
        """載入學年度選項供篩選"""
        # settings = await AcademicYearSetting.find_all(sort=[("academic_year", -1)]).to_list()
        # options = [{"label": "全部學年度", "value": "ALL"}] + [{"label": s.academic_year, "value": s.academic_year} for s in settings]
        # self.academic_year_options = options
        print("TODO: _load_academic_year_options 尚未從資料庫載入")
        # 模擬資料
        self.academic_year_options = [
            {"label": "全部學年度", "value": "ALL"},
            {"label": "113-1", "value": "113-1"},
            {"label": "112-2", "value": "112-2"},
        ]


    async def load_enrollments_data(self):
        """載入或篩選報名資料列表"""
        # query_conditions = {}
        # if self.selected_academic_year != "ALL":
        #     query_conditions["academic_year"] = self.selected_academic_year
        #
        # # TODO: 構建更複雜的 search_term 查詢邏輯
        # #       可能需要查詢 User 和 Course 表，然後再根據關聯的 ID 查詢 Enrollment
        # #       例如，如果 search_term 是學生姓名，先找到 User ID，再用 User ID 查 Enrollment
        # if self.search_term:
        #    print(f"搜尋字詞 '{self.search_term}' 的查詢邏輯待實現")
        #
        # self.enrollments_list = await Enrollment.find(query_conditions, fetch_links=True).to_list()
        print(f"TODO: load_enrollments_data 尚未從資料庫載入 (學年: {self.selected_academic_year}, 搜尋: {self.search_term})")
        # 模擬資料
        # user1 = User(id=PydanticObjectId(), fullname="學生A", student_id="S1001")
        # course1 = Course(id=PydanticObjectId(), course_name="課程X", course_code="CX01")
        # self.enrollments_list = [
        #     Enrollment(id=PydanticObjectId(), user_id=user1, course_id=course1, academic_year="113-1", status=EnrollmentStatus.SUCCESS, payment_status="待繳費")
        # ]

    async def handle_search_term_change(self, term: str):
        self.search_term = term
        # 可以選擇即時搜尋或等待按鈕觸發
        # await self.load_enrollments_data() 

    async def handle_academic_year_change(self, year: str):
        self.selected_academic_year = year
        await self.load_enrollments_data()


    async def handle_csv_export(self):
        """處理下載報名資料 CSV"""
        # TODO: 根據 self.enrollments_list (當前篩選結果) 產生 CSV 內容
        #       需符合規格 6.3 (學生報名資料匯出格式)
        #       欄位包含：報名日期, 學號, 學生姓名, 選課序號, 科目代碼, 科目名稱, 學分數, 費用 等。
        #       注意 Link 欄位 (user_id, course_id) 的資料提取。
        # csv_data_string = "報名日期,學號,學生姓名,選課序號,科目代碼,科目名稱,學分數,費用\n" # Header
        # for enroll in self.enrollments_list:
        #     user_info = enroll.user_id # 假設已 fetch_links
        #     course_info = enroll.course_id # 假設已 fetch_links
        #     row = [
        #         enroll.enrolled_at.strftime("%Y/%m/%d") if enroll.enrolled_at else "",
        #         user_info.student_id if user_info else "",
        #         user_info.fullname if user_info else "",
        #         str(enroll.id), # 選課序號 (Enrollment ID)
        #         course_info.course_code if course_info else "",
        #         course_info.course_name if course_info else "",
        #         str(course_info.credits) if course_info else "",
        #         str(course_info.total_fee) if course_info else "" # 確保 total_fee 已計算
        #     ]
        #     csv_data_string += ",".join(row) + "\n"
        # return rx.download(data=csv_data_string.encode("utf-8-sig"), filename="報名資料.csv") # utf-8-sig for Excel BOM
        print("TODO: ManagerEnrollmentsState.handle_csv_export 匯出 CSV")
        return rx.toast.info("TODO: CSV 下載功能尚未實作")

    # --- 現場報名 Modal ---
    def open_manual_enroll_modal(self):
        self.manual_enroll_form_data = {"student_identifier": "", "course_id_to_enroll": None}
        self.manual_enroll_course_search_results = []
        self.manual_enroll_course_search_term = ""
        self.show_manual_enroll_modal = True

    def close_manual_enroll_modal(self):
        self.show_manual_enroll_modal = False
        
    async def search_courses_for_manual_enroll(self, term: str):
        """現場報名時搜尋課程"""
        self.manual_enroll_course_search_term = term
        if not term or len(term) < 2: # 至少輸入2個字才搜尋
            self.manual_enroll_course_search_results = []
            return
        # TODO: 根據 term 搜尋課程 (僅開放選課的)
        # self.manual_enroll_course_search_results = await Course.find(
        #     Course.course_name.ilike(f"%{term}%"),
        #     Course.is_open_for_registration == True
        # ).limit(10).to_list()
        print(f"TODO: search_courses_for_manual_enroll 搜尋課程: {term}")

    def select_course_for_manual_enroll(self, course_id: str):
        self.manual_enroll_form_data["course_id_to_enroll"] = course_id
        # 可以考慮清除搜尋結果或顯示已選課程名稱
        # self.manual_enroll_course_search_results = [] 
        # self.manual_enroll_course_search_term = "已選擇課程ID: " + course_id


    async def handle_manual_enroll_submit(self):
        """處理現場報名表單提交"""
        # TODO: 規格 3.4
        #       從 self.manual_enroll_form_data 獲取 student_identifier 和 course_id_to_enroll
        #       查找 User (依學號/Email)
        #       查找 Course
        #       執行衝堂檢查 (check_course_conflict)
        #       創建 Enrollment 記錄
        #       (可選) 產生繳費資訊 (規格 5.1)
        #       成功後關閉 Modal，重新載入報名列表，並提示成功
        student_id = self.manual_enroll_form_data.get("student_identifier")
        course_id = self.manual_enroll_form_data.get("course_id_to_enroll")

        if not student_id or not course_id:
            return rx.toast.error("學生和課程皆須選擇。")
        
        # found_user = await User.find_one(User.student_id == student_id) # 或 Email
        # if not found_user:
        #     return rx.toast.error(f"找不到學生：{student_id}")
        #
        # selected_course = await Course.get(PydanticObjectId(course_id))
        # if not selected_course:
        #     return rx.toast.error("找不到所選課程。")
        #
        # # ... 衝堂檢查 ...
        # # conflict = await check_course_conflict(...)
        # # if conflict: return rx.toast.error("衝堂！")
        #
        # # new_enrollment = Enrollment(...)
        # # await new_enrollment.insert()
        #
        # self.close_manual_enroll_modal()
        # await self.load_enrollments_data()
        # return rx.toast.success(f"學生 {student_id} 報名課程 {course_id} 成功！")
        print(f"TODO: handle_manual_enroll_submit 現場報名: 學生 {student_id}, 課程 {course_id}")
        self.close_manual_enroll_modal()
        return rx.toast.info("TODO: 現場報名功能尚未完整實作")
