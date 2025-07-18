import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from fastapi import Request
from core.exceptions import EnrollmentError, ResourceNotFoundError
from core.logging import get_logger

logger = get_logger("test_api_exception_handlers")

app = FastAPI()

@app.exception_handler(EnrollmentError)
async def enrollment_exception_handler(request: Request, exc: EnrollmentError):
    logger.error(f"EnrollmentError: {exc}", exc_info=True)
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_exception_handler(request: Request, exc: ResourceNotFoundError):
    logger.error(f"ResourceNotFoundError: {exc}", exc_info=True)
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.get("/enrollment-error")
def raise_enrollment_error():
    raise EnrollmentError("Test EnrollmentError handler")

@app.get("/not-found-error")
def raise_not_found_error():
    raise ResourceNotFoundError("Test ResourceNotFoundError handler")

client = TestClient(app)

def test_enrollment_error_handler():
    response = client.get("/enrollment-error")
    assert response.status_code == 400
    assert response.json()["detail"] == "Test EnrollmentError handler"

def test_resource_not_found_error_handler():
    response = client.get("/not-found-error")
    assert response.status_code == 404
    assert response.json()["detail"] == "Test ResourceNotFoundError handler" 