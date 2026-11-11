
import os
import json
from dotenv import load_dotenv
from groq import Groq

# Import database functions
from database import (
    get_order,
    verify_customer_email,
    cancel_order,
    create_refund_request,
    get_refund_status,
    create_complaint,
    create_support_request
)
# Load API key
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("Groq API key not found!")

# Connect to Groq
client = Groq(api_key=api_key)
# Store the order waiting for cancellation confirmation
pending_cancellation = None


# Function to get order information
def get_order_information(order_id):

    order = get_order(order_id)

    if order:
        return (
            f"Customer: {order['customer_name']}\n"
            f"Product: {order['product']}\n"
            f"Status: {order['status']}\n"
            f"Estimated Delivery: {order['estimated_delivery']}"
        )

    return "Sorry, this order ID was not found."

# Function to handle delayed delivery complaints
def handle_delivery_delay(order_id):

    order = get_order(order_id)

    if not order:
        return "Sorry, this order ID was not found."

    status = order["status"]
    delivery_date = order["estimated_delivery"]

    if status.lower() == "delivered":
        return (
            f"Order {order_id} has already been delivered. "
            f"Current status: {status}."
        )

    if status.lower() == "cancelled":
        return (
            f"Order {order_id} has been cancelled. "
            "There is no active delivery."
        )

    return (
        f"Order ID: {order_id}\n"
        f"Product: {order['product']}\n"
        f"Current Status: {status}\n"
        f"Estimated Delivery: {delivery_date}\n"
        "Please check again if the order does not arrive "
        "by the estimated delivery date."
    )




# Function to check cancellation eligibility
def check_cancellation_eligibility(order_id):

    global pending_cancellation

    order = get_order(order_id)

    if not order:
        return "Order not found."

    if order["status"].lower() == "processing":

        pending_cancellation = order_id

        return (
            f"Order {order_id} is eligible for cancellation. "
            "Ask the customer to confirm before cancelling."
        )

    return (
        f"Order {order_id} cannot be cancelled "
        f"because its status is {order['status']}."
    )

# Function to cancel an order
def cancel_customer_order(order_id):
    return cancel_order(order_id)

# Function to submit a refund request
def submit_customer_refund(order_id, reason):
    return create_refund_request(order_id, reason)


# Function to check refund status
def check_customer_refund_status(order_id):
    return get_refund_status(order_id)

# Function to submit wrong product complaints
def report_wrong_product(order_id, description):

    result = create_complaint(order_id, description)

    return result
# Function to request human support
def request_human_support(customer_name, order_id, issue):

    result = create_support_request(
        customer_name,
        order_id,
        issue
    )

    return result

# AI tool definitions
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_information",
            "description": "Get order details using the customer's order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Customer order ID, for example QC101."
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_cancellation_eligibility",
            "description": "Check whether a customer can cancel a specific order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Customer order ID, for example QC102."
                    }
                },
                "required": ["order_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "submit_customer_refund",
            "description": "Submit a refund request for a delivered order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Customer order ID."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for requesting a refund."
                    }
                },
                "required": ["order_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_customer_refund_status",
            "description": "Check the refund request status using an order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Customer order ID."
                    }
                },
                "required": ["order_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "handle_delivery_delay",
            "description": "Check order status and estimated delivery information when a customer reports a delayed order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Customer order ID."
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "report_wrong_product",
        "description": "Submit a wrong product complaint for a customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Customer order ID"
                },
                "description": {
                    "type": "string",
                    "description": "Details about the wrong product received"
                }
            },
            "required": ["order_id", "description"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "request_human_support",
        "description": "Forward a customer's issue to the human support team.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer's name"
                },
                "order_id": {
                    "type": "string",
                    "description": "Customer's order ID, if available"
                },
                "issue": {
                    "type": "string",
                    "description": "Reason for requesting human support"
                }
            },
            "required": ["customer_name", "order_id", "issue"]
        }
    }
}


]


# Function to ask AI
def ask_ai(user_message, conversation_history=None, verified_orders=None, agent_state=None):
    verified_orders = verified_orders or []
    agent_state = agent_state if agent_state is not None else {}


        # Check whether this customer's order is waiting for confirmation
    pending_order = agent_state.get("pending_cancellation")

    if pending_order is not None:

        reply = user_message.strip().lower().rstrip("!.")

        if reply in ["yes", "yes please", "confirm"]:

            if pending_order not in verified_orders:
                agent_state["pending_cancellation"] = None
                return "Please verify your order before cancelling it."

            result = cancel_customer_order(pending_order)
            agent_state["pending_cancellation"] = None
            return result

        elif reply in ["no", "no thanks", "don't cancel", "do not cancel"]:

            agent_state["pending_cancellation"] = None
            return "Okay! Your order will not be cancelled."

        else:
            return (
                f"Your order {pending_order} is waiting "
                "for cancellation confirmation. "
                "Please reply Yes or No."
            )
        messages = [
        {
            "role": "system",
            "content": """
            You are QuickCart's friendly customer support assistant.

            Remember information shared earlier in the conversation,
            including the customer's name and order ID.

            Do not repeatedly ask for information already provided.

            Help customers with their orders.

            Use get_order_information when customers ask about
            their order details or delivery status.

            Use check_cancellation_eligibility when customers
            ask whether they can cancel an order.

            Use submit_customer_refund when customers want
            to request a refund for a delivered order.

            Use check_customer_refund_status when customers
            ask about their refund status.

            Use report_wrong_product when customers report
            receiving the wrong product.

            Use request_human_support when customers ask
            to speak with a human representative.

            Ask for the customer's name if it is missing.
            Ask for the order ID if it is missing.

            Never invent order details.
            Only use information returned by the tools.
            Do not claim an order has been cancelled without confirmation.
            Never claim a refund has been paid.
            A refund request is only submitted with Pending status.
            """
        }
    ]

    
    messages = [
        {
            "role": "system",
            "content": """
            You are QuickCart's friendly customer support assistant.

            For simple greetings like Hi, Hello, or Hey,
            respond with a short and friendly greeting.

            Do not mention customer names, order IDs,
            delivery status, or previous order details
            during simple greetings.

            Only discuss order details when the customer
            specifically asks an order-related question.

            Use previous conversation information only
            when relevant to the current question.

            Do not repeatedly ask for information already provided.
            Never invent order details.
            Only use information returned by the tools.
            """
        }
    ]


    if conversation_history:
     messages.extend(conversation_history[-10:])

    messages.append({
    "role": "user",
    "content": user_message
})


    # Ask AI whether it needs a tool
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.3
    )

    response_message = response.choices[0].message

    # Check whether AI requested a tool
    if response_message.tool_calls:

        messages.append(response_message)

        for tool_call in response_message.tool_calls:

            function_name = tool_call.function.name

            function_args = json.loads(
                tool_call.function.arguments
            )


            # Check customer verification before executing tools
            protected_tools = [
                "get_order_information",
                "check_cancellation_eligibility",
                "submit_customer_refund",
                "check_customer_refund_status",
                "handle_delivery_delay",
                "report_wrong_product",
                "request_human_support"
            ]

            order_id = function_args.get("order_id", "").upper()

            if (
                function_name in protected_tools
                and order_id not in verified_orders
            ):
                result = (
                    "Customer verification required. "
                    "Ask the customer for their order ID "
                    "and registered email."
                )

            elif function_name == "get_order_information":
                result = get_order_information(order_id)

            elif function_name == "check_cancellation_eligibility":
                result = check_cancellation_eligibility(order_id)
                if "eligible for cancellation" in result.lower():
                 agent_state["pending_cancellation"] = order_id

            elif function_name == "submit_customer_refund":
                result = submit_customer_refund(
                    order_id, function_args["reason"]
                )
                return result

            elif function_name == "check_customer_refund_status":
                result = check_customer_refund_status(order_id)

            elif function_name == "handle_delivery_delay":
                result = handle_delivery_delay(order_id)

            elif function_name == "report_wrong_product":
                result = report_wrong_product(
                    order_id, function_args["description"]
                )

            elif function_name == "request_human_support":
                result = request_human_support(
                    function_args["customer_name"],
                    order_id,
                    function_args["issue"]
                )

            else:
                result = "Unknown tool requested."


            # Send tool result back to AI
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

        # AI generates final response
        final_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.3
        )

        return final_response.choices[0].message.content

    return response_message.content


# Run QuickCart
if __name__ == "__main__":

    print("Welcome to QuickCart Support!")
    print("Type 'exit' to stop.\n")

    while True:

        user_message = input("You: ")

        if user_message.lower() == "exit":
            print("Thank you for contacting QuickCart!")
            break

        answer = ask_ai(user_message)

        print("\nQuickCart AI:", answer, "\n")
