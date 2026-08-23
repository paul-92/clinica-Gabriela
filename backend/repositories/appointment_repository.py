from datetime import date, datetime, time

from backend.models.appointment import Appointment
from backend.repositories.base_repository import BaseRepository


class AppointmentRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Appointment)

    def list_filtered(self, target_date=None, psychologist_id=None):
        query = self.db.query(Appointment)
        if target_date:
            start = datetime.combine(target_date, time.min)
            end = datetime.combine(target_date, time.max)
            query = query.filter(Appointment.scheduled_at.between(start, end))
        if psychologist_id:
            query = query.filter(Appointment.psychologist_id == psychologist_id)
        return query.order_by(Appointment.scheduled_at).all()

    def today(self):
        return self.list_filtered(date.today())
