from datetime import datetime

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
from app.models.draft_models import *
from app.models.game_models import *
from app.util import name_generator
from app.util import slack
from app.util.cube_wrapper import CubeWrapper
from app.util.deck_builder import DeckBuilder
from app.util.deck_info import DeckInfo
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
            game_id=game_id,  # Used by header.html
            game=game,
            game_state=game.state,
            num_players=len(game.state.players),

            genform=GameEditNameForm(),
        )

    else:
        # Deck Builder
        draft = game.linked_draft()
        deck_info = draft.info().deck_info(current_user)

        # Output
        return render_template(
            'game_lobby.html',
            game_id=game_id,
            game_state=game.state,

            apform=SelectPlayerForm.factory(),
            genform=GameEditNameForm(),
            rform=GameDeckReadyForm(),

            draft=draft,
            deck_info=deck_info,
        )


@app.route("/game/<game_id>/add_player", methods=['POST'])
@login_required
def game_add_player(game_id):
    form = SelectPlayerForm.factory()

    if form.validate_on_submit():
        game = Game.query.get(game_id)
        game.add_player_by_name(form.players.data)  # Commited internally
        slack.send_new_game_notifications(game, form.players.data)

    return redirect(url_for('game', game_id=game_id))


@app.route("/game/<game_id>/delete")
@login_required
def game_delete(game_id):
    GameUserLink.query.filter(GameUserLink.game_id == game_id).delete()
    GameDraftLink.query.filter(GameDraftLink.game_id == game_id).delete()
    GameDraftV2Link.query.filter(GameDraftV2Link.game_id == game_id).delete()
    Game.query.filter(Game.id == game_id).delete()
    db.session.commit()

    flash("Game deleted")

    return redirect(url_for('index'))


@app.route("/game/draft_fight/<draft_id>/<opp_id>")
@login_required
def game_draft_fight(draft_id, opp_id):
    draft = Draft.query.get(draft_id)
    opp = User.query.get(opp_id)
    sassy_phrase = name_generator.generate()

    game = Game.factory(
        name = f"{current_user.name} vs. {opp.name} - {draft.name} - {sassy_phrase}",
        players = [current_user, opp],
    )

    link = GameDraftLink(draft_id=draft_id, game_id=game.id)
    db.session.add(link)
    db.session.commit()

    return redirect(url_for('game', game_id=game.id))


@app.route("/game/draft_v2_fight/<draft_id>/<opp_id>")
@login_required
def game_draft_v2_fight(draft_id, opp_id):
    from app.models.draft_v2_models import DraftV2

    draft = DraftV2.query.get(draft_id)
    opp = User.query.get(opp_id)
    sassy_phrase = name_generator.generate()

    game = Game.factory(
        name = f"{draft.name} - {sassy_phrase}",
        players = [current_user, opp],
    )
    db.session.add(game)

    link = GameDraftV2Link(draft_id=draft_id, game_id=game.id)
    db.session.add(link)
    db.session.commit()

    return redirect(url_for('game', game_id=game.id))


@app.route("/game/<game_id>/edit_name", methods=["POST"])
@login_required
def game_edit_name(game_id):
    form = GameEditNameForm()
    if form.validate_on_submit():
        if len(form.new_game_name.data.strip()) == 0:
            raise ValueError('Invalid game name')

        game = Game.query.get(game_id)
        state = game.state
        state.data['name'] = form.new_game_name.data.strip()
        game.update(state)

    return redirect(url_for('game', game_id=game_id))


@app.route("/game/next")
@login_required
def game_next():
    waiting_games = current_user.waiting_games()
    if not waiting_games:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('game', game_id=waiting_games[0].id))


@app.route("/game/new")
@login_required
def game_new():
    game = Game.factory(
        name = f"{current_user.name}'s game",
        players = [current_user],
    )

    return redirect(url_for('game', game_id=game.id))


@app.route("/game/<game_id>/ready", methods=["POST"])
@login_required
def game_ready(game_id):
    form = GameDeckReadyForm()

    if not form.validate_on_submit():
        raise RuntimeError("Error validating GameDeckReadyForm")

    deck_info = DeckInfo(json.loads(form.deck_json.data), {})
    game = Game.query.get(game_id)
    state = game.state
    player = state.player_by_id(current_user.id)
    player.ready_to_start = True

    basics = [state.make_card(x) for x in deck_info.basic_ids()]
    maindeck = [state.make_card(x) for x in deck_info.maindeck_ids()]
    sideboard = [state.make_card(x) for x in deck_info.sideboard_ids()]
    command = [state.make_card(x) for x in deck_info.command_ids()]

    state.load_deck(
        player_id = player.id,
        maindeck = maindeck + basics,
        sideboard = sideboard,
        command = command,
    )

    if state.ready_to_start():
        state.start_game()
        state.set_phase(GamePhase.untap)

    game.update(state)

    return redirect(url_for('game', game_id=game_id))


@app.route("/game/<game_id>/rematch")
@login_required
def game_rematch(game_id):
    game = Game.query.get(game_id)

    new_game = Game.factory(
        name = game.state.name + '+',
        players = [x.user for x in game.user_links],
    )

    linked_draft = game.linked_draft()
    if linked_draft:
        new_link = GameDraftV2Link(game_id=new_game.id, draft_id=linked_draft.id)
        db.session.add(new_link)

    db.session.commit()

    return redirect(url_for('game', game_id=new_game.id))


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

        if game.state.is_finished() and not game.completed_timestamp:
            game.completed_timestamp = datetime.utcnow()
            db.session.add(game)
            db.session.commit()

        slack.send_your_turn_in_game_notification(game)
        return "saved"


@app.route("/game_test")
@login_required
def game_test():
    from app.util.test_state import test_state
    return render_template(
        'game.html',
        test_state=test_state,
    )
