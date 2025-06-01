from fastapi import FastAPI
from routers import leaves
app = FastAPI()
app.include_router(leaves.router, prefix="/leaves")
