from flask import Flask
from flask_migrate import Migrate
from models import db
from routes import main
from config import Config
from flask_jwt_extended import JWTManager
from flask_cors import CORS

app = Flask(__name__)

CORS(app, 
     resources={r"/*": {
         "origins": ["http://localhost:5173"],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
         "expose_headers": ["Content-Type", "Authorization"],
         "supports_credentials": True,
         "send_wildcard": False,
         "vary_header": True
     }})

app.config.from_object(Config)
jwt = JWTManager(app)

db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(main)

if __name__ == "__main__":
    app.run(debug=True, port=5000)