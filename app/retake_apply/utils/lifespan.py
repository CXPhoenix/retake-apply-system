import reflex as rx
from reflex.utils import console
from contextlib import asynccontextmanager
from .db import init_db, close_db

@asynccontextmanager
async def lifespan(app: rx.App):
    client = await init_db()
    yield
    if client:
        await close_db(client=client)