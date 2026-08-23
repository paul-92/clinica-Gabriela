from datetime import date, datetime, time

from app.models.appointment import Appointment
from app.repositories.base_repository import BaseRepository


class AppointmentRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, Appointment)

    def by_day(self, target_date=None, psychologist_id=None):
        target_date = target_date or date.today()
        start = datetime.combine(target_date, time.min)
        end = datetime.combine(target_date, time.max)
        query = self.session.query(Appointment).filter(Appointment.scheduled_at.between(start, end))
        if psychologist_id:
            query = query.filter(Appointment.psychologist_id == psychologist_id)
        return query.order_by(Appointment.scheduled_at).all()
