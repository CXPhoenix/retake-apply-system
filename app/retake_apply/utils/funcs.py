"""通用輔助函式模組。

此模組包含專案中可能在多處使用到的日期時間處理、
業務邏輯判斷（例如衝堂檢查）等通用功能。
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from ..models.course import Course # CourseTimeSlot 內嵌於 Course 模型檔案中
# 備註：Enrollment 模型目前未在此模組直接使用。

# 備註：get_now 函式提供獲取特定時區時間的功能，
# 但在專案內部，尤其是在與資料庫時間戳互動時，
# 強烈建議統一使用 get_utc_now() 以確保時區一致性。
def get_now(utc_offset: int = 8) -> datetime:
    """獲取帶有指定 UTC 時區偏移的當前日期時間。

    Args:
        utc_offset (int, optional): 相對於 UTC 的小時偏移量。預設為 8 (台北時間 UTC+8)。

    Returns:
        datetime: 一個代表當前日期時間的 timezone-aware `datetime` 物件。
    """
    return datetime.now(timezone(timedelta(hours=utc_offset)))

def get_utc_now() -> datetime:
    """獲取當前的 UTC 日期時間 (timezone-aware)。

    Returns:
        datetime: 一個代表當前 UTC 日期時間的 timezone-aware `datetime` 物件。
    """
    return datetime.now(timezone.utc)

def format_datetime_to_taipei_str(utc_dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """將一個 UTC 的 `datetime` 物件轉換為台北時區 (UTC+8) 的格式化字串。

    如果輸入的 `datetime` 物件為 `None`，則回傳空字串。
    如果輸入的 `datetime` 物件是 naive (無時區資訊)，則會假設其代表 UTC 時間。

    Args:
        utc_dt (Optional[datetime]): 待轉換的 UTC `datetime` 物件。
        fmt (str, optional): 輸出的日期時間格式字串。
                             預設為 "%Y-%m-%d %H:%M:%S"。

    Returns:
        str: 轉換後的台北時間格式化字串，或在輸入為 `None` 時回傳空字串。
    """
    if utc_dt is None:
        return "" # 或可考慮回傳 "N/A" 或其他預設值
    
    # 確保輸入的 datetime 是時區感知的 UTC (如果它來自 Beanie 且正確設定，應該就是)
    # 如果 utc_dt 可能來自其他地方且是 naive datetime，需要先使其 aware
    if utc_dt.tzinfo is None or utc_dt.tzinfo.utcoffset(utc_dt) is None:
        # 假設 naive datetime 代表 UTC 時間
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
    taipei_tz = timezone(timedelta(hours=8))
    taipei_dt = utc_dt.astimezone(taipei_tz)
    return taipei_dt.strftime(fmt)

# check_time_slot_overlap 函式將被 CourseTimeSlot.overlaps_with 取代，故移除或註解。
# def check_time_slot_overlap(slot1: CourseTimeSlot, slot2: CourseTimeSlot) -> bool:
#     """
#     檢查兩個課程時間插槽是否在時間上重疊。
#     此函式已被 CourseTimeSlot.overlaps_with 方法取代。
#     """
#     # ... (舊的實現) ...
#     pass


def check_course_conflict(
    selected_course: Course,
    enrolled_courses: List[Course],
    current_academic_year: str
) -> Optional[str]:
    """
    檢查新選課程 (selected_course) 是否與已選課程列表 (enrolled_courses) 衝堂。
    此檢查基於指定的 `current_academic_year`。

    衝堂定義（根據專案規格文件 2.4）：
    1.  **時間重疊**：不同課程之間，若課程表定的上課時間有任何重疊，即視為衝堂。
        此判斷透過 `CourseTimeSlot.overlaps_with` 方法實現。
    2.  **同課程不同時段**：若同一門課程（以科目代碼及學年期識別）於多個不同時段重複開設，
        學生一旦成功選取其中一個時段的課程後，該課程的其他所有時段對此學生均視為衝堂。

    Args:
        selected_course (Course): 學生嘗試選擇的新課程。
        enrolled_courses (List[Course]): 學生在 `current_academic_year` 已成功選上的課程列表。
        current_academic_year (str): 當前的學年度，用於確認比較範圍 (例如 "113-1")。

    Returns:
        Optional[str]: 如果有衝堂，返回一個描述衝堂原因的字串；若無衝堂，則返回 `None`。
    """
    # 防禦性檢查：確保欲選課程屬於當前學年
    if selected_course.academic_year != current_academic_year:
        return (f"選課錯誤：課程 '{selected_course.course_name}' ({selected_course.course_code}) "
                f"不屬於當前學年 {current_academic_year}。")

    for enrolled_course in enrolled_courses:
        # 僅與當前學年的已選課程進行比較
        if enrolled_course.academic_year != current_academic_year:
            continue

        # 檢查定義二: 同課程不同時段
        # 如果已選課程中，有與欲選課程的 course_code 相同（且 academic_year 也相同，因已過濾），則表示衝堂。
        if enrolled_course.course_code == selected_course.course_code:
            return (f"課程衝突：您已選修過 '{selected_course.course_name}' "
                    f"({selected_course.course_code}) 的其他時段。")

        # 檢查定義一: 時間重疊 (不同課程之間)
        # 遍歷欲選課程的每一個 time_slot
        for selected_slot in selected_course.time_slots:
            # 遍歷當前已選課程的每一個 time_slot
            for enrolled_slot in enrolled_course.time_slots:
                if selected_slot.overlaps_with(enrolled_slot):
                    return (
                        f"課程衝突：'{selected_course.course_name}' ({selected_course.course_code}) 的時段 "
                        f"(星期{selected_slot.day_of_week} 節次{selected_slot.period}) "
                        f"與已選課程 '{enrolled_course.course_name}' ({enrolled_course.course_code}) 的時段 "
                        f"(星期{enrolled_slot.day_of_week} 節次{enrolled_slot.period}) 重疊。"
                    )
                    
    return None # 若遍歷完所有已選課程均未發現衝堂
