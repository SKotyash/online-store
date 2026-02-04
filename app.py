import os
from flask import Flask
from models import db
from flask_migrate import Migrate
import routes

app = Flask(__name__)
app.secret_key = "dev-key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'

db.init_app(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Создаст папку, если её нет


migrate=Migrate(app, db)


routes.init_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
