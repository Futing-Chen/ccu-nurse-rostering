from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
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
