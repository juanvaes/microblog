import os

# The configuration settings are defined as class variables inside the Config class. 
# As the application needs more configuration items, they can be added to this class, 
# and later if I find that I need to have more than one configuration set, 
# I can create subclasses of it. 
class Config(object):
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
	SQLALCHEMY_DATABASE_URI = 'mysql://juancamilo:4454861@localhost/practiflask'							#mysql://username:password@server/db
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	POSTS_PER_PAGE = 3