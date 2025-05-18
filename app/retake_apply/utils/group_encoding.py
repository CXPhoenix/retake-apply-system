import typing

class GroupEncoding:
    """
    Group Encoding 採用 8 bits 組別 + 8 bits 所屬班級 的編碼格式，
    
    前 8 bits 由 LSB 到 MSB 的組別為:
    - 學生 student
    - 教師 teacher
    - 導師 mentor
    - 行政 specialist
    - 二級主管 jmanager
    - 一級主管 smanager
    - 暫時權限 spacc
    - 資訊組系統管理人 mis
    
    後 8 bits 編排為:
        - 前 2 bits 表示年級
        - 後 6 bits 表示班級號碼
    
    總數為 2 bytes 的數值大小。
    沒有文字表示法。
    """
    def __init__(self, group_number: int):
        pass