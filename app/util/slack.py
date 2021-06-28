from datetime import datetime
from urllib.parse import urlparse

from flask import request
from flask_login import current_user
from slack import WebClient
from slack.errors import SlackApiError

from app import db
from app.config import Config
from app.models.user_models import *


_client = WebClient(token=Config.SLACK_BOT_TOKEN)

clo_channel = 'C01AV1RGJSK'


def send_new_game_notifications(game, name):
    state = game.state_no_cache()

    for player in state.players:
        if player.name != name or player.name == current_user.name:
            continue

        user = User.query.get(player.id)
        domain_host = urlparse(request.base_url).hostname
        game_url = f"http://{domain_host}/game/{game.id}"
        message = f"You've been invited to a new game, '{state.name}'. <{game_url}|Don't keep your opponent waiting!>."

        _send_slack_message(user, message)


def send_your_turn_in_game_notification(game):
    state = game.state_no_cache()

    if len(state.players) == 1:
        return

    next_player = state.priority_player()

    user = User.query.get(next_player.id)
    domain_host = urlparse(request.base_url).hostname
    game_url = f"http://{domain_host}/game/{game.id}"
    message = f"You have received priority in {state.name}. <{game_url}|Don't keep your opponent waiting!>."

    _send_slack_message(user, message)


def send_new_draft_notifications(draft):
    from app.models.draft_v2_models import DraftV2UserLink
    draft_user_links = DraftV2UserLink.query.filter(DraftV2UserLink.draft_id == draft.id).all()
    draft_users = [x.user for x in draft_user_links]

    for user in draft_users:
        domain_host = urlparse(request.base_url).hostname
        draft_url = f"http://{domain_host}/draft_v2/{draft.id}"
        message = f"A new draft, {draft.name}, has started. <{draft_url}|Come check it out>."

        _send_slack_message(user, message)


def send_your_pick_notification(user, draft):
    if not user.should_send_notification():
        return

    domain_host = urlparse(request.base_url).hostname
    draft_url = f"http://{domain_host}/draft_v2/{draft.id}"
    message = f"Someone has passed you a pack in {draft.name}. Time to <{draft_url}|make a pick>."

    if _send_slack_message(user, message):
        user.last_notif_timestamp = datetime.utcnow()
        db.session.add(user)
        db.session.commit()


def _send_slack_message(user, message):
    if Config.FLASK_ENV != 'production':
        return

    if not user.slack_id:
        return

    try:
        open_response = _client.conversations_open(users=[user.slack_id])
        dm_channel = open_response['channel']['id']

        send_response = _client.chat_postMessage(
            channel=dm_channel,
            text=message,
        )

        return True

    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got Slack error: {e.response['error']}")
        return False

    except Exception:
        # Don't crash the server because Slack notifications aren't working.
        print(f"Crashed when trying to send Slack message. user({user.name}). msg({message})")
        return False



def test_direct_message(user):
    try:
        open_response = _client.conversations_open(users=[user.slack_id])
        dm_channel = open_response['channel']['id']

        send_response = _client.chat_postMessage(
            channel=dm_channel,
            text="Hello, world!",
        )

    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")


def test_chat_message():
    # Docs: https://api.slack.com/methods/chat.postMessage
    try:
        response = _client.chat_postMessage(
            channel=_channel,
            text="Hello world!",
        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")
