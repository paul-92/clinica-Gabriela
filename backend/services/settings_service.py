from backend.repositories.settings_repository import SettingsRepository


class SettingsService:
    def __init__(self, db):
        self.repository = SettingsRepository(db)

    def get_settings(self):
        return self.repository.get_current()

    def update_settings(self, data):
        settings = self.get_settings()
        return self.repository.update(settings, data)
