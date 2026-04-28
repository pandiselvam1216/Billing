from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)

with app.app_context():
    db.create_all()
    try:
        Item.query.paginate(page=1, per_page=10, error_out=False)
        print("Success")
    except Exception as e:
        import traceback
        traceback.print_exc()
