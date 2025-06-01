from pydantic import BaseModel
from datetime import date

class LeaveRequest(BaseModel):
    employee_name: str
    start_date: date
    end_date: date
    reason: str

class LeaveResponse(LeaveRequest):
    id: int
    status: str
