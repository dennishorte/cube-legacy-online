from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import login_required
from flask_login import logout_user
from is_safe_url import is_safe_url

from app import app
# from app.draft import DraftWrapper
# from app.draft_debugger import DraftDebugger
from app.forms import LoginForm
from app.forms import NewCubeForm
from app.models.cube import *
from app.models.draft import *
from app.models.user import *


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        
        if not next_page or not is_safe_url(next_page, request.host):
            next_page = url_for('index')
            
        return redirect(next_page)        
    
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/")
@app.route("/index")
@login_required
def index():
    active_seats = [x for x in current_user.draft_seats if not x.draft.complete]
    complete_seats = [x for x in current_user.draft_seats if x.draft.complete]
    return render_template(
        'index.html',
        active=active_seats,
        complete=complete_seats,
    )


@app.route("/cubes", methods=['GET', 'POST'])
@login_required
def cubes():
    form = NewCubeForm()

    if form.validate_on_submit():
        cube = Cube.query.filter(Cube.name==form.name.data).first()
        if cube is not None:
            flash('A Cube with the name "{}" already exists.'.format(cube.name))
            return redirect(url_for('cubes'))

        cube = Cube(name=form.name.data)
        db.session.add(cube)
        db.session.commit()
    
    cubes = Cube.query.all()
    return render_template(
        'cubes.html',
        active=[x for x in cubes if x.active],
        inactive=[x for x in cubes if not x.active],
        form=form
    )


# @app.route("/cards")
# @login_required
# def cards():
#     card_list = Card.query.all()
#     scar_list = Scar.query.all()

#     scars = {}
#     for scar in scar_list:
#         scars.setdefault(scar.card_id, []).append(scar.text)
        
#     return render_template('cards.html', cards=card_list, scars=scars)


# @app.route("/draft/<draft_id>")
# @login_required
# def draft(draft_id):
#     dw = DraftWrapper(draft_id, current_user)
#     return render_template(
#         'draft.html',
#         dw=dw,
#         draft=dw.draft,
#         seating=dw.seating,
#         user=dw.user,
#         pack=dw.pack,
#         pack_cards=dw.pack_cards(),
#         passing_to=dw.passing_to(),
#         scar_map=dw.scar_map,
#     )


# @app.route("/draft/<draft_id>/pick/<card_id>")
# @login_required
# def draft_pick(draft_id, card_id):
#     dw = DraftWrapper(draft_id, current_user)
#     dw.pick_card(card_id)
#     return redirect("/draft/{}".format(draft_id))


# @app.route("/draft/<draft_id>/force/<user_id>")
# @login_required
# def force_pick(draft_id, user_id):
#     user = User.query.get(user_id)
#     dw = DraftWrapper(draft_id, user)

#     # Don't apply any scar an advance.
#     if dw.is_scarring_round():
#         dw.unlock_new_scars()

#     # Pick the first card in the pack.
#     if dw.pack_cards():
#         dw.pick_card(dw.pack_cards()[0].id)
#     return redirect("/draft/{}".format(draft_id))

# @app.route("/draft/<draft_id>/scar/<card_id>/<scar_id>")
# @login_required
# def apply_scar(draft_id, card_id, scar_id):
#     dw = DraftWrapper(draft_id, current_user)
#     dw.apply_scar(card_id, scar_id)
#     return redirect("/draft/{}".format(draft_id))

# @app.route("/draft/<draft_id>/new_scars")
# @login_required
# def get_new_scars(draft_id):
#     dw = DraftWrapper(draft_id, current_user)
#     dw.these_scars_suck()
#     return redirect("/draft/{}".format(draft_id))

# @app.route("/draft/<draft_id>/debug")
# @login_required
# def draft_debug(draft_id):
#     draft_debugger = DraftDebugger(draft_id)
#     return render_template('draft_debug.html', d=draft_debugger)
