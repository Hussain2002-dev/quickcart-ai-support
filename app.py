

import re
import os
import secrets

from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)

from agent import ask_ai

from database import (
    verify_customer_email,
    get_all_orders,
    get_all_refunds,
    get_all_complaints,
    get_all_support_requests,
    update_complaint_status,
    update_refund_status,
    update_support_status
)

load_dotenv()


app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Employee dashboard

# Employee login
@app.route("/login", methods=["GET", "POST"])
def employee_login():

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (
            ADMIN_USERNAME
            and ADMIN_PASSWORD
            and secrets.compare_digest(username, ADMIN_USERNAME)
            and secrets.compare_digest(password, ADMIN_PASSWORD)
        ):
            session["employee_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


# Employee dashboard
@app.route("/admin")
def admin_dashboard():


    orders = get_all_orders()
    refunds = get_all_refunds()
    complaints = get_all_complaints()
    support_requests = get_all_support_requests()

    return render_template(
        "admin.html",
        orders=orders,
        refunds=refunds,
        complaints=complaints,
        support_requests=support_requests
    )


# Update complaint status
@app.route("/resolve-complaint/<int:complaint_id>", methods=["POST"])
def resolve_complaint(complaint_id):

    update_complaint_status(complaint_id, "Resolved")

    return redirect(url_for("admin_dashboard"))

# Update refund status
@app.route("/update-refund/<order_id>/<new_status>", methods=["POST"])
def update_refund(order_id, new_status):

    allowed_statuses = ["Approved", "Processed"]

    if new_status not in allowed_statuses:
        return "Invalid refund status", 400

    update_refund_status(order_id, new_status)

    return redirect(url_for("admin_dashboard"))

# Update support request status
@app.route("/complete-support/<int:request_id>", methods=["POST"])
def complete_support(request_id):

    update_support_status(request_id, "Completed")

    return redirect(url_for("admin_dashboard"))

# Employee logout
@app.route("/logout")
def employee_logout():

    session["employee_logged_in"] = False
    session.modified = True

    return redirect(url_for("employee_login"))

# Receive customer messages
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({
            "response": "Please enter a message."
        }), 400

    # Detect order ID and email
    order_match = re.search(
        r"\bQC\d+\b",
        user_message,
        re.IGNORECASE
    )

    email_match = re.search(
        r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}",
        user_message
    )

    # Remember the order ID for this session
    if order_match:
        order_id = order_match.group(0).upper()
        verified_orders = session.get("verified_orders", [])

        if order_id not in verified_orders:
            session["pending_order_id"] = order_id

    pending_order_id = session.get("pending_order_id")

    # Ask for email if an order ID was provided
    if pending_order_id and not email_match:
        return jsonify({
            "response": (
                f"I found your order ID {pending_order_id}. "
                "Please provide the email address registered "
                "with this order to verify your identity."
            )
        })

    # Verify customer email
    if pending_order_id and email_match:

        email = email_match.group(0)

        if verify_customer_email(pending_order_id, email):

            verified_orders = session.get("verified_orders", [])

            if pending_order_id not in verified_orders:
                verified_orders.append(pending_order_id)

            session["verified_orders"] = verified_orders
            session.pop("pending_order_id", None)

            return jsonify({
                "response": (
                    f"Your identity has been verified successfully "
                    f"for order {pending_order_id}! "
                    "How can I help you with this order?"
                )
            })

        return jsonify({
            "response": (
                "The email address does not match our records. "
                "Please check your registered email and try again."
            )
        })

    # Get conversation history and verified orders
    conversation_history = session.get("conversation_history", [])
    verified_orders = session.get("verified_orders", [])

    agent_state = {
        "pending_cancellation": session.get("pending_cancellation")
    }

    try:
        ai_response = ask_ai(
            user_message,
            conversation_history,
            verified_orders,
            agent_state
        )

        if agent_state.get("pending_cancellation"):
            session["pending_cancellation"] = agent_state["pending_cancellation"]
        else:
            session.pop("pending_cancellation", None)

        # Save conversation history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })

        conversation_history.append({
            "role": "assistant",
            "content": ai_response
        })

        session["conversation_history"] = conversation_history[-10:]

        return jsonify({
            "response": ai_response
        })

    except Exception as error:
        print("Error:", error)

        return jsonify({
            "response": "Sorry! Something went wrong. Please try again."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
