import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from app.common.exception_handler import http_exception_handler, validation_exception_handler
from .router import router as countries_routes
from mangum import Mangum

app = FastAPI()

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    return await http_exception_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def form_validation_exception_handler(request, exc):
    return await validation_exception_handler(request, exc)

app.include_router(countries_routes)

if os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None:
    handler = Mangum(app)
else:
    load_dotenv()