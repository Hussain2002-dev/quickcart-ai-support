# QuickCart – AI Delivery Customer Support Agent

QuickCart is an AI-powered customer support application built using Python and Flask. It helps customers with common delivery and order-related questions through an AI chatbot.

I developed this project to learn how AI can be used in real-world customer support systems.

## Features

- AI-powered customer support chatbot
- Order tracking using order ID
- Customer email verification
- Order cancellation eligibility checking
- Refund request and refund status checking
- Wrong product complaint submission
- Human support request
- Employee dashboard to manage orders, refunds, complaints, and support requests
- SQLite database for storing records

## Technologies Used

- Python
- Flask
- Groq API
- SQLite
- HTML
- CSS
- JavaScript

## Project Setup

1. Clone this repository:

   ```bash
   git clone YOUR_GITHUB_REPOSITORY_LINK
   ```

2. Open the project folder:

   ```bash
   cd quickcart-ai-support
   ```

3. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

4. Activate the environment on macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

5. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

6. Create a `.env` file in the project folder and add your own credentials:

   ```env
   GROQ_API_KEY=your_groq_api_key
   ADMIN_USERNAME=your_admin_username
   ADMIN_PASSWORD=your_admin_password
   FLASK_SECRET_KEY=your_secret_key
   ```

7. Run the application:

   ```bash
   python app.py
   ```

8. Open this address in your browser:

   `http://127.0.0.1:5000/`

## Learning Outcomes

Through this project, I practiced working with Flask, database operations, AI integration, API usage, and building a web-based application.

## Project Status

Developed as a learning project to explore AI-powered customer support automation.

**Note:** This is a local demonstration project. The employee dashboard currently needs authentication and security improvements before public deployment.