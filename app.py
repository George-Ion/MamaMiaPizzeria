from flask import Flask, render_template
from controllers import users_bp, orders_bp, products_bp
from models import db
from sqlalchemy import inspect

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Fotina17@localhost/mamma_mia_pizza"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = "dev-secret"

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(users_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(products_bp)

    # Test database connection
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Connected to database. Found tables: {tables}")
        except Exception as e:
            print(f"Database connection error: {e}")

    # Home route - now renders the proper template
    @app.route("/")
    def index():
        return render_template('index.html')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)