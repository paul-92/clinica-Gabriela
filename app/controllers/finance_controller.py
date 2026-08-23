from app.database.session import get_session
from app.services.finance_service import FinanceService


class FinanceController:
    def summary(self):
        with get_session() as session:
            return FinanceService(session).monthly_summary()
