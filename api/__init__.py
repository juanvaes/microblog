import logging
from api import routes, models, errors
from logging.handlers import SMTPHandler
from api.app import app
from api.app import mail
from api.app import boostrap