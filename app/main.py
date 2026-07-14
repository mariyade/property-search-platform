from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routers import admin, agent, auth, health, pages, search_run, users

app = FastAPI(title="Property Search Platform")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router)
app.include_router(health.router)
app.include_router(search_run.router)
app.include_router(agent.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(auth.router)
