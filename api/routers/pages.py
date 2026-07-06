from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="api/templates")


@router.get("/")
async def root():
    return RedirectResponse(url="/ui")


@router.get("/ui")
async def ui_page(request: Request):
    return templates.TemplateResponse(request, "search.html")


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")
