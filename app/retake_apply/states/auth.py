import reflex as rx
from reflex_google_auth import GoogleAuthState


class LoginState(GoogleAuthState):
    
    REDIRECT_URI_ON_LOGIN_REQUIRED = "/"
    
    @rx.var(cache=True)
    async def current_user(self):
        ...
    
    