"""
API endpoints для услуг
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import Service
from pydantic import BaseModel

router = APIRouter(prefix="/api/services", tags=["services"])


class ServiceResponse(BaseModel):
    id: int
    name: str
    category: str
    description: str = None
    duration_minutes: int
    max_participants: int
    base_price: float
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[ServiceResponse])
async def get_services(
    db: Session = Depends(get_db)
):
    """Получение списка всех услуг"""
    services = db.query(Service).all()
    return services

