from backend.models.settings import ClinicSettings
from backend.repositories.base_repository import BaseRepository


class SettingsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, ClinicSettings)

    def get_current(self):
        settings = self.db.query(ClinicSettings).first()
        if settings:
            return settings
        return self.create({})
