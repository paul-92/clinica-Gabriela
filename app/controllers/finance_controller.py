from datetime import date, timedelta


class FinanceController:
    def __init__(self, api_client):
        self.api_client = api_client

    def summary(self, start=None, end=None, regime="cash"):
        today = date.today()
        start = start or today.replace(day=1)
        end = end or (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return self.api_client.get(
            f"/finance/summary?start={start.isoformat()}&end={end.isoformat()}&regime={regime}"
        )


def format_cents(value):
    cents = int(value)
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}R$ {cents // 100:,},{cents % 100:02d}".replace(",", "X").replace(".", ",").replace("X", ".")
