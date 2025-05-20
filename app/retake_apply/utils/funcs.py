from datetime import datetime, timedelta, timezone
from typing import List
from ..models.course import Course, CourseTimeSlot
from ..models.enrollment import Enrollment


def get_now(utc: int = 8) -> datetime:
    return datetime.now(timezone(timedelta(hours=utc)))


def check_time_slot_overlap(slot1: CourseTimeSlot, slot2: CourseTimeSlot) -> bool:
    """
    檢查兩個課程時間插槽是否在時間上重疊。
    
    參數:
        slot1: 第一個課程時間插槽。
        slot2: 第二個課程時間插槽。
    
    返回:
        bool: 如果時間重疊則返回 True，否則返回 False。
    """
    if slot1.day_of_week != slot2.day_of_week:
        return False
        
    # 比較開始和結束時間
    start1 = slot1.start_time
    end1 = slot1.end_time
    start2 = slot2.start_time
    end2 = slot2.end_time
    
    return not (end1 <= start2 or end2 <= start1)


def check_course_conflict(new_course: Course, enrolled_courses: List[Course]) -> bool:
    """
    檢查新選課程是否與已選課程衝堂。
    衝堂定義：
    1. 時間重疊：不同課程之間，若上課時間有任何重疊，即視為衝堂。
    2. 同課程不同時段：若同一門課程於多個不同時段重複開設，學生一旦選取其中一個時段後，其他時段視為衝堂。
    
    參數:
        new_course: 新選的課程。
        enrolled_courses: 學生已選的課程列表。
    
    返回:
        bool: 如果有衝堂則返回 True，否則返回 False。
    """
    for enrolled_course in enrolled_courses:
        # 檢查同課程不同時段
        if enrolled_course.course_code == new_course.course_code and enrolled_course.academic_year == new_course.academic_year:
            return True
            
        # 檢查時間重疊
        for new_slot in new_course.time_slots:
            for enrolled_slot in enrolled_course.time_slots:
                if check_time_slot_overlap(new_slot, enrolled_slot):
                    return True
                    
    return False
