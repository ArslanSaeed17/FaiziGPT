"""
BrallGPT API — FastAPI entrypoint.
"From assignment to startup — BrallGPT gets it done."
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.routers import health, auth, chat, tools, history, profile, admin

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI assistant platform for students, programmers, cybersecurity learners, freelancers, and business starters.",
    version="1.0.0",
)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Global error handlers ----------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": True, "detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": True, "detail": "Internal server error"},
    )


# ---------- Routers ----------
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(tools.router)
app.include_router(history.router)
app.include_router(profile.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {
        "message": "BrallGPT API is running",
        "tagline": "From assignment to startup — BrallGPT gets it done.",
        "docs": "/docs",
    }
