from pydantic import BaseModel
from typing import List, Optional

class Expense(BaseModel):
    expense_id: str
    amount: float
    category: str

class EmployeeExpensesResponse(BaseModel):
    employee_id: str
    expenses: List[Expense]
    total_amount: float
    summary: str
    raw_data: List[dict]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# New schemas for approvals, payments, and vendor spend
class Approval(BaseModel):
    report_id: str
    step: float
    step_name: Optional[str] = None
    decision: Optional[str] = None
    decided_at: Optional[str] = None
    approver_id: Optional[str] = None
    approver_name: Optional[str] = None

class EmployeeApprovalsResponse(BaseModel):
    employee_id: str
    approvals: List[Approval]
    summary: str
    raw_data: List[dict]

class Payment(BaseModel):
    report_id: str
    payment_id: str
    method: Optional[str] = None
    status: Optional[str] = None
    payment_date: Optional[str] = None
    total_amount: Optional[float] = None
    company_paid: Optional[float] = None
    employee_due: Optional[float] = None

class EmployeePaymentsResponse(BaseModel):
    employee_id: str
    payments: List[Payment]
    total_amount: float
    summary: str
    raw_data: List[dict]

class VendorSpend(BaseModel):
    vendor: str
    spend: float

class VendorSpendResponse(BaseModel):
    items: List[VendorSpend]
    summary: str
    raw_data: List[dict]