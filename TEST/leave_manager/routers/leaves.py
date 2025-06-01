from fastapi import APIRouter, HTTPException
from schemas.leave_schema import LeaveRequest, LeaveResponse
from services.leave_service import LeaveService

router = APIRouter()
leave_service = LeaveService()

@router.post("/", response_model=LeaveResponse)
def apply_leave(leave: LeaveRequest):
    return leave_service.create_leave(leave)

@router.get("/", response_model=list[LeaveResponse])
def list_leaves():
    return leave_service.get_all_leaves()
