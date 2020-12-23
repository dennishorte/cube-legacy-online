from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import url_for
from flask_login import current_user
from flask_login import login_required

from app import app
from app.forms import *
from app.models.cube_models import *
from app.models.deck_models import *
from app.models.game_models import *
from app.util import slack
from app.util.deck_builder import DeckBuilder
from app.util.game_logic import GameCard
from app.util.game_logic import GamePhase
from app.util.game_logic import GameState

@app.route("/game/<game_id>")
@login_required
def game(game_id):
    game = Game.query.get(game_id)

    if game.state.ready_to_start():
        return render_template(
            'game.html',
            game_id=game_id,
            game_state=game.state,
            num_players=len(game.state.players),
        )

    else:
        dsform = DeckSelectorForm.factory(current_user.id)
        rform = GameDeckReadyForm()

        player = game.state.player_by_id(current_user.id)
        if player.has_deck():
            deck = Deck.query.get(player.deck_id)
            deck_builder = DeckBuilder(
                draft_id=deck.draft_id,
                user_id=current_user.id
            )
        else:
            deck_builder = None

        return render_template(
            'game_deck_selector.html',
            game_id=game_id,
            game_state=game.state,
            dsform=dsform,
            rform=rform,
            db=deck_builder,
        )


@app.route("/game/<game_id>/delete")
@login_required
def game_delete(game_id):
    Game.query.filter(Game.id == game_id).delete()
    db.session.commit()

    flash("Game deleted")

    return redirect(url_for('admin'))


@app.route("/game/next")
@login_required
def game_next():
    waiting_games = current_user.waiting_games()
    if not waiting_games:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('game', game_id=waiting_games[0].id))


@app.route("/game/new", methods=['POST'])
@login_required
def game_new():
    form = NewGameForm.factory()

    if form.validate_on_submit():
        game = Game()
        db.session.add(game)
        db.session.commit()

        game_state = GameState.factory(
            game_id=game.id,
            name=form.name.data.strip(),
            player_ids=[int(x) for x in form.players.data],
        )
        game.update(game_state)

        slack.send_new_game_notifications(game_state)

        return redirect(url_for('game', game_id=game.id))

    else:
        flash('Error creating game')
        return redirect(url_for('index'))


@app.route("/game/<game_id>/ready", methods=["POST"])
@login_required
def game_ready(game_id):
    form = GameDeckReadyForm()

    if not form.validate_on_submit():
        raise RuntimeError("Error validating GameDeckReadyForm")

    game = Game.query.get(game_id)
    state = game.state
    player = state.player_by_id(current_user.id)
    player.ready_to_start = True

    maindeck_ids = form.maindeck_ids.data.split(',')
    sideboard_ids = form.sideboard_ids.data.split(',')
    basic_lands = form.basics_list.data.split(',')

    sideboard_cards = []
    for id in sideboard_ids:
        if not id:
            continue
        sideboard_cards.append(state.make_card(id))

    maindeck_cards = []
    for id in maindeck_ids:
        if not id:
            continue
        maindeck_cards.append(state.make_card(id))

    basics_cube = Cube.query.filter(Cube.name == 'basic lands').first()
    basic_cards = {x.name(): x for x in basics_cube.cards()}
    for basic in basic_lands:
        if not basic:
            continue
        count, name = basic.split()
        for i in range(int(count)):
            maindeck_cards.append(state.make_card(basic_cards[name].id))


    state.load_deck(player.id, maindeck_cards, sideboard_cards)

    if state.ready_to_start():
        state.set_phase = GamePhase.untap

    game.update(state)

    return redirect(url_for('game', game_id=game_id))


@app.route("/game/save", methods=['POST'])
@login_required
def game_save():
    data = request.json
    game = Game.query.get(data['id'])

    # For backwards compatibility
    if not game.state.latest_version:
        data['latest_version'] = 1
        game.state.data['latest_version'] = 1

    # Prevent overwriting other updates due to race condition when both players submit save.
    if data['latest_version'] != game.state.latest_version:
        return "version conflict"

    # Update the game
    else:
        data['latest_version'] += 1
        game.update(data)
        slack.send_your_turn_in_game_notification(game.state_no_cache())
        return "saved"


@app.route("/game/<game_id>/select_deck", methods=["POST"])
@login_required
def game_select_deck(game_id):
    form = DeckSelectorForm.factory(current_user.id)

    if form.validate_on_submit():
        game = Game.query.get(game_id)
        state = game.state
        player = state.player_by_id(current_user.id)
        player.deck_id = int(form.deck.data)
        game.update(state)

    else:
        flash('Error on form submission')

    return redirect(url_for('game', game_id=game_id))


@app.route("/game_test")
@login_required
def game_test():
    from app.util.test_state import test_state
    return render_template(
        'game.html',
        test_state=test_state,
    )
