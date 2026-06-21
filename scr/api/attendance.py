"""
API endpoints для посещений
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import User, UserRole, Visit, TrainingSession, TrainingSessionParticipant
from scr.core.dependencies import get_current_active_user

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.get("/me/history")
async def get_my_visit_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение истории посещений текущего пользователя (клиент/тренер)"""
    if current_user.role == UserRole.CLIENT:
        visits = (
            db.query(Visit)
            .filter(Visit.client_id == current_user.id)
            .order_by(Visit.check_in_time.desc())
            .all()
        )
    elif current_user.role == UserRole.TRAINER:
        # 1) Если есть Visit с trainer_id — используем их (детально по каждому клиенту)
        visits = (
            db.query(Visit)
            .filter(Visit.trainer_id == current_user.id)
            .order_by(Visit.check_in_time.desc())
            .all()
        )

        # 2) Если Visit еще не проставлены (старые данные) — показываем историю по проведенным занятиям
        if not visits:
            sessions = (
                db.query(TrainingSession)
                .filter(
                    TrainingSession.trainer_id == current_user.id,
                    TrainingSession.is_completed == True,
                )
                .order_by(TrainingSession.session_date.desc(), TrainingSession.start_time.desc())
                .all()
            )

            session_ids = [s.id for s in sessions]
            parts = []
            if session_ids:
                parts = (
                    db.query(TrainingSessionParticipant)
                    .filter(TrainingSessionParticipant.session_id.in_(session_ids))
                    .all()
                )

            parts_by_session = {}
            for p in parts:
                parts_by_session.setdefault(p.session_id, []).append(p)

            history = []
            for s in sessions:
                check_in_dt = datetime.combine(s.session_date, s.start_time).replace(tzinfo=timezone.utc)
                check_out_dt = datetime.combine(s.session_date, s.end_time).replace(tzinfo=timezone.utc)
                plist = parts_by_session.get(s.id, [])

                history.append({
                    "id": str(s.id),
                    "check_in_time": check_in_dt.isoformat(),
                    "check_out_time": check_out_dt.isoformat(),
                    "visit_type": "training",
                    "method": "training",
                    "participants_count": len(plist),
                    "clients": [
                        f"{p.client.first_name} {p.client.last_name}".strip()
                        for p in plist
                        if p.client
                    ],
                })

            return {"history": history}
    else:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    history = []
    for visit in visits:
        item = {
            "id": str(visit.id),
            "check_in_time": visit.check_in_time.isoformat() if visit.check_in_time else None,
            "check_out_time": visit.check_out_time.isoformat() if visit.check_out_time else None,
            "visit_type": visit.visit_type,
            "method": "training" if visit.visit_type == "training" else "manual"
        }
        # Для тренера полезно видеть, кто был на занятии
        if current_user.role == UserRole.TRAINER and visit.client:
            item["client_name"] = f"{visit.client.first_name} {visit.client.last_name}".strip()
        history.append(item)
    
    return {"history": history}

