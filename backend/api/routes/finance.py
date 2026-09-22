from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from sqlalchemy.orm import Session

from backend.api.versioning import parse_if_match
from backend.database.session import get_db
from backend.schemas.finance import (
    ExpenseAction,
    ExpenseCategoryCreate,
    ExpenseCategoryRead,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    ExpenseRead,
    FinanceSummary,
    FinancialEventRead,
    PaymentAction,
    PaymentCreate,
    PaymentRead,
    PaymentSettlement,
    PaymentUpdate,
)
from backend.services.finance_service import FinanceService
from backend.api.routes.auth import get_current_user


router = APIRouter(prefix="/finance", tags=["finance"], dependencies=[Depends(get_current_user)])


def _required_version(if_match):
    version = parse_if_match(if_match)
    if version is None:
        raise HTTPException(428, "If-Match obrigatorio.")
    return version


@router.get("/summary", response_model=FinanceSummary)
def finance_summary(
    start: date,
    end: date,
    regime: str = Query("cash", pattern="^(cash|accrual)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FinanceService(db).summary(start, end, regime, current_user)


@router.get("/payments", response_model=list[PaymentRead])
def list_payments(
    start: date,
    end: date,
    regime: str = Query("cash", pattern="^(cash|accrual)$"),
    status: str | None = None,
    patient_id: int | None = None,
    reference_date: date | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FinanceService(db).list_payments(start, end, regime, status, patient_id, reference_date, current_user)


@router.post("/payments", response_model=PaymentRead, status_code=201)
def create_payment(payload: PaymentCreate, response: Response, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = FinanceService(db).create_payment(payload.model_dump(), current_user)
    response.headers["ETag"] = f'"{item["version"]}"'
    return item


@router.get("/payments/{payment_id}", response_model=PaymentRead)
def get_payment(payment_id: int, response: Response, reference_date: date | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = FinanceService(db).get_payment(payment_id, reference_date, current_user)
    response.headers["ETag"] = f'"{item["version"]}"'
    return item


@router.patch("/payments/{payment_id}", response_model=PaymentRead)
def update_payment(payment_id: int, payload: PaymentUpdate, response: Response, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(422, "Alteracao financeira vazia.")
    item = FinanceService(db).update_payment(payment_id, data, _required_version(if_match), current_user)
    response.headers["ETag"] = f'"{item["version"]}"'
    return item


@router.post("/payments/{payment_id}/pay", response_model=PaymentRead)
def register_payment(payment_id: int, payload: PaymentSettlement, response: Response, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = FinanceService(db).register_payment(payment_id, payload.model_dump(), _required_version(if_match), current_user)
    response.headers["ETag"] = f'"{item["version"]}"'
    return item


@router.post("/payments/{payment_id}/cancel", response_model=PaymentRead)
def cancel_payment(payment_id: int, payload: PaymentAction, response: Response, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = FinanceService(db).cancel_payment(payment_id, payload.reason, _required_version(if_match), current_user)
    response.headers["ETag"] = f'"{item["version"]}"'
    return item


@router.post("/payments/{payment_id}/reverse", response_model=PaymentRead)
def reverse_payment(payment_id: int, payload: PaymentAction, response: Response, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = FinanceService(db).reverse_payment(payment_id, payload.reason, _required_version(if_match), current_user)
    response.headers["ETag"] = f'"{item["version"]}"'
    return item


@router.get("/expenses", response_model=list[ExpenseRead])
def list_expenses(
    start: date,
    end: date,
    regime: str = Query("cash", pattern="^(cash|accrual)$"),
    status: str | None = None,
    category_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FinanceService(db).list_expenses(start, end, regime, status, category_id, current_user)


@router.post("/expenses", response_model=ExpenseRead, status_code=201)
def create_expense(payload: ExpenseCreate, response: Response, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = FinanceService(db).create_expense(payload.model_dump(), current_user)
    response.headers["ETag"] = f'"{item["version"]}"'
    return item


@router.post("/expenses/{expense_id}/cancel", response_model=ExpenseRead)
def cancel_expense(expense_id: int, payload: ExpenseAction, response: Response, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = FinanceService(db).cancel_expense(expense_id, payload.reason, _required_version(if_match), current_user)
    response.headers["ETag"] = f'"{item["version"]}"'
    return item


@router.get("/categories", response_model=list[ExpenseCategoryRead])
def list_categories(include_inactive: bool = False, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return FinanceService(db).list_categories(include_inactive, current_user)


@router.post("/categories", response_model=ExpenseCategoryRead, status_code=201)
def create_category(payload: ExpenseCategoryCreate, response: Response, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = FinanceService(db).create_category(payload.model_dump(), current_user)
    response.headers["ETag"] = f'"{item.version}"'
    return item


@router.patch("/categories/{category_id}", response_model=ExpenseCategoryRead)
def update_category(category_id: int, payload: ExpenseCategoryUpdate, response: Response, if_match: str | None = Header(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(422, "Alteracao de categoria vazia.")
    item = FinanceService(db).update_category(category_id, data, _required_version(if_match), current_user)
    response.headers["ETag"] = f'"{item.version}"'
    return item


@router.get("/events/{resource_type}/{resource_id}", response_model=list[FinancialEventRead])
def list_events(resource_type: str, resource_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return FinanceService(db).list_events(resource_type, resource_id, current_user)
