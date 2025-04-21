from fastapi import APIRouter
from app.models import UserRequest, APIResponse
from app.controllers import process_gse_pipeline

router = APIRouter()


@router.post("/process", response_model=APIResponse)
def process_data(request: UserRequest):
    return {"result": f"Processed: {request.query}"}

@router.get("/", tags=["Health Check"])
def read_root():
    return {"message": "API is running 🚀"}

@router.get("/pipeline/{gse_id}")
def run_pipeline(gse_id: str):
    result = process_gse_pipeline(gse_id)
    return {"result": str(result)}