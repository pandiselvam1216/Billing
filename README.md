# Billing Software - Browser Application

A comprehensive billing and inventory management system built with Flask and SQLite.

## Features

- **Product Management**: Add, edit, and delete products with stock tracking.
- **Customer Management**: Manage customer details and purchase history.
- **Billing**: Create professional invoices with itemized products.
- **Order Management**: Track and manage customer orders.
- **User Authentication**: Secure login system.
- **Reporting**: Generate sales reports and analytics.

## Prerequisites

- Python 3.6+
- pip (Python package installer)

## Installation

1.  **Clone the repository** (or download the source code).

2.  **Navigate to the project directory**:
    ```bash
    cd billing-software-browser_app_new
    ```

3.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    ```

4.  **Activate the virtual environment**:
    - **Windows**: `.\venv\Scripts\activate`
    - **macOS/Linux**: `source venv/bin/activate`

5.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application**:
    ```bash
    .\venv\Scripts\python.exe app.py
    ```
    *(Or `python app.py` if your virtual environment is active)*

2.  **Access the application**:
    Open your web browser and go to: `http://127.0.0.1:5000`

## Database

The application uses SQLite for data storage.
- The database file is located at: `billing_software.db`
- It will be created automatically on the first run if it doesn't exist.

## Project Structure

```
billing-software-browser_app_new/
├── app.py                 # Main application file
├── models.py              # Database models (SQLAlchemy)
├── routes.py              # Application routes and logic
├── templates/             # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── products/
│   ├── customers/
│   ├── orders/
│   └── reports/
├── static/                # CSS, JavaScript, Images
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```