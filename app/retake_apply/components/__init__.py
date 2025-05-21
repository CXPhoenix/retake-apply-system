"""Components 模組的初始化檔案。

此檔案用於匯出模組內定義的共用元件，
使其可以透過 `from retake_apply.components import ...` 的方式被其他模組引用。
"""

from .navbar import navbar # 匯出 navbar 元件

__all__ = ["navbar"] # 定義 `from .components import *` 時會匯出的內容
