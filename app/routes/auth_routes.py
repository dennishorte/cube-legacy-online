from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import login_required
from flask_login import logout_user

from app import app
from app.forms import LoginForm
from app.models.user_models import User


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(name=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)


        return redirect(url_for('index'))

    return render_template('login.html', title='Sign In', form=form)



@app.route('/login_as/<user_name>')
@login_required
def login_as(user_name):
    if not app.config['FLASK_ENV'] == 'development':
        return "Forbidden"

    user = User.query.filter(User.name == user_name).first()

    if user and user_name != current_user.name:
        logout_user()
        login_user(user)

    return redirect(request.referrer)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
