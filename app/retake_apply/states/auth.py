import functools
from typing import Callable

import reflex as rx
from beanie.exceptions import CollectionWasNotInitialized
from reflex_google_auth import GoogleAuthState, google_oauth_provider

from ..models import User
from ..utils.data_enum import Groups

ComponentCallable = Callable[[], rx.Component]


class AuthState(GoogleAuthState):
    """"""

    REDIRECT_URI_ON_LOGIN_REQUIRED = "/login"
    REDIRECT_URI_ON_UNAUTHORIZED = "/dashboard"

    async def _user_in_db(self) -> User | None:
        """"""
        try:
            User.get_settings()
            return await User.find_one(User.email == self.tokeninfo.get("email"))
        except CollectionWasNotInitialized:
            return None

    async def _insert_user_to_db(self) -> User | None:
        try:
            User.get_settings()
            return (await User(
                email=self.tokeninfo.get("email"),
                name=self.tokeninfo.get("name"),
                family_name=self.tokeninfo.get("family_name"),
                given_name=self.tokeninfo.get("given_name"),
            )).save()
        except CollectionWasNotInitialized:
            return None

    @rx.var(cache=True)
    async def get_current_user(self) -> User | None:
        """取得目前使用者

        若是目前的使用者不在 DB 中，會將在 User 中創建使用者資料。

        Returns:
            (User): 存在 DB 中的使用者資訊。
        """
        if not self.token_is_valid:
            return None
        if (current_user := await self._user_in_db()) is None:
            current_user = await self._insert_user_to_db()
        return current_user

    @rx.var(cache=True)
    async def user_roles(self) -> list[Groups]:
        """"""
        if (current_user := await self.get_current_user) is None:
            return []
        return current_user.roles


def require_access(
    groups: list[Groups] = [Groups.STUDENT],
) -> ComponentCallable | Callable[[ComponentCallable], ComponentCallable]:
    """"""

    def _inner(page: ComponentCallable) -> ComponentCallable:
        @functools.wraps(page)
        def _auth_wrapper() -> rx.Component:
            def _group_access_check() -> rx.Component:
                return rx.cond(
                    any([group in AuthState.user_roles for group in groups]),
                    page(),
                    rx.redirect(AuthState.REDIRECT_URI_ON_UNAUTHORIZED),
                )

            return google_oauth_provider(
                rx.cond(
                    rx.State.is_hydrated,  # 確認前端是否已準備就緒 (hydrated)
                    rx.cond(
                        AuthState.token_is_valid,  # 使用你的 AuthState 檢查 token 是否有效
                        _group_access_check(),  # 如果 token 有效，渲染目標頁面；否則，重新導向到 AuthState 中定義的 URI
                        rx.redirect(AuthState.REDIRECT_URI_ON_LOGIN_REQUIRED),
                    ),
                    rx.center(rx.spinner(size="3"), class_name=["p-[5em]"]),
                )
            )

        return _auth_wrapper

    return _inner
