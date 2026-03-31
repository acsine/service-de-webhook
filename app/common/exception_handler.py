from app.common.responses import ReplyJSON
from fastapi.responses import JSONResponse
import http.client

async def http_exception_handler(request, exc):
    response_model = ReplyJSON(
        status=exc.status_code,
        code="HTTP_ERROR",
        error=True,
        message=str(exc.detail),
        data={}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response_model.toJson(),
    )

async def validation_exception_handler(request, exc):
    error_details = []
    for error in exc.errors():
        error_detail = {
            error.get("loc")[-1]: error.get("msg")
        }
        error_details.append(error_detail)
    response_model = ReplyJSON(
        status=http.client.BAD_REQUEST,
        code="BAD_REQUEST",
        error=True,
        message="Some of the input values are fd invalid",
        data={"errors": error_details}
    )
    return JSONResponse(
        status_code=http.client.BAD_REQUEST,
        content=response_model.toJson(),
    )