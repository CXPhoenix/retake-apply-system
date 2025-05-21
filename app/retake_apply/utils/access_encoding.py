import re
import typing
from functools import singledispatchmethod

_RWX_STR_REGEX = r"^[Rr-][Ww-][Xx-]$" # 用於驗證 rwx 字串格式的正規表示式

class AccessEncoding:
    """以類似 Linux 檔案權限的 RWX 方式編碼和管理系統操作權限。

    本類別將權限抽象為讀取 (Read)、寫入 (Write，代表新增/修改) 和執行 (eXecute，代表刪除)。
    它僅支援特定的權限組合，對應於整數值 0 (---), 4 (r--), 6 (rw-), 和 7 (rwx)。
    這是因為在本系統的權限模型中，通常需要有讀取權限才能進行寫入，需要寫入權限才能刪除。

    Attributes:
        READ (bool): 是否具有讀取權限。
        CREATE (bool): 是否具有新增權限 (等同於 UPDATE)。
        UPDATE (bool): 是否具有修改權限 (等同於 CREATE)。
        DELETE (bool): 是否具有刪除權限。
    """

    def __init__(self, rwx_number: int = 0):
        """初始化 AccessEncoding 物件。

        Args:
            rwx_number (int, optional): 代表權限的整數值。
                必須是 0, 4, 6, 或 7 其中之一。預設為 0 (無任何權限)。
                若提供無效的數值，將預設為 0。
        """
        if rwx_number not in [0, 4, 6, 7]:
            rwx_number = 0  # 對無效輸入進行預設處理
        # 將整數轉換為三位二進制字串，然後映射為布林值
        self._r, self._w, self._x = map(
            lambda v: bool(int(v)), list(f"{bin(rwx_number)[2:]:03s}")
        )

    @property
    def READ(self) -> bool:
        """是否具有讀取權限。"""
        return self._r

    @property
    def CREATE(self) -> bool:
        """是否具有新增權限 (等同於寫入/修改權限)。"""
        return self._w

    @property
    def UPDATE(self) -> bool:
        """是否具有修改權限 (等同於寫入/新增權限)。"""
        return self._w

    @property
    def DELETE(self) -> bool:
        """是否具有刪除權限 (等同於執行權限)。"""
        return self._x

    def __str__(self) -> str:
        """以 'rwx' 字串格式回傳權限狀態。

        例如：'rwx', 'rw-', 'r--', '---'。

        Returns:
            str: 代表權限的 rwx 字串。
        """
        return "".join(
            ["r" if self._r else "-", "w" if self._w else "-", "x" if self._x else "-"]
        )
    
    def __int__(self) -> int:
        """以整數（0, 4, 6, 7）回傳權限編碼。

        Returns:
            int: 代表權限的整數值。
        """
        return int(f"{int(self._r)}{int(self._w)}{int(self._x)}", 2)

    def to_number(self) -> int:
        """回傳權限的整數編碼 (等同於 `int(self)`)。

        Returns:
            int: 代表權限的整數值。
        """
        return int(self)

    def to_string(self) -> str:
        """回傳權限的字串表示 (等同於 `str(self)`)。

        Returns:
            str: 代表權限的 rwx 字串。
        """
        return str(self)

    @singledispatchmethod
    def update(self, access: typing.Any) -> None:
        """根據提供的參數更新權限狀態 (泛型方法)。

        此方法使用 `@singledispatchmethod` 實現多型，
        實際的更新邏輯由針對特定類型註冊的輔助方法執行。

        Args:
            access (typing.Any): 用於更新權限的表示，可以是字串或整數。

        Raises:
            ValueError: 若提供的 `access` 參數類型不受支援。
        """
        raise ValueError(f"不支援的權限表示類型: {type(access)}")
    
    @update.register(str)
    def _update_from_string(self, access: str) -> None:
        """以 'rwx' 字串格式更新權限狀態。

        Args:
            access (str): 代表權限的 rwx 字串 (例如 "rwx", "r--")。
                          不區分大小寫。

        Raises:
            ValueError: 若提供的字串格式不符合 'rwx' 模式。
        """
        if (matched_str := re.match(_RWX_STR_REGEX, access, re.IGNORECASE)) is None:
            raise ValueError(f"無效的權限字串格式: '{access}'. 應為 'rwx' 形式。")
        # 將 'r', 'w', 'x' (或 '-') 映射為布林值
        self._r, self._w, self._x = map(
            lambda v: v.lower() != "-", list(matched_str.group())
        )
    
    @update.register(int)
    def _update_from_int(self, access: int) -> None:
        """以整數（0, 4, 6, 7）更新權限狀態。

        Args:
            access (int): 代表權限的整數值。必須是 0, 4, 6, 或 7。

        Raises:
            ValueError: 若提供的整數值不是有效的權限編碼。
        """
        if access not in [0, 4, 6, 7]:
            raise ValueError(f"無效的權限數值: {access}. 必須是 0, 4, 6, 或 7。")
        # 將整數轉換為三位二進制字串，然後映射為布林值
        self._r, self._w, self._x = map(
            lambda v: bool(int(v)), list(f"{bin(access)[2:]:03s}")
        )
