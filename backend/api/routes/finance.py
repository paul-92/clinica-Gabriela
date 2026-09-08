from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.finance import ExpenseCreate, ExpenseRead, FinanceSummary, PaymentCreate, PaymentRead
from backend.services.finance_service import FinanceService
from backend.api.routes.auth import get_current_user


router = APIRouter(prefix="/finance", tags=["finance"], dependencies=[Depends(get_current_user)])


@router.get("/summary", response_model=FinanceSummary)
def finance_summary(db: Session = Depends(get_db)):
    return FinanceService(db).summary()


@router.get("/payments", response_model=list[PaymentRead])
def list_payments(db: Session = Depends(get_db)):
    return FinanceService(db).list_payments()


@router.post("/payments", response_model=PaymentRead, status_code=201)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    return FinanceService(db).create_payment(payload.model_dump())


@router.get("/expenses", response_model=list[ExpenseRead])
def list_expenses(db: Session = Depends(get_db)):
    return FinanceService(db).list_expenses()


@router.post("/expenses", response_model=ExpenseRead, status_code=201)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    return FinanceService(db).create_expense(payload.model_dump())
