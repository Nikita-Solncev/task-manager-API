from flask import Flask
from flask_migrate import Migrate
from models import db
from routes import main
from config import Config
from flask_jwt_extended import JWTManager
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)
jwt = JWTManager(app)

db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(main)


if __name__ == "__main__":
    app.run(debug=True, port=5000)