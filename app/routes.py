# imports
from flask import render_template, redirect, flash, url_for, request
from werkzeug.urls import url_parse
from datetime import datetime

# extensions imports
from flask_login import current_user, login_user, logout_user, login_required


# Local imports
from .app import app, db
from app.errors import internal_error, not_found_error
from .forms import LoginForm, RegisterForm, EditProfileForm, PostForm
from .models import User, Post


@app.route('/')
def home():
	form_obj = PostForm()
	if form_obj.validate_on_submit():
		post= Post(body=form_obj.post.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Great!')
		return redirect(url_for('home'))
	return(render_template('home.html', form = form_obj))

@app.route('/register', methods=['GET','POST'])
def register():
	if current_user.is_authenticated:
		return(redirect(url_for('home')))
	rform = RegisterForm()
	if rform.validate_on_submit():
		user = User(username = rform.username.data, email = rform.email.data)
		user.set_password(rform.password.data)
		db.session.add(user)
		db.session.commit()
		flash('You are registered. ¡Now you can login to have access to our amazing things!')
		return(redirect(url_for('login')))

	return(render_template('register.html', form=rform))
	
@app.route('/login', methods=['GET','POST'])
def login():
	if current_user.is_authenticated:
		return(redirect(url_for('/')))
	form_obj = LoginForm()
	# Whent the browser sends a POST request as a result of the user pressing the submit buttom, form.validate_on_submit() 
	# is going to gather all the data, run all validators attached to fields, and if everything is all right it will return True
	if form_obj.validate_on_submit():
		flash('Login requested for user {}, remember_me={}'.format(form_obj.username.data, form_obj.remember_me.data))
		user = User.query.filter_by(username=form_obj.username.data).first()
		if user is None or not user.check_password(form_obj.password.data):
			flash('Invalid username or password')
			return(redirect(url_for('login')))
		# login_user() comes from flask_login extension. This function will register the user as logged in, so that means
		# that any future pages the user navigates to will have the current_user set to that user.
		login_user(user,remember=form_obj.remember_me.data)	
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('home')
		return(redirect(next_page))
	return(render_template('login.html', form = form_obj))


@app.route('/logout')
@login_required
def logout():
	logout_user()
	return(redirect(url_for('home')))

@app.route('/dashboard', methods=['GET','POST'])
@login_required
def dashboard():
	return(render_template('dashboard.html'))

@app.route('/users/', methods=['GET'])
def get_users():
	users = User.query.all()
	return(render_template('users.html', users = users))


@app.route('/user/<username>')
@login_required
def user_profile(username):
	user = User.query.filter_by(username=username).first_or_404()
	posts = [{'author':user, 'body':'Text post #1'}, {'author':user, 'body':'Text post #2'}]
	return(render_template('user.html', user = user, posts = posts))

@app.before_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen = datetime.utcnow()
		db.session.commit()

@app.route('/edit_profile', methods=['GET','POST'])
@login_required
def edit_profile():
	try:
		form_obj = EditProfileForm()
		if form_obj.validate_on_submit():
			current_user.username = form_obj.username.data
			current_user.about_me = form_obj.about_me.data
			db.session.commit()
			flash('Your changes have been saved.')
			return(redirect(url_for('edit_profile')))
		elif request.method == 'GET':
			form_obj.username.data = current_user.username
			form_obj.about_me.data = current_user.about_me
		return render_template('edit_profile.html', title = 'Edit Profile', form=form_obj)
	except Exception as e:
		return(internal_error(e))


@app.route('/follow/<username>')
@login_required
def follow(username):
	user = User.query.filter_by(username=username).first()
	print(user)
	if user is None:
		flash('User {} not found'.format(username))
		return(redirect(url_for('home')))
	if user == current_user:
		flash('You can not follow yourself')
		return(redirect(url_for('user_profile', username=username)))
	current_user.follow(user)
	db.session.commit()
	flash('You are following {}!'.format(username))
	return(redirect(url_for('user_profile', username = username)))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('User {} not found'.format(username))
		return(redirect(url_for('home')))
	if user == current_user:
		flash('You can not unfollow yourself')
		return(redirect(url_for('user_profile', username=username)))
	current_user.unfollow(user)
	db.session.commit()
	flash('You are not following {}!'.format(username))
	return(redirect(url_for('user_profile', username=username)))