from app import create_app

app = create_app()

# Run migrations automatically
with app.app_context():
    upgrade()

if __name__ == '__main__':
    app.run(debug=True)