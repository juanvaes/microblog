# imports
from flask import render_template, redirect, flash, url_for, request
from werkzeug.urls import url_parse
from datetime import datetime

# flask extensions imports
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Mail, Message


# Local imports
from .app import app
from .app import db
from .app import mail
from .errors import internal_error, not_found_error
from .forms import LoginForm, RegisterForm, EditProfileForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from .models import User, Post
from .email import send_password_reset_email

@app.route('/', methods=['GET','POST'])
@app.route('/home', methods=['GET','POST'])
def home():
	form_obj = PostForm()
	if form_obj.validate_on_submit():
		post= Post(body=form_obj.post.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Great!')
		return redirect(url_for('home'))
	page = request.args.get('page', 1, type = int)
	if current_user.is_authenticated:
		posts = current_user.followed_posts().paginate(page, app.config['POSTS_PER_PAGE'], False)
		# Next url
		next_url = url_for('home', page = posts.next_num) if posts.has_next else None
		prev_url = url_for('home', page = posts.prev_num) if posts.has_prev else None
		return(render_template('home.html', title = 'Home', form = form_obj, posts = posts.items, next_url = next_url, prev_url = prev_url))
	
	return(render_template('home.html', title = 'Home', form = form_obj))

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


@app.route('/user/<username>')
@login_required
def user_profile(username):
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1, type = int)
	posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('user_profile', username = user.username, page = posts.next_num) if posts.has_next else None
	prev_url = url_for('user_profile', username = user.username, page = posts.prev_num) if posts.has_prev else None
	print(posts)
	return(render_template('user.html', user = user, posts = posts.items, next_url = next_url, prev_url = prev_url))


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


@app.route('/explore')
@login_required
def explore():
	page = request.args.get('page', 1, type = int)
	posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('explore', page = posts.next_num) if posts.has_next else None
	prev_url = url_for('explore', page = posts.prev_num) if posts.has_prev else None
	return render_template('home.html', title = 'Explore', posts = posts.items, next_url = next_url, prev_url = prev_url)

@app.route('/msg')
def msg():
	msg = Message('Atención!', sender='energiesop@gmail.com', recipients = ['jcvalencia22@hotmail.com'])
	msg.body = "Este sabado no deben trabajar"
	mail.send(msg)
	return 'sent'


@app.route('/reset_password_request', methods = ['GET', 'POST'])
def reset_password_request():
	if current_user.is_authenticated:
		return(redirect(url_for('login')))
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email = form.email.data).first()
		if user:
			send_password_reset_email(user)
		flash('Check your email for the instructions to reset your password')
		return(redirect(url_for('login')))
	return(render_template('reset_password_request.html', title = 'Reset Password', form = form))


@app.route('/reset_password_reset/<token>', methods = ['GET', 'POST'])
def reset_password(token):
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	user = User.verify_reset_password_token(token)
	if not user:
		return redirect(url_for('home'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		user.set_password(form.password.data)
		db.session.commit()
		flash('Your password has been reset')
		return redirect(url_for('login'))
	return render_template('reset_password.html', form = form)