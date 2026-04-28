from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/items")
def get_items():
    return render_template("items_list.html")

@app.route("/inventory/<int:item_id>")
def get_inventory(item_id):
    return render_template("inventory.html", item_id=item_id)

@app.route("/add-item")
def add_item():
    return render_template("add_item.html")

@app.route("/edit-item/<int:item_id>")
def edit_item(item_id):
    return render_template("edit_item.html", item_id=item_id)

@app.route("/receipts")
def get_receipts():
    return render_template("receipt_list.html")

@app.route('/bill/<string:order_id>')
def bill(order_id):
    return render_template("bill_template.html", order_id=order_id)

if __name__ == "__main__":
    app.run(debug=False)