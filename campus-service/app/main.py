from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from .routers import auth, students, schedules, repair_orders, scholarships, notices, internal
from .utils.exceptions import (
    app_exception_handler,
    http_exception_handler,
    general_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)

app = FastAPI(title="Campus QA - Campus Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(schedules.router)
app.include_router(repair_orders.router)
app.include_router(scholarships.router)
app.include_router(notices.router)
app.include_router(internal.router)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.get("/health")
def health():
    return {"status": "ok"}
