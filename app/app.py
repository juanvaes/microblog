from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Initialize/creates a flask object
app = Flask(__name__)

# Configurate flask object for config.py script
app.config.from_object(Config)

# Initialize a login object for the application
login = LoginManager(app)
login.login_view = 'login'


# Creates an instance of db by binding the flask application (the app object)
db = SQLAlchemy(app) 	#This is a database object

# Migrates the db
migrate = Migrate(app,db)


from app import models
db.create_all()


from app import routes