"""
API для разовых записей расписания (по конкретной дате)
"""
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import (
    User, UserRole,
    GymZone, ZonePass, Visit,
    TrainingSession, TrainingSessionParticipant,
)
from scr.core.dependencies import get_current_active_user, require_role
from scr.schemas.training_session import TrainingSessionCreate, TrainingSessionResponse


router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.post("", response_model=TrainingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_training_session(
    payload: TrainingSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER))
):
    """Тренер создаёт запись расписания на конкретную дату"""
    if payload.start_time >= payload.end_time:
        raise HTTPException(status_code=400, detail="Время начала должно быть меньше времени окончания")

    zone = db.query(GymZone).filter(GymZone.id == payload.gym_zone_id, GymZone.is_active == True).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Зал не найден")

    # Проверка пересечений у тренера на эту дату
    overlap = db.query(TrainingSession).filter(
        TrainingSession.trainer_id == current_user.id,
        TrainingSession.session_date == payload.session_date,
        TrainingSession.is_cancelled == False,
        TrainingSession.start_time < payload.end_time,
        TrainingSession.end_time > payload.start_time,
    ).first()
    if overlap:
        raise HTTPException(status_code=409, detail="У тренера уже есть запись в это время")

    session = TrainingSession(
        trainer_id=current_user.id,
        session_date=payload.session_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        gym_zone_id=payload.gym_zone_id,
        is_cancelled=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return TrainingSessionResponse(
        id=session.id,
        session_date=session.session_date,
        start_time=session.start_time,
        end_time=session.end_time,
        gym_zone=session.gym_zone,
        trainer=session.trainer,
        participants_count=0,
        participants=[],
        is_cancelled=False,
        is_completed=False,
    )


@router.get("", response_model=List[TrainingSessionResponse])
async def list_training_sessions(
    session_date: date = Query(..., description="Дата (YYYY-MM-DD)"),
    gym_zone_id: Optional[int] = Query(None, description="ID зала (опционально)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Список записей на дату. Клиент видит все, тренер — только свои."""
    q = db.query(TrainingSession).filter(
        TrainingSession.session_date == session_date,
    )
    if gym_zone_id:
        q = q.filter(TrainingSession.gym_zone_id == gym_zone_id)

    if current_user.role == UserRole.TRAINER:
        q = q.filter(TrainingSession.trainer_id == current_user.id)

    sessions = q.order_by(TrainingSession.start_time.asc()).all()

    # Предзагрузка участников
    session_ids = [s.id for s in sessions]
    parts = []
    if session_ids:
        parts = db.query(TrainingSessionParticipant).filter(TrainingSessionParticipant.session_id.in_(session_ids)).all()

    parts_by_session = {}
    for p in parts:
        parts_by_session.setdefault(p.session_id, []).append(p)

    resp: List[TrainingSessionResponse] = []
    for s in sessions:
        plist = parts_by_session.get(s.id, [])
        participants_count = len(plist)

        if current_user.role == UserRole.TRAINER:
            participants = [p.client for p in plist]
            resp.append(TrainingSessionResponse(
                id=s.id,
                session_date=s.session_date,
                start_time=s.start_time,
                end_time=s.end_time,
                gym_zone=s.gym_zone,
                trainer=s.trainer,
                participants_count=participants_count,
                participants=participants,
                is_cancelled=s.is_cancelled,
                is_completed=s.is_completed,
            ))
        elif current_user.role == UserRole.CLIENT:
            is_signed = any(p.client_id == current_user.id for p in plist)
            resp.append(TrainingSessionResponse(
                id=s.id,
                session_date=s.session_date,
                start_time=s.start_time,
                end_time=s.end_time,
                gym_zone=s.gym_zone,
                trainer=s.trainer,
                participants_count=participants_count,
                is_signed=is_signed,
                is_cancelled=s.is_cancelled,
                is_completed=s.is_completed,
            ))
        else:
            resp.append(TrainingSessionResponse(
                id=s.id,
                session_date=s.session_date,
                start_time=s.start_time,
                end_time=s.end_time,
                gym_zone=s.gym_zone,
                trainer=s.trainer,
                participants_count=participants_count,
                is_cancelled=s.is_cancelled,
                is_completed=s.is_completed,
            ))

    return resp


@router.post("/{session_id}/signup", status_code=status.HTTP_201_CREATED)
async def signup_for_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    """Клиент записывается на запись расписания"""
    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.is_cancelled == False
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    # Проверка дубля
    exists = db.query(TrainingSessionParticipant).filter(
        TrainingSessionParticipant.session_id == session_id,
        TrainingSessionParticipant.client_id == current_user.id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Вы уже записаны на эту тренировку")

    # Проверка наличия абонемента на зал
    if session.gym_zone_id:
        zone_pass = db.query(ZonePass).filter(
            ZonePass.client_id == current_user.id,
            ZonePass.gym_zone_id == session.gym_zone_id
        ).first()
        if not zone_pass or zone_pass.remaining_visits <= 0:
            raise HTTPException(
                status_code=402,
                detail=f"Недостаточно занятий в абонементе для зала '{session.gym_zone.name if session.gym_zone else 'неизвестный'}'. Осталось: {zone_pass.remaining_visits if zone_pass else 0}"
            )

        # Ограничение по вместимости зала (если задано)
        zone = db.query(GymZone).filter(GymZone.id == session.gym_zone_id).first()
        if zone and zone.capacity and zone.capacity > 0:
            cnt = db.query(TrainingSessionParticipant).filter(
                TrainingSessionParticipant.session_id == session_id
            ).count()
            if cnt >= zone.capacity:
                raise HTTPException(status_code=409, detail="В этом зале больше нет мест")

    part = TrainingSessionParticipant(session_id=session_id, client_id=current_user.id)
    db.add(part)
    db.commit()

    return {"status": "ok"}


@router.delete("/{session_id}")
async def cancel_training_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER))
):
    """Тренер отменяет своё занятие"""
    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.trainer_id == current_user.id,
        TrainingSession.is_cancelled == False,
        TrainingSession.is_completed == False
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Занятие не найдено, уже отменено или проведено")

    session.is_cancelled = True
    db.commit()

    return {"status": "ok", "message": "Занятие отменено"}


@router.post("/{session_id}/complete", status_code=status.HTTP_200_OK)
async def complete_training_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER))
):
    """Тренер отмечает занятие как проведенное - списывает занятия у всех участников"""
    # Берем блокировку строки, чтобы исключить двойное проведение при параллельных запросах
    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.trainer_id == current_user.id,
        TrainingSession.is_cancelled == False
    ).with_for_update().first()
    if not session:
        raise HTTPException(status_code=404, detail="Занятие не найдено или уже отменено")

    # Проверяем, не было ли занятие уже проведено
    if session.is_completed:
        raise HTTPException(status_code=400, detail="Занятие уже отмечено как проведенное")

    # Получаем всех участников
    participants = db.query(TrainingSessionParticipant).filter(
        TrainingSessionParticipant.session_id == session_id
    ).all()

    if not participants:
        raise HTTPException(status_code=400, detail="На занятие никто не записан")

    # Списываем занятия у каждого участника и создаем записи в истории посещений
    successful_count = 0
    failed_clients = []

    for participant in participants:
        if session.gym_zone_id:
            # Если уже есть запись посещения по этому занятию для этого клиента — пропускаем (идемпотентность)
            already = db.query(Visit).filter(
                Visit.client_id == participant.client_id,
                Visit.training_session_id == session.id
            ).first()
            if already:
                continue

            zone_pass = db.query(ZonePass).filter(
                ZonePass.client_id == participant.client_id,
                ZonePass.gym_zone_id == session.gym_zone_id
            ).first()
            if zone_pass and zone_pass.remaining_visits > 0:
                zone_pass.remaining_visits -= 1
                successful_count += 1

                # Создаем запись в истории посещений
                check_in_datetime = datetime.combine(session.session_date, session.start_time).replace(tzinfo=timezone.utc)
                check_out_datetime = datetime.combine(session.session_date, session.end_time).replace(tzinfo=timezone.utc)

                visit = Visit(
                    client_id=participant.client_id,
                    trainer_id=session.trainer_id,
                    training_session_id=session.id,
                    visit_type="training",
                    check_in_time=check_in_datetime,
                    check_out_time=check_out_datetime
                )
                db.add(visit)
            else:
                # Если у клиента нет абонемента или занятий, добавляем в список проблемных
                client_name = f"{participant.client.first_name} {participant.client.last_name}"
                failed_clients.append(client_name)

    # Отмечаем занятие как проведенное
    session.is_completed = True
    session.completed_at = datetime.now(timezone.utc)

    db.commit()

    message = f"Занятие проведено. Списано занятий у {successful_count} клиентов."
    if failed_clients:
        message += f" Не удалось списать у: {', '.join(failed_clients)} (недостаточно занятий в абонементе)."

    return {"status": "ok", "message": message, "successful_count": successful_count, "failed_clients": failed_clients}


