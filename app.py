from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import threading
import requests
from datetime import datetime, timedelta
from babel.numbers import format_currency
# from flask_cors import CORS
import win32print
# from PyQt6.QtCore import QUrl
# from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
# from PyQt6.QtWebEngineWidgets import QWebEngineView
import sys
import webbrowser
import time
import pyautogui
from flask_migrate import Migrate

app = Flask(__name__)
# CORS(app)  # Allow all origins

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///billing.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ESC/POS Commands
ESC = b'\x1B'
LF = b'\x0A'
CENTER = ESC + b'\x61\x01'
LEFT = ESC + b'\x61\x00'
RIGHT = ESC + b'\x61\x02'

BOLD_ON = ESC + b'\x45\x01'
BOLD_OFF = ESC + b'\x45\x00'
DOUBLE_WIDTH_ON = ESC + b'\x21\x20'
DOUBLE_WIDTH_OFF = ESC + b'\x21\x00'
DOUBLE_SIZE_ON = ESC + b'\x21\x30'
DOUBLE_SIZE_OFF = ESC + b'\x21\x00'
CUT = LF + LF + LF + LF + LF + b'\x1D\x56\x00'

START_DATE = datetime(2025, 3, 25)

class BaseModel(db.Model):
    __abstract__ = True  # Don't create a table for this class
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def soft_delete(self):
        """Mark the record as deleted."""
        self.deleted_at = datetime.utcnow()
        db.session.commit()

    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None
        db.session.commit()

    @classmethod
    def query_active(cls):
        """Query only non-deleted records."""
        return cls.query.filter(cls.deleted_at.is_(None))

# Define the Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)  # Foreign Key
    customer = db.relationship('Customer', backref=db.backref('order', lazy=True))
    customer_name = db.Column(db.String(100), nullable=True)
    mobile = db.Column(db.String(50), nullable=True)
    seller_code = db.Column(db.String(50), nullable=True)
    items = db.Column(db.Text, nullable=False)  # JSON format
    subtotal = db.Column(db.Float, nullable=False)
    cgst = db.Column(db.Float, nullable=False)
    sgst = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    total_quantity = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)  # Foreign Key
    order = db.relationship('Order', backref=db.backref('order_item', lazy=True))
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)  # Foreign Key
    item = db.relationship('Item', backref=db.backref('order_item', lazy=True))
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)

# Define the Item model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_number = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    suffix = db.Column(db.String(100), nullable=True)
    active = db.Column(db.Boolean, default=True)
    def __init__(self, name, suffix=None):
        # Get the highest existing item_number and increment it
        # max_item_number = db.session.query(db.func.max(Item.item_number)).scalar()
        max_item_number = db.session.query(db.func.max(Item.item_number)).filter(Item.active == True).scalar()
        self.item_number = (max_item_number or 0) + 1  # If None, start from 1
        self.name = name
        self.suffix = suffix
# Define the Item model
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=True)
    mobile = db.Column(db.String(50), nullable=True)

@app.route("/")
def index():
    current_date = datetime.now()
    # days_diff = (current_date - START_DATE).days
    # if days_diff > 15:
    #     # return "Trial licence expired."
    #     return render_template("licence_expired.html")
    # else:
    return render_template("index.html")

@app.route("/items", methods=['GET'])
def get_items():
    page = request.args.get('page', 1, type=int)  # Get page number from query params
    per_page = request.args.get('per_page', 10, type=int)  # Items per page
    items_data = Item.query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template("items_list.html",  items=items_data)


@app.route("/inventory/<int:item_id>", methods=['GET'])
def get_inventory(item_id):
    page = request.args.get('page', 1, type=int)  # Get page number from query params
    per_page = request.args.get('per_page', 10, type=int)  # Items per page
    items_data = Item.query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template("inventory.html",  items=items_data)

@app.route("/get-items-list", methods=['GET'])
def get_items_list():
    items = Item.query.all()
    items_data = [{"id": item.item_number, "name": item.name, "suffix": item.suffix} for item in items]
    return jsonify(items_data)

@app.route("/add-item", methods=["GET"])
def add_item():
    return render_template("add_item.html")

@app.route("/add_item", methods=["POST"])
def submit_item():
    data = request.json
    existing_item = Item.query.filter_by(name=data["name"]).first()  # Check for existing item
    if existing_item:
        return jsonify({"message": "Item with this name already exists!"}), 400  # Return error if exists
    else:
        new_item = Item(name=data["name"])
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"message": "Item added successfully!"})

@app.route("/edit-item/<int:item_id>", methods=["GET"])
def edit_item(item_id):
    item = Item.query.get(item_id)
    return render_template("edit_item.html", item = item)

@app.route("/edit_item/<int:item_id>", methods=["POST"])
def update_item(item_id):
    data = request.json
    existing_item = Item.query.filter(Item.name == data["name"], Item.id != item_id).first()
    if existing_item:
        return jsonify({"message": "Item with this name already exists!"}), 400
    else:
        item = Item.query.get(item_id)
        if item:
            item.name = data["name"]
            db.session.commit()
            return jsonify({"message": "Item updated successfully!"})
        return jsonify({"message": "Item not found"}), 404

@app.route("/get_new_order_id", methods=["GET"])
def get_new_order_id():
    max_order = db.session.query(db.func.max(Order.id)).scalar()  # Get max order_id
    next_order_id = (max_order or 0) + 1  # Default to 1 if no orders exist
    return jsonify(next_order_id)

@app.route("/delete_item/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if item:
        db.session.delete(item)
        items = db.session.query(Item).order_by(Item.id).all()

        # Reassign item_number
        for index, item in enumerate(items, start=1):
            item.item_number = index
        db.session.commit()
        return jsonify({"message": "Item deleted successfully!"})
    return jsonify({"message": "Item not found"}), 404

@app.route("/receipts", methods=['GET'])
def get_receipts():
    page = request.args.get('page', 1, type=int)  # Get page number from query params
    per_page = request.args.get('per_page', 10, type=int)  # Items per page
    receipt_data = Order.query.order_by(Order.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("receipt_list.html",  receipts=receipt_data)

@app.route("/save_order", methods=["POST"])
def save_order():
    total = 0
    data = request.json
    item_data = []
    total_quantity = 0
    for item in data["items"]:
        total = total + item["price"]*item["quantity"]
        itemObj = Item.query.filter_by(item_number=item['id']).first()
        total_quantity = total_quantity + item["quantity"]
        suffix = itemObj.suffix if itemObj.suffix else ''
        item_data.append({"name": itemObj.name, "quantity": str(item["quantity"])+' '+suffix, "price": format(item["price"], ".2f"), "total": format(item["total"], ".2f")})
    subtotal = (total/105)*100  # Removing 5% GST
    subtotal = round(subtotal, 2)
    tax = (total - subtotal)
    cgst = sgst = tax / 2
    total = subtotal + cgst + sgst  # This should match the total amount including GST
    
    new_order = Order(
        seller_code=data["sellerCode"],
        customer_name=data["customerName"],
        mobile=data["mobile"],
        items=json.dumps(item_data),
        subtotal=format(subtotal, ".2f"),
        cgst=format(cgst, ".2f"),
        sgst=format(sgst, ".2f"),
        tax=format(tax, ".2f"),
        total=format(total, ".2f"),
        timestamp=datetime.today(),
        total_quantity=total_quantity,
    )
    db.session.add(new_order)
    db.session.commit()
    # print_receipt(new_order.id)
    # print_receipt(new_order.id)
    return jsonify({"message": "Order saved", "order_id": new_order.id})

@app.route('/bill/<string:order_id>')
def bill(order_id):
    order = Order.query.get(order_id)
    items = json.loads(order.items)
    receipt_data = {
        "order_id": order.id,
        "mobile": order.mobile,
        "seller_code": order.seller_code or "",
        "date": order.timestamp.strftime("%d/%m/%y"),
        "time": order.timestamp.strftime("%H:%M"),
        "items": items,
        "subtotal": order.subtotal,
        "cgst": order.cgst,
        "sgst": order.sgst,
        "tax": order.tax,
        "total": order.total,
        "total_items": len(items),
        "total_quantity": order.total_quantity,
    }
    return render_template("bill_template.html",  receipt=receipt_data)

def print_receipt(order_id):
    order = Order.query.get(order_id)
    items = json.loads(order.items)
    receipt_data = {
        "order_id": order.id,
        "mobile": order.mobile,
        "seller_code": order.seller_code or "",
        "date": order.timestamp.strftime("%d/%m/%y"),
        "time": order.timestamp.strftime("%H:%M"),
        "items": items,
        "subtotal": order.subtotal,
        "cgst": order.cgst,
        "sgst": order.sgst,
        "tax": order.tax,
        "total": order.total,
        "total_items": len(items),
        "total_quantity": order.total_quantity,
    }
    # Printer Setup
    # Printer Setup
    printer_name = win32print.GetDefaultPrinter()
    hprinter = win32print.OpenPrinter(printer_name)
    hprinter_dc = win32print.StartDocPrinter(hprinter, 1, ("Receipt", None, "RAW"))
    win32print.StartPagePrinter(hprinter)

    # Print Header
    win32print.WritePrinter(hprinter, LF)
    win32print.WritePrinter(hprinter, CENTER + DOUBLE_SIZE_ON + b"PAKEEZA COLLECTION" + DOUBLE_SIZE_OFF + LF)
    win32print.WritePrinter(hprinter, b"18, 1st Cross Rd" + LF)
    win32print.WritePrinter(hprinter, b"Old Gurappanapalya" + LF)
    win32print.WritePrinter(hprinter, b"Jayanagara 9th block" + LF)
    win32print.WritePrinter(hprinter, b"S.G. Palya, Bengaluru 560029" + LF)
    win32print.WritePrinter(hprinter, LF)
    win32print.WritePrinter(hprinter, LEFT + b"MOBILE:8431795196" + LF)
    win32print.WritePrinter(hprinter, b"GSTIN:290IWPS3898Q1Z3" + LF)
    # win32print.WritePrinter(hprinter, f'BILL NO: {receipt_data['order_id']}' + LF)
    win32print.WritePrinter(hprinter, f"BILL NO:{receipt_data['order_id']}".encode() + LF)
    # win32print.WritePrinter(hprinter, f"BILL NO: {str(receipt_data['order_id'])}".encode() + LF)
    win32print.WritePrinter(hprinter, f"DATE:{receipt_data['date']}".encode() + b' ' * 24 + b"TIME:" + f"{receipt_data['time']}".encode() + LF)
    win32print.WritePrinter(hprinter, receipt_data['seller_code'].encode() + LF)

    win32print.WritePrinter(hprinter, LEFT + b'-' * 48 + LF)

    # Print Table Header
    win32print.WritePrinter(hprinter, LEFT + BOLD_ON + b"SI	ITEM NAME	QTY	RATE	AMOUNT" + BOLD_OFF + LF)
    win32print.WritePrinter(hprinter, LEFT + b'-' * 48 + LF)

    # Print Table Items
    win32print.WritePrinter(hprinter, LEFT)
    for no, item in enumerate(receipt_data['items'], start=1):
        item_name, qty, rate, amount = item['name'], float(item['quantity']), float(item['price']), float(item['total'])
        item_line = f"{no:>2}  {item_name[:17]:<17} {qty:>5.2f} {rate:>8.2f} {amount:>10.2f}"
        win32print.WritePrinter(hprinter, item_line.encode() + LF)

    win32print.WritePrinter(hprinter, LEFT + b'-' * 48 + LF)

    # Print Total
    item_line = f"TOTAL ITEM(S):{receipt_data['total_items']:>2}/QTY:{receipt_data['total_quantity']:<5}           {receipt_data['total']:>10.2f}"
    win32print.WritePrinter(hprinter, item_line.encode() + LF)

    win32print.WritePrinter(hprinter, b'-' * 48 + LF)


    # Print taxes
    win32print.WritePrinter(hprinter, BOLD_ON + b"TAX %    TAXABLE VAL   CGST   SGST   TAX AMOUNT" + BOLD_OFF + LF)
    win32print.WritePrinter(hprinter, b'-' * 48 + LF)
    win32print.WritePrinter(hprinter, b"                     (2.50%) (2.50%)" + LF)
    item_line = f"{5.00:<4.2f}     {receipt_data['subtotal']:>10.2f}   {receipt_data['cgst']:>5.2f}  {receipt_data['sgst']:>5.2f}    {receipt_data['tax']:>7.2f}"
    win32print.WritePrinter(hprinter, item_line.encode() + LF)
    win32print.WritePrinter(hprinter, b'-' * 48 + LF)

    # Print final
    item_line = f"TOTAL:                          {receipt_data['total']:>15.2f}"
    win32print.WritePrinter(hprinter, BOLD_ON + item_line.encode() + BOLD_OFF + LF)
    win32print.WritePrinter(hprinter, b'-' * 48 + LF)

    # Print Footer Notes
    win32print.WritePrinter(hprinter, CENTER + b"NOTE: AFTER CUTTING NO EXCHANGE" + LF)
    win32print.WritePrinter(hprinter, b"COTTON AND LINEN CLOTH WASH BEFORE STITCH" + LF)
    win32print.WritePrinter(hprinter, b"COLOUR AND PRINT NO GUARANTEE" + LF)
    win32print.WritePrinter(hprinter, b"THANK YOU, VISIT AGAIN" + LF)

    # Cut Paper
    win32print.WritePrinter(hprinter, CUT)

    # End Printing
    win32print.EndPagePrinter(hprinter)
    win32print.EndDocPrinter(hprinter)
    win32print.ClosePrinter(hprinter)


@app.route("/get-day-report", methods=["POST"])
def get_day_report():
    try:
        data = request.get_json()
        selected_date = data.get("date")  # Expected format: "DD-MM-YYYY"

        if not selected_date:
            return jsonify({"success": False, "message": "Date is required"}), 400

        # Convert DD-MM-YYYY to timestamp range
        start_date = datetime.strptime(selected_date, "%d-%m-%Y")
        end_date = start_date + timedelta(days=1)  # End of the selected day

        # Check if the date is in the future
        today = datetime.now().date()
        if start_date.date() > today:
            return jsonify({"success": False, "message": "Future dates are not allowed"}), 400

        # Calculate total sum of all matching orders
        total_sum = db.session.query(db.func.sum(Order.total)).filter(
            Order.timestamp >= start_date, Order.timestamp < end_date
        ).scalar() or 0  # Default to 0 if no orders found
        orders = Order.query.filter(Order.timestamp >= start_date, Order.timestamp < end_date).all()
        report = {
            'list': [],
            'total': {
                'items': 0,
                'amount': 0,
                'tax': '0.00',
                'discount': '0.00'
            }
        }
        for order in orders:
            report['list'].append({
                'bill_no': order.id,
                'items': format(order.total_quantity, ".2f"),
                'tax': '0.00',
                'discount': '0.00',
                'amount': format(order.total, ".2f"),
            })
            report['total']['items'] += order.total_quantity
            report['total']['amount'] += order.total
        report['total']['items'] = format(report['total']['items'], ".2f")
        report['total']['amount'] = format(report['total']['amount'], ".2f")
        return jsonify({
            "success": True,
            "report": report,
            "total": format_currency(total_sum, "", locale='en_IN').strip()
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route("/print-day-report", methods=["POST"])
def print_day_report():
    data = request.get_json()
    selected_date = data.get("date")  # Expected format: "DD-MM-YYYY"

    if not selected_date:
        return jsonify({"success": False, "message": "Date is required"}), 400

    # Convert DD-MM-YYYY to timestamp range
    start_date = datetime.strptime(selected_date, "%d-%m-%Y")
    end_date = start_date + timedelta(days=1)  # End of the selected day

    # Check if the date is in the future
    today = datetime.now().date()
    if start_date.date() > today:
        return jsonify({"success": False, "message": "Future dates are not allowed"}), 400

    orders = Order.query.filter(Order.timestamp >= start_date, Order.timestamp < end_date).all()
    report_data = {
        'report_date': datetime.strptime(selected_date, "%d-%m-%Y").strftime('%d/%m/%y'),
        'current_date': today.strftime('%d/%m/%y'),
        'current_time': datetime.now().strftime('%H:%M'),
        'list': [],
        'total': {
            'items': 0,
            'amount': 0,
            'tax': '0.00',
            'discount': '0.00'
        }
    }
    index = 1
    for order in orders:
        report_data['list'].append({
            'bill_no': order.id,
            'items': order.total_quantity,
            'tax': '0.00',
            'discount': '0.00',
            'amount': order.total,
        })
        report_data['total']['items'] += order.total_quantity
        report_data['total']['amount'] += order.total
        index += 1
    report_data['total']['items'] = report_data['total']['items']
    report_data['total']['amount'] = report_data['total']['amount']

    # Printer Setup
    printer_name = win32print.GetDefaultPrinter()
    hprinter = win32print.OpenPrinter(printer_name)
    hprinter_dc = win32print.StartDocPrinter(hprinter, 1, ("Receipt", None, "RAW"))
    win32print.StartPagePrinter(hprinter)

    # Print Header
    win32print.WritePrinter(hprinter, LF)
    win32print.WritePrinter(hprinter, CENTER + DOUBLE_SIZE_ON + b"PAKEEZA COLLECTION" + DOUBLE_SIZE_OFF + LF)
    win32print.WritePrinter(hprinter, b"18, 1st Cross Rd" + LF)
    win32print.WritePrinter(hprinter, b"Old Gurappanapalya" + LF)
    win32print.WritePrinter(hprinter, b"Jayanagara 9th block" + LF)
    win32print.WritePrinter(hprinter, b"S.G. Palya, Bengaluru 560029" + LF)
    win32print.WritePrinter(hprinter, LF)
    win32print.WritePrinter(hprinter, BOLD_ON + b"BILLWISE REPORT" + BOLD_OFF + LF)
    win32print.WritePrinter(hprinter, LF)
    win32print.WritePrinter(hprinter, LEFT + f"PRESENT DATE:{report_data['current_date']}".encode() + b' ' * 17 + f"TIME:{report_data['current_time']}".encode() + LF)
    win32print.WritePrinter(hprinter, f"REPORT DATE :{report_data['report_date']}".encode() + LF)

    win32print.WritePrinter(hprinter, b'-' * 48 + LF)

    # Print Table Header
    win32print.WritePrinter(hprinter, BOLD_ON + b"BLNO       ITEMS    TAX    DISC          AMOUNT" + BOLD_OFF + LF)
    win32print.WritePrinter(hprinter, b'-' * 48 + LF)

    # Print Table Items
    # win32print.WritePrinter(hprinter, LEFT)
    for item in report_data['list']:
        bill_no, items, tax, discount, amount = item['bill_no'], item['items'], item['tax'], item['discount'], item['amount']
        # Format item line to match PDF spacing
        item_line = f"{bill_no:<6}   {items:>8.2f}   {tax}   {discount}    {amount:>12.2f}"
        win32print.WritePrinter(hprinter, item_line.encode() + LF)
    win32print.WritePrinter(hprinter, LEFT + b'-' * 48 + LF)

    # # Print Total
    item_line = f"TOTAL:{report_data['total']['items']:>11.2f}   0.00   0.00{report_data['total']['amount']:>16.2f}"
    win32print.WritePrinter(hprinter, item_line.encode() + LF)

    win32print.WritePrinter(hprinter, b'-' * 48 + LF)

    # Print Footer Notes
    win32print.WritePrinter(hprinter, b"NOTE: TAX AMOUNT INCLUDES OTHER CHARGES" + LF)
    win32print.WritePrinter(hprinter, b"NOTE: -VE VALUES INDICATE RETURN BILL" + LF)

    # Cut Paper
    win32print.WritePrinter(hprinter, CUT)

    # End Printing
    win32print.EndPagePrinter(hprinter)
    win32print.EndDocPrinter(hprinter)
    win32print.ClosePrinter(hprinter)
    return jsonify({
        "success": True
    }), 200

@app.route("/search_customer", methods=["GET"])
def search_customer():
    query = request.args.get("mobile", "")
    customers = Customer.query.filter(Customer.mobile.like(f"{query}%")).all()
    results = [{"id": c.id, "mobile": c.mobile, "customer_name": c.customer_name} for c in customers]
    return jsonify(results)

# def run_flask():
#     app.run(host="127.0.0.1", port=5000, debug=False)

# class WebApp(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Billing")

#         layout = QVBoxLayout()
#         self.browser = QWebEngineView()
#         self.browser.setUrl(QUrl("http://127.0.0.1:5000/"))
#         layout.addWidget(self.browser)

#         central_widget = QWidget()
#         central_widget.setLayout(layout)
#         self.setCentralWidget(central_widget)
#         # self.showFullScreen()  # Make the window full-screen\
#         self.showMaximized()

# if __name__ == "__main__":
#     # Start Flask in a separate thread
#     threading.Thread(target=run_flask, daemon=True).start()

#     # Start PyQt6 app
#     app = QApplication(sys.argv)
#     window = WebApp()
#     window.show()
#     sys.exit(app.exec())


def open_browser():
    webbrowser.open_new("http://localhost:5000/")
    time.sleep(2)  # Wait for the browser to open
    pyautogui.hotkey('ctrl', 'l')  # Focus the browser window (optional)
    pyautogui.hotkey('f11')

def is_flask_running():
    try:
        response = requests.get("http://localhost:5000/")
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


#  Function to start the Flask app
def start_flask():
     app.run(debug=False, use_reloader=False)

if __name__ == "__main__":
    if not is_flask_running():
        threading.Timer(1.25, open_browser).start()  # Open the browser after 1.25 seconds
        start_flask()
    else:
        threading.Timer(1.25, open_browser).start()

# if __name__ == "__main__":
#     app.run(debug=True)