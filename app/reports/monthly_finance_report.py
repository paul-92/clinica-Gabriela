from app.controllers.finance_controller import FinanceController


def build_monthly_finance_report():
    summary = FinanceController().summary()
    return (
        "Relatorio financeiro mensal\n"
        f"Recebido: R$ {summary['paid']:.2f}\n"
        f"Pendente: R$ {summary['pending']:.2f}\n"
        f"Despesas: R$ {summary['expenses']:.2f}\n"
        f"Saldo: R$ {summary['balance']:.2f}\n"
    )
