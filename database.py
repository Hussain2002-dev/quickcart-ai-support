
import sqlite3


# Connect to the database
def connect_db():
    connection = sqlite3.connect("quickcart.db")
    connection.row_factory = sqlite3.Row
    return connection


# Create database tables and sample orders
def initialize_database():
    connection = connect_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            email TEXT,
            product TEXT NOT NULL,
            status TEXT NOT NULL,
            estimated_delivery TEXT,
            tracking_number TEXT
        )
    """)

    columns = [
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(orders)"
        ).fetchall()
    ]

    if "email" not in columns:
        connection.execute(
            "ALTER TABLE orders ADD COLUMN email TEXT"
        )

    connection.execute("""
        CREATE TABLE IF NOT EXISTS support_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            order_id TEXT,
            issue TEXT NOT NULL,
            request_status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS refunds (
            order_id TEXT PRIMARY KEY,
            refund_status TEXT NOT NULL,
            reason TEXT,
            request_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            complaint_type TEXT NOT NULL,
            description TEXT,
            complaint_status TEXT DEFAULT 'Submitted',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    sample_orders = [
        ("QC101", "Ali", "ali@gmail.com", "Laptop",
         "Shipped", "2026-11-10", "TRK1001"),

        ("QC102", "Ahmed", "ahmed@gmail.com", "Headphones",
         "Processing", "2026-11-12", "TRK1002"),

        ("QC103", "Sara", "sara@gmail.com", "Mobile",
         "Delivered", "2026-11-05", "TRK1003")
    ]

    connection.executemany("""
        INSERT INTO orders (
            order_id, customer_name, email, product,
            status, estimated_delivery, tracking_number
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(order_id)
        DO UPDATE SET email = excluded.email
    """, sample_orders)

    connection.commit()
    connection.close()


# Get order information
def get_order(order_id):
    connection = connect_db()

    order = connection.execute(
        "SELECT * FROM orders WHERE order_id = ?",
        (order_id,)
    ).fetchone()

    connection.close()

    return dict(order) if order else None


# Verify customer email
def verify_customer_email(order_id, email):
    order = get_order(order_id)

    if not order or not order["email"] or not email:
        return False

    return (
        order["email"].strip().lower()
        == email.strip().lower()
    )


# Cancel an order
def cancel_order(order_id):
    connection = connect_db()

    cursor = connection.execute("""
        UPDATE orders
        SET status = 'Cancelled'
        WHERE order_id = ?
        AND LOWER(status) = 'processing'
    """, (order_id,))

    connection.commit()
    connection.close()

    if cursor.rowcount > 0:
        return f"Order {order_id} has been cancelled successfully."

    return "Order could not be cancelled. Please check its status."


# Create a refund request
def create_refund_request(order_id, reason):
    order = get_order(order_id)

    if not order:
        return "Order not found."

    if order["status"].lower() != "delivered":
        return "Refund requests are only allowed for delivered orders."

    connection = connect_db()

    existing_refund = connection.execute(
        "SELECT * FROM refunds WHERE order_id = ?",
        (order_id,)
    ).fetchone()

    if existing_refund:
        connection.close()
        return "A refund request already exists for this order."

    connection.execute("""
        INSERT INTO refunds (order_id, refund_status, reason)
        VALUES (?, 'Pending', ?)
    """, (order_id, reason))

    connection.commit()
    connection.close()

    return "Your refund request has been submitted with Pending status."


# Check refund status
def get_refund_status(order_id):
    connection = connect_db()

    refund = connection.execute(
        "SELECT * FROM refunds WHERE order_id = ?",
        (order_id,)
    ).fetchone()

    connection.close()

    if refund:
        return (
            f"Refund status for order {order_id}: "
            f"{refund['refund_status']}"
        )

    return "No refund request was found for this order."


# Submit a wrong product complaint
def create_complaint(order_id, description):
    connection = connect_db()

    order = connection.execute(
        "SELECT order_id FROM orders WHERE order_id = ?",
        (order_id,)
    ).fetchone()

    if not order:
        connection.close()
        return "Order not found."

    connection.execute("""
        INSERT INTO complaints (
            order_id, complaint_type, description
        )
        VALUES (?, 'Wrong Product', ?)
    """, (order_id, description))

    connection.commit()
    connection.close()

    return "Your wrong product complaint has been submitted successfully."


# Request human support
def create_support_request(customer_name, order_id, issue):
    connection = connect_db()

    connection.execute("""
        INSERT INTO support_requests (
            customer_name, order_id, issue
        )
        VALUES (?, ?, ?)
    """, (customer_name, order_id, issue))

    connection.commit()
    connection.close()

    return (
        "Your request has been forwarded to our "
        "human support team successfully."
    )


# Get all records for the employee dashboard
def get_dashboard_records(table_name):
    allowed_tables = [
        "orders",
        "refunds",
        "complaints",
        "support_requests"
    ]

    if table_name not in allowed_tables:
        return []

    connection = connect_db()

    cursor = connection.execute(
        f"SELECT * FROM {table_name} ORDER BY rowid DESC"
    )

    columns = [description[0] for description in cursor.description]
    records = [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

    connection.close()

    return records


# Get all customer orders
def get_all_orders():
    return get_dashboard_records("orders")


# Get all refund requests
def get_all_refunds():
    return get_dashboard_records("refunds")


# Get all customer complaints
def get_all_complaints():
    return get_dashboard_records("complaints")


# Get all human support requests
def get_all_support_requests():
    return get_dashboard_records("support_requests")

if __name__ == "__main__":
    initialize_database()
    print("QuickCart database created successfully!")

def update_complaint_status(complaint_id, new_status):
    connection = connect_db()

    connection.execute(
        """
        UPDATE complaints
        SET complaint_status = ?
        WHERE complaint_id = ?
        """,
        (new_status, complaint_id)
    )

    connection.commit()
    connection.close()

def update_refund_status(order_id, new_status):
    connection = connect_db()

    connection.execute(
        """
        UPDATE refunds
        SET refund_status = ?
        WHERE order_id = ?
        """,
        (new_status, order_id)
    )

    connection.commit()
    connection.close()

def update_support_status(request_id, new_status):
    connection = connect_db()

    connection.execute(
        """
        UPDATE support_requests
        SET request_status = ?
        WHERE request_id = ?
        """,
        (new_status, request_id)
    )

    connection.commit()
    connection.close()
