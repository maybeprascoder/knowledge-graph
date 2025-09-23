from fastapi import FastAPI, HTTPException, Depends
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
