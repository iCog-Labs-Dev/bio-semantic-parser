from fastapi import APIRouter
from app.models import UserRequest, APIResponse
router = APIRouter()


@router.post("/process", response_model=APIResponse)
def process_data(request: UserRequest):
    return {"result": f"Processed: {request.query}"}

@router.get("/", tags=["Health Check"])
def read_root():
    return {"message": "API is running 🚀"}