from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import List
from models import (
    EmployeeExpensesResponse, ErrorResponse, Expense,
    EmployeeApprovalsResponse, Approval,
    EmployeePaymentsResponse, Payment,
    VendorSpendResponse, VendorSpend,
)
from database import db
from ollama_service import ollama_service
from emb_index import search_facts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Knowledge Graph API",
    description="API for querying Neo4j knowledge graph with Ollama integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _question_tokens(q: str) -> List[str]:
    import re
    return [t for t in re.findall(r"[A-Za-z0-9_]+", (q or "").lower()) if len(t) > 1][:8]

def _try_answer_structured(question: str, context: dict) -> str | None:
    """Lightweight deterministic extractor over context arrays.
    Covers common fact queries without invoking the LLM.
    - expense date for vendor X
    - largest expense amount for vendor X
    - payment status/date for report R
    Returns a concise string or None if not handled.
    """
    import re
    q = (question or "").lower()
    expenses = context.get("expenses") or []
    payments = context.get("payments") or []
    approvals = context.get("approvals") or []
    vendors_rows = context.get("vendors") or []

    def _norm(s: str) -> str:
        return (str(s or "").strip().lower())

    # Resolve vendor/entity names from question by substring match
    def _resolve_vendor() -> str | None:
        names = set()
        for e in expenses:
            v = e.get("vendor")
            if v:
                names.add(_norm(v))
        for v in vendors_rows:
            n = v.get("vendor")
            if n:
                names.add(_norm(n))
        cand = [n for n in names if n and n in q]
        if not cand:
            return None
        cand.sort(key=len, reverse=True)
        return cand[0]

    # Extract simple time windows from question (year or mm/yyyy)
    def _extract_year() -> str | None:
        m = re.search(r"\b(20\d{2})\b", q)
        return m.group(1) if m else None

    def _extract_month_year() -> tuple[str | None, str | None]:
        m = re.search(r"\b(\d{1,2})[\-/](20\d{2})\b", q)
        if m:
            return (m.group(1), m.group(2))
        return (None, None)

    def _parse_top_n(default_n: int = 5) -> int:
        m = re.search(r"top\s+(\d{1,2})", q)
        if m:
            try:
                return max(1, int(m.group(1)))
            except Exception:
                return default_n
        return default_n
    # 1) Expense date for vendor X
    if "expense" in q and "date" in q and ("vendor" in q or any("vendor" in k for k in q.split())):
        # guess vendor token(s) by checking substrings against vendors present in context
        vendors = {str(e.get("vendor", "")).lower(): e for e in expenses if e.get("vendor")}
        for v in sorted(vendors.keys(), key=len, reverse=True):
            if v and v in q:
                # choose most recent expense for that vendor
                vendor_rows = [e for e in expenses if str(e.get("vendor", "")).lower() == v]
                if vendor_rows:
                    # pick by date if available, else highest amount
                    def _date_key(r):
                        return str(r.get("expense_date") or "")
                    row = sorted(vendor_rows, key=_date_key, reverse=True)[0]
                    if row.get("expense_date"):
                        return str(row.get("expense_date"))
        # fallback: if only one expense in context, return its date
        if len(expenses) == 1 and expenses[0].get("expense_date"):
            return str(expenses[0].get("expense_date"))

    # 2) Largest expense amount for vendor X
    if ("largest" in q or "highest" in q or "max" in q) and "expense" in q and ("amount" in q or "how much" in q):
        if expenses:
            top = max(expenses, key=lambda r: float(r.get("amount") or 0.0))
            if top.get("amount") is not None:
                return str(top.get("amount"))

    # 2b) Largest expenses and who approved them (top 3)
    if ("largest" in q or "highest" in q or "top" in q) and "expense" in q and ("approve" in q or "approved" in q):
        if expenses:
            # take top 3 expenses
            topn = sorted(expenses, key=lambda r: float(r.get("amount") or 0.0), reverse=True)[:3]
            # build approver list per report
            rid_to_approvers: dict[str, list[str]] = {}
            for a in approvals:
                rid = str(a.get("report_id"))
                who = a.get("approver_name") or a.get("approver_id")
                if rid:
                    rid_to_approvers.setdefault(rid, [])
                    if who and who not in rid_to_approvers[rid]:
                        rid_to_approvers[rid].append(str(who))
            lines = []
            for r in topn:
                rid = str(r.get("report_id"))
                amt = r.get("amount")
                appr = ", ".join(rid_to_approvers.get(rid, [])) or "unknown"
                lines.append(f"report {rid}: {amt} approved by {appr}")
            if lines:
                return "; ".join(lines)

    # 3) Totals over time window and/or vendor
    if ("total" in q or "sum" in q) and ("spend" in q or "amount" in q or "expenses" in q):
        if expenses:
            target_vendor = _resolve_vendor()
            year = _extract_year()
            mm, yyyy = _extract_month_year()
            rows = expenses
            if target_vendor:
                rows = [e for e in rows if _norm(e.get("vendor")) == target_vendor]
            if yyyy and mm:
                rows = [e for e in rows if _norm(e.get("expense_date")).endswith(f"{yyyy}") and (f"/{mm}/" in _norm(e.get("expense_date")) or _norm(e.get("expense_date")).startswith(f"{mm}/") )]
            elif year:
                rows = [e for e in rows if year in _norm(e.get("expense_date"))]
            total = sum(float(e.get("amount") or 0.0) for e in rows)
            return str(total)

    # 4) Top N vendors (optionally by category)
    if ("top" in q and "vendor" in q):
        n = _parse_top_n(5)
        category = None
        m = re.search(r"category\s+([A-Za-z0-9_\-]+)", q)
        if m:
            category = _norm(m.group(1))
        agg: dict[str, float] = {}
        for e in expenses:
            if category and category != _norm(e.get("category")):
                continue
            v = _norm(e.get("vendor"))
            if not v:
                continue
            agg[v] = agg.get(v, 0.0) + float(e.get("amount") or 0.0)
        if agg:
            top = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)[:n]
            return "; ".join([f"{name}: {amt}" for name, amt in top])

    # 3) Payment status/date for report R
    if "payment" in q and ("status" in q or "date" in q or "paid" in q):
        # detect explicit report id pattern in question
        import re
        rid = None
        m = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", q)
        if m:
            rid = m.group(0)
        if payments:
            rows = payments if rid is None else [p for p in payments if str(p.get("report_id")) == rid]
            if rows:
                row = sorted(rows, key=lambda r: str(r.get("payment_date") or ""), reverse=True)[0]
                if "status" in q and row.get("payment_status"):
                    return str(row.get("payment_status"))
                if "date" in q and row.get("payment_date"):
                    return str(row.get("payment_date"))
    return None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Knowledge Graph API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check including database connectivity"""
    try:
        # Test Neo4j connection
        with db.get_session() as session:
            result = session.run("RETURN 1 as test")
            neo4j_status = "connected" if result.single() else "disconnected"
    except Exception as e:
        neo4j_status = f"error: {str(e)}"
    
    return {
        "api": "healthy",
        "neo4j": neo4j_status,
        "ollama": "available"  # We'll add actual Ollama health check later
    }

@app.get("/employee/{employee_id}/expenses", response_model=EmployeeExpensesResponse)
async def get_employee_expenses(employee_id: str):
    """
    Get all expenses for a specific employee
    
    Args:
        employee_id: The ID of the employee
        
    Returns:
        EmployeeExpensesResponse with expenses, total amount, and AI-generated summary
    """
    try:
        # Cypher query to get employee expenses
        cypher_query = """
        MATCH (e:Employee {id: $employee_id})-[:SUBMITTED]->(:Report)-[:HAS_ENTRY]->(ex:Expense)
        RETURN ex.id AS expense_id,
               toFloat(ex.amount) AS amount,
               coalesce(ex.spend_category, ex.type_name, ex.type_code, 'Unknown') AS category
        ORDER BY amount DESC
        """
        
        # Execute query
        raw_results = db.execute_query(cypher_query, {"employee_id": employee_id})
        
        if not raw_results:
            raise HTTPException(
                status_code=404, 
                detail=f"No expenses found for employee {employee_id}"
            )
        
        # Convert to Expense objects
        expenses = [
            Expense(
                expense_id=row["expense_id"],
                amount=float(row["amount"]),
                category=row["category"]
            )
            for row in raw_results
        ]
        
        # Calculate total amount
        total_amount = sum(expense.amount for expense in expenses)
        
        # Generate AI summary
        summary = ollama_service.generate_summary(
            raw_results, 
            f"expense data for employee {employee_id}"
        )
        
        return EmployeeExpensesResponse(
            employee_id=employee_id,
            expenses=expenses,
            total_amount=total_amount,
            summary=summary,
            raw_data=raw_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting expenses for employee {employee_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/employees")
async def list_employees():
    """Get list of all employees in the database"""
    try:
        cypher_query = """
        MATCH (e:Employee)
        RETURN e.id as employee_id, e.name as name
        ORDER BY e.name
        """
        
        results = db.execute_query(cypher_query)
        return {"employees": results}
        
    except Exception as e:
        logger.error(f"Error listing employees: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/expenses/categories")
async def get_expense_categories():
    """Get all unique expense categories"""
    try:
        cypher_query = """
        MATCH (ex:Expense)
        RETURN DISTINCT ex.category as category
        ORDER BY category
        """
        
        results = db.execute_query(cypher_query)
        categories = [row["category"] for row in results]
        
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"Error getting expense categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# ------------------------------
# New endpoints
# ------------------------------

@app.get("/qa")
async def qa_global(q: str = Query(..., description="Your question over the whole graph"), limit: int = 50, mode: str = Query("auto", description="precise|conversational|auto")):
    """Answer a natural-language question across the entire knowledge graph
    (reports, expenses, approvals, payments, vendors) without scoping to an employee.
    """
    try:
        tokens = _question_tokens(q)

        token_pred = " OR ".join([
            f"toLower(coalesce(x.description,'')) CONTAINS '{t}' OR toLower(coalesce(x.type_name,'')) CONTAINS '{t}' OR toLower(coalesce(x.type_code,'')) CONTAINS '{t}'"
            for t in tokens
        ]) if tokens else ""

        vendor_pred = " OR ".join([
            f"toLower(coalesce(v.name,'')) CONTAINS '{t}'" for t in tokens
        ]) if tokens else ""

        appr_pred = " OR ".join([
            f"toLower(coalesce(a.step_name,'')) CONTAINS '{t}' OR toLower(coalesce(a.decision,'')) CONTAINS '{t}'"
            for t in tokens
        ]) if tokens else ""

        pay_pred = " OR ".join([
            f"toLower(coalesce(p.method,'')) CONTAINS '{t}' OR toLower(coalesce(p.status,'')) CONTAINS '{t}'"
            for t in tokens
        ]) if tokens else ""

        expenses_q = f"""
        MATCH (r:Report)-[:HAS_ENTRY]->(x:Expense)
        OPTIONAL MATCH (x)-[:PAID_TO]->(v:Vendor)
        {"WHERE " + token_pred if token_pred else ""}
        RETURN r.id AS report_id,
               coalesce(x.spend_category, x.type_name, x.type_code, 'Unknown') AS category,
               toFloat(x.amount) AS amount,
               coalesce(v.name, x.vendor, 'Unknown') AS vendor,
               x.currency AS currency,
               x.transaction_date AS expense_date
        ORDER BY expense_date DESC, amount DESC
        LIMIT $limit
        """

        approvals_q = f"""
        MATCH (r:Report)-[a:APPROVED_BY]->(approver:Employee)
        {"WHERE " + appr_pred if appr_pred else ""}
        RETURN r.id AS report_id, toFloat(a.step) AS step, a.step_name AS step_name,
               a.decision AS decision, a.at AS decided_at,
               approver.id AS approver_id, approver.name AS approver_name
        ORDER BY r.id, step
        LIMIT $limit
        """

        payments_q = f"""
        MATCH (r:Report)-[:SETTLED_BY]->(p:Payment)
        {"WHERE " + pay_pred if pay_pred else ""}
        RETURN r.id AS report_id, p.id AS payment_id, p.method AS payment_method,
               p.payment_date AS payment_date, toFloat(p.total_amount) AS total_amount,
               toFloat(p.company_paid) AS company_paid_amount, toFloat(p.employee_due) AS employee_due_amount,
               p.status AS payment_status
        ORDER BY payment_date DESC
        LIMIT $limit
        """

        vendors_q = f"""
        MATCH (x:Expense)-[:PAID_TO]->(v:Vendor)
        {"WHERE " + vendor_pred if vendor_pred else ""}
        RETURN v.name AS vendor, sum(toFloat(x.amount)) AS spend
        ORDER BY spend DESC
        LIMIT 25
        """

        expenses = db.execute_query(expenses_q, {"limit": limit}) or []
        approvals = db.execute_query(approvals_q, {"limit": limit}) or []
        payments = db.execute_query(payments_q, {"limit": limit}) or []
        vendors = db.execute_query(vendors_q, {}) or []

        # Semantic facts via embeddings
        facts = []
        try:
            # Retrieve more, then compact
            raw_facts = search_facts(q, k=80)
            def compact_facts(items, max_k=24):
                seen = set()
                out = []
                for f in items:
                    txt = (f.get("text") or "").strip()
                    if not txt:
                        continue
                    key = txt.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    # keep only small meta to reduce context size
                    out.append({"text": txt, "kind": f.get("kind"), "meta": {k: f["meta"][k] for k in (f.get("meta") or {}) if k in ("report_id","payment_id","vendor","amount","expense_date")}})
                    if len(out) >= max_k:
                        break
                return out
            facts = compact_facts(raw_facts, max_k=24)
        except Exception as _e:
            facts = []

        context = {
            "scope": "global",
            "question_tokens": tokens,
            "expenses": expenses,
            "approvals": approvals,
            "payments": payments,
            "vendors": vendors,
            "facts": facts,
        }
        # deterministic attempt first
        det = _try_answer_structured(q, context)
        if mode == "precise":
            answer = det if det is not None else "I don't know from the available structured data."
        elif mode == "conversational":
            answer = ollama_service.answer_question(q, context)
        else:
            answer = det if det is not None else ollama_service.answer_question(q, context)
        return {"question": q, "answer": answer, "context": context}
    except Exception as e:
        logger.error(f"Global QA error: {e}")
        raise HTTPException(status_code=500, detail="QA failed")

@app.get("/employee/{employee_id}/approvals", response_model=EmployeeApprovalsResponse)
async def get_employee_approvals(employee_id: str):
    """Approvals across all reports submitted by the employee."""
    try:
        cypher = """
        MATCH (e:Employee {id: $employee_id})-[:SUBMITTED]->(r:Report)
        MATCH (r)-[a:APPROVED_BY]->(u:Employee)
        RETURN r.id AS report_id,
               toFloat(a.step) AS step,
               a.step_name AS step_name,
               a.decision AS decision,
               a.at AS decided_at,
               u.id AS approver_id,
               u.name AS approver_name
        ORDER BY report_id, step
        """
        rows = db.execute_query(cypher, {"employee_id": employee_id})
        if not rows:
            raise HTTPException(status_code=404, detail=f"No approvals found for employee {employee_id}")

        approvals = [
            Approval(
                report_id=r["report_id"],
                step=r.get("step", 0.0),
                step_name=r.get("step_name"),
                decision=r.get("decision"),
                decided_at=r.get("decided_at"),
                approver_id=r.get("approver_id"),
                approver_name=r.get("approver_name"),
            ) for r in rows
        ]

        summary = ollama_service.generate_summary(rows, f"approvals for employee {employee_id}")
        return EmployeeApprovalsResponse(
            employee_id=employee_id,
            approvals=approvals,
            summary=summary,
            raw_data=rows,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting approvals for employee {employee_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/employee/{employee_id}/payments", response_model=EmployeePaymentsResponse)
async def get_employee_payments(employee_id: str):
    """Payments linked to reports submitted by the employee."""
    try:
        cypher = """
        MATCH (e:Employee {id: $employee_id})-[:SUBMITTED]->(r:Report)-[:SETTLED_BY]->(p:Payment)
        RETURN r.id AS report_id,
               p.id AS payment_id,
               p.method AS method,
               p.status AS status,
               p.payment_date AS payment_date,
               toFloat(p.total_amount) AS total_amount,
               toFloat(p.company_paid) AS company_paid,
               toFloat(p.employee_due) AS employee_due
        ORDER BY payment_date DESC
        """
        rows = db.execute_query(cypher, {"employee_id": employee_id})
        if not rows:
            raise HTTPException(status_code=404, detail=f"No payments found for employee {employee_id}")

        payments = [
            Payment(
                report_id=r["report_id"],
                payment_id=r["payment_id"],
                method=r.get("method"),
                status=r.get("status"),
                payment_date=r.get("payment_date"),
                total_amount=float(r.get("total_amount") or 0.0),
                company_paid=float(r.get("company_paid") or 0.0),
                employee_due=float(r.get("employee_due") or 0.0),
            ) for r in rows
        ]
        total_amount = sum(p.total_amount or 0.0 for p in payments)
        summary = ollama_service.generate_summary(rows, f"payments for employee {employee_id}")
        return EmployeePaymentsResponse(
            employee_id=employee_id,
            payments=payments,
            total_amount=total_amount,
            summary=summary,
            raw_data=rows,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payments for employee {employee_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/vendors/top", response_model=VendorSpendResponse)
async def get_top_vendors(limit: int = 10):
    """Top vendors by spend across all expenses."""
    try:
        cypher = """
        MATCH (x:Expense)-[:PAID_TO]->(v:Vendor)
        RETURN v.name AS vendor, sum(toFloat(x.amount)) AS spend
        ORDER BY spend DESC
        LIMIT $limit
        """
        rows = db.execute_query(cypher, {"limit": limit})
        items = [VendorSpend(vendor=r["vendor"], spend=float(r.get("spend") or 0.0)) for r in rows]
        summary = ollama_service.generate_summary(rows, f"top {limit} vendors by spend")
        return VendorSpendResponse(items=items, summary=summary, raw_data=rows)
    except Exception as e:
        logger.error(f"Error getting top vendors: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/qa/employee/{employee_id}")
async def qa_employee(employee_id: str, q: str = Query(..., description="Your question")):
    """Answer a natural-language question about a given employee by
    aggregating expenses, approvals and payments, then asking the local LLM.
    """
    try:
        expenses_q = """
        MATCH (e:Employee {id: $employee_id})-[:SUBMITTED]->(r:Report)-[:HAS_ENTRY]->(x:Expense)
        OPTIONAL MATCH (x)-[:PAID_TO]->(v:Vendor)
        RETURN r.id AS report_id,
               coalesce(x.spend_category, x.type_name, x.type_code, 'Unknown') AS category,
               toFloat(x.amount) AS amount,
               coalesce(v.name, x.vendor, 'Unknown') AS vendor,
               x.currency AS currency,
               x.transaction_date AS expense_date
        ORDER BY expense_date DESC
        """

        approvals_q = """
        MATCH (e:Employee {id: $employee_id})-[:SUBMITTED]->(r:Report)-[a:APPROVED_BY]->(approver:Employee)
        RETURN r.id AS report_id, a.step AS step, a.step_name AS step_name,
               a.decision AS decision, a.at AS decided_at,
               approver.id AS approver_id, approver.name AS approver_name
        ORDER BY r.id, a.step
        """

        payments_q = """
        MATCH (e:Employee {id: $employee_id})-[:SUBMITTED]->(r:Report)-[:SETTLED_BY]->(p:Payment)
        RETURN r.id AS report_id, p.id AS payment_id, p.method AS payment_method,
               p.payment_date AS payment_date, p.total_amount AS total_amount,
               p.company_paid AS company_paid_amount, p.employee_due AS employee_due_amount,
               p.status AS payment_status
        ORDER BY p.payment_date DESC
        """

        expenses = db.execute_query(expenses_q, {"employee_id": employee_id}) or []
        approvals = db.execute_query(approvals_q, {"employee_id": employee_id}) or []
        payments = db.execute_query(payments_q, {"employee_id": employee_id}) or []

        context = {
            "employee_id": employee_id,
            "expenses": expenses,
            "approvals": approvals,
            "payments": payments,
        }

        answer = ollama_service.answer_question(q, context)
        return {"employee_id": employee_id, "question": q, "answer": answer, "context": context}
    except Exception as e:
        logger.error(f"QA error for {employee_id}: {e}")
        raise HTTPException(status_code=500, detail="QA failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
