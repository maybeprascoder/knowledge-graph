"""
Sample data creation script for Neo4j database
Run this to populate the database with sample employee and expense data
"""

from database import db
import logging

logger = logging.getLogger(__name__)

def create_sample_data():
    """Create sample data in Neo4j database"""
    
    # Clear existing data
    clear_query = "MATCH (n) DETACH DELETE n"
    db.execute_query(clear_query)
    logger.info("Cleared existing data")
    
    # Create sample employees
    employees_data = [
        {"id": "EMP001", "name": "John Smith", "department": "Engineering"},
        {"id": "EMP002", "name": "Sarah Johnson", "department": "Marketing"},
        {"id": "EMP003", "name": "Mike Wilson", "department": "Sales"},
        {"id": "EMP004", "name": "Lisa Brown", "department": "HR"},
        {"id": "EMP005", "name": "David Lee", "department": "Finance"}
    ]
    
    for emp in employees_data:
        create_employee_query = """
        CREATE (e:Employee {
            id: $id,
            name: $name,
            department: $department
        })
        """
        db.execute_query(create_employee_query, emp)
    
    logger.info(f"Created {len(employees_data)} employees")
    
    # Create sample reports
    reports_data = [
        {"id": "RPT001", "employee_id": "EMP001", "month": "2024-01", "status": "approved"},
        {"id": "RPT002", "employee_id": "EMP001", "month": "2024-02", "status": "approved"},
        {"id": "RPT003", "employee_id": "EMP002", "month": "2024-01", "status": "pending"},
        {"id": "RPT004", "employee_id": "EMP003", "month": "2024-01", "status": "approved"},
        {"id": "RPT005", "employee_id": "EMP004", "month": "2024-02", "status": "approved"}
    ]
    
    for rpt in reports_data:
        create_report_query = """
        MATCH (e:Employee {id: $employee_id})
        CREATE (r:Report {
            id: $id,
            month: $month,
            status: $status
        })
        CREATE (e)-[:SUBMITTED]->(r)
        """
        db.execute_query(create_report_query, rpt)
    
    logger.info(f"Created {len(reports_data)} reports")
    
    # Create sample expenses
    expenses_data = [
        # EMP001 expenses
        {"id": "EXP001", "amount": 150.00, "category": "Travel", "report_id": "RPT001"},
        {"id": "EXP002", "amount": 75.50, "category": "Meals", "report_id": "RPT001"},
        {"id": "EXP003", "amount": 200.00, "category": "Accommodation", "report_id": "RPT001"},
        {"id": "EXP004", "amount": 45.00, "category": "Transportation", "report_id": "RPT002"},
        {"id": "EXP005", "amount": 120.00, "category": "Meals", "report_id": "RPT002"},
        
        # EMP002 expenses
        {"id": "EXP006", "amount": 300.00, "category": "Marketing", "report_id": "RPT003"},
        {"id": "EXP007", "amount": 85.00, "category": "Meals", "report_id": "RPT003"},
        
        # EMP003 expenses
        {"id": "EXP008", "amount": 500.00, "category": "Client Entertainment", "report_id": "RPT004"},
        {"id": "EXP009", "amount": 100.00, "category": "Travel", "report_id": "RPT004"},
        
        # EMP004 expenses
        {"id": "EXP010", "amount": 60.00, "category": "Training", "report_id": "RPT005"},
        {"id": "EXP011", "amount": 25.00, "category": "Office Supplies", "report_id": "RPT005"}
    ]
    
    for exp in expenses_data:
        create_expense_query = """
        MATCH (r:Report {id: $report_id})
        CREATE (ex:Expense {
            id: $id,
            amount: $amount,
            category: $category
        })
        CREATE (r)-[:HAS_ENTRY]->(ex)
        """
        db.execute_query(create_expense_query, exp)
    
    logger.info(f"Created {len(expenses_data)} expenses")
    
    # Create some additional relationships for richer data
    # Add manager relationships
    manager_relationships = [
        ("EMP001", "EMP002"),  # John manages Sarah
        ("EMP001", "EMP003"),  # John manages Mike
        ("EMP004", "EMP005")   # Lisa manages David
    ]
    
    for manager_id, employee_id in manager_relationships:
        create_manager_query = """
        MATCH (m:Employee {id: $manager_id}), (e:Employee {id: $employee_id})
        CREATE (e)-[:REPORTS_TO]->(m)
        """
        db.execute_query(create_manager_query, {
            "manager_id": manager_id,
            "employee_id": employee_id
        })
    
    logger.info("Created manager relationships")
    
    print("✅ Sample data created successfully!")
    print(f"   - {len(employees_data)} employees")
    print(f"   - {len(reports_data)} reports") 
    print(f"   - {len(expenses_data)} expenses")
    print(f"   - Manager relationships created")

if __name__ == "__main__":
    create_sample_data()
