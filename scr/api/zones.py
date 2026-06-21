"""
API endpoints для залов
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import GymZone
from pydantic import BaseModel

router = APIRouter(prefix="/api/zones", tags=["zones"])


class ZoneResponse(BaseModel):
    id: int
    name: str
    description: str = None
    capacity: int
    is_active: bool
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[ZoneResponse])
async def get_zones(
    db: Session = Depends(get_db)
):
    """Получение списка всех залов"""
    zones = db.query(GymZone).filter(GymZone.is_active == True).all()
    return zones

