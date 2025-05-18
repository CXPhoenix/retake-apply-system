# -*- coding: utf-8 -*-
import re
import typing
from functools import singledispatchmethod

_RWX_STR_REGEX = r"^[Rr-][Ww-][Xx-]$"

class AccessEncoding:
    """
    #################################
    #################################
    ###                           ###
    ###      Access Encoding      ###
    ###     R: Read               ###
    ###     W: Create, Update     ###
    ###     X: Delete             ###
    ###                           ###
    #################################
    #################################

    AccessEncoding 以 Linux 檔案權限的 RWX 編碼方式，管理系統權限的存取控制。

    本類別僅允許 0, 4, 6, 7 四種權限組合（---, r--, rw-, rwx），
    並將權限分為讀取（READ）、新增/修改（CREATE/UPDATE）、刪除（DELETE）。
    
    Attributes:
        * READ (bool): 是否具有讀取權限。
        * CREATE (bool): 是否具有新增權限（與 UPDATE 相同）。
        * UPDATE (bool): 是否具有修改權限（與 CREATE 相同）。
        * DELETE (bool): 是否具有刪除權限。
    
    Methods:
        * __str__(): 以 'rwx' 字串格式回傳權限狀態。
        * __int__(): 以整數（0, 4, 6, 7）回傳權限編碼。
        * to_number(): 回傳權限的整數編碼。
        * to_string(): 回傳權限的字串表示。
        * update(access): 以字串或整數更新權限狀態。
    
    Raises:
        ValueError: 權限格式不符時拋出。

    ****************************
    ****************************
    **                        **
    **   權限編碼額外的內容說明   **
    **                        **
    ****************************
    ****************************

    使用 Linux RWX 方式進行編碼權重管理，
    惟系統使用權上，僅具有前項權限，才得以具備後項權限，
    因此系統權重僅有 0, 4, 6, 7 (---, r--, rw-, rwx)。

    """

    def __init__(self, rwx_number: int = 0):
        if rwx_number not in [0, 4, 6, 7]:
            rwx_number = 0
        self._r, self._w, self._x = map(
            lambda v: bool(int(v)), list(f"{bin(rwx_number)[2:]:03}")
        )

    @property
    def READ(self):
        return self._r

    @property
    def CREATE(self):
        return self._w

    @property
    def UPDATE(self):
        return self._w

    @property
    def DELETE(self):
        return self._x


    def __str__(self) -> str:
        return "".join(
            ["r" if self._r else "-", "w" if self._w else "-", "x" if self._x else "-"]
        )
    
    def __int__(self) -> int:
        return int(f"{int(self._r)}{int(self._w)}{int(self._x)}", 2)

    def to_number(self) -> int:
        return int(self)

    def to_string(self) -> str:
        return str(self)

    @singledispatchmethod
    def update(self, access: typing.Any) -> None:
        raise ValueError("Mismatched access representation.")
    
    @update.register(str)
    def _update(self, access: str) -> None:
        if (matched_str := re.match(_RWX_STR_REGEX, access)) is None:
            raise ValueError("Mismatched access string.")
        self._r, self._w, self._x = map(
            lambda v: v != "-", list(matched_str.group())
        )
    
    @update.register(int)
    def _update(self, access:int) -> None:
        if access not in [0, 4, 6, 7]:
            raise ValueError("Mismatched access number.")
        self._r, self._w, self._x = map(
            lambda v: bool(int(v)), list(f"{bin(access)[2:]:03}")
        )
