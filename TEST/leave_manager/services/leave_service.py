from db.models import Leave
from schemas.leave_schema import LeaveRequest, LeaveResponse
from db.database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

class LeaveService:
    def create_leave(self, leave: LeaveRequest) -> LeaveResponse:
        db = SessionLocal()
        new_leave = Leave(**leave.dict())
        db.add(new_leave)
        db.commit()
        db.refresh(new_leave)
        db.close()
        return LeaveResponse(**new_leave.__dict__)

    def get_all_leaves(self) -> list[LeaveResponse]:
        db = SessionLocal()
        leaves = db.query(Leave).all()
        db.close()
        return [LeaveResponse(**leave.__dict__) for leave in leaves]
