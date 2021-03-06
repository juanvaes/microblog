from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment

from config import Config

# Initialize/creates a flask object
app = Flask(__name__)

# Configurate flask object for config.py script
app.config.from_object(Config)

# Initialize a login object for the application
login = LoginManager(app)
login.login_view = 'login'

# Initialize a mail application
mail = Mail(app)

#Initialize a bootstrap object
boostrap = Bootstrap(app)

#Initialize a moment object
moment = Moment(app)

# Creates an instance of db by binding the flask application (the app object)
db = SQLAlchemy(app) 	#This is a database object

# Migrates the db
migrate = Migrate(app,db)


from api import models
db.create_all()


from api import routes