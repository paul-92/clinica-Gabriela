from app.controllers.finance_controller import FinanceController, format_cents


def build_monthly_finance_report(api_client):
    summary = FinanceController(api_client).summary()
    return (
        f"Relatorio financeiro - caixa [{summary['start']}, {summary['end']})\n"
        f"Recebido em caixa: {format_cents(summary['income_cents'])}\n"
        f"Despesas de caixa: {format_cents(summary['expense_cents'])}\n"
        f"Saldo de caixa: {format_cents(summary['balance_cents'])}\n"
    )
