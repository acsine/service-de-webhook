import os
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from .router import router as welcome_routes
from app.common.exception_handler import http_exception_handler, validation_exception_handler
from mangum import Mangum

app = FastAPI()


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def form_validation_exception_handler(request, exc):
    return await validation_exception_handler(request, exc)


app.include_router(welcome_routes)

if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None or os.environ.get("AWS_EXECUTION_ENV") is not None:
    handler = Mangum(app)
else:
    from dotenv import load_dotenv

    load_dotenv()
