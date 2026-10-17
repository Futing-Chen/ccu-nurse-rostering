from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

def register_exception_handlers(app: FastAPI):
    # 1. Status code 500: 攔截自訂錯誤 / 系統一般錯誤
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logging.error(f"系統發生錯誤: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_code": 500,
                "message": "伺服器內部錯誤，請聯繫管理員",
                "details": str(exc)
            },
        )

    # 3. Status code 400 / 404 等: 攔截程式中主動 raise 的 HTTPException
    # 用法: raise HTTPException(status_code=400, detail={"message": "...", "details": "..."})
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if isinstance(exc.detail, dict):
            message = exc.detail.get("message", "請求發生錯誤")
            details = exc.detail.get("details")
        else:
            message, details = str(exc.detail), None
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error_code": exc.status_code,
                "message": message,
                "details": details
            },
        )

    # 2. Status code 422: 攔截 FastAPI 的驗證錯誤
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "error_code": 422,
                "message": "資料格式驗證失敗",
                "details": exc.errors()
            },
        )
