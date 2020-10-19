from datetime import datetime
from urllib.parse import urlparse

from flask import request
from slack import WebClient
from slack.errors import SlackApiError

from app import db
from app.config import Config


_client = WebClient(token=Config.SLACK_BOT_TOKEN)

clo_channel = 'C01AV1RGJSK'


def send_your_pick_notification(user, draft):
    if Config.FLASK_ENV != 'production':
        return

    try:
        open_response = _client.conversations_open(users=[user.slack_id])
        dm_channel = open_response['channel']['id']

        domain_host = urlparse(request.base_url).hostname
        draft_url = f"http://{domain_host}/draft/{draft.id}"
        message = f"Someone has passed you a pack in {draft.name}. Time to <{draft_url}|make a pick>."
        
        if not user.should_send_notification():
            message += "\nThis message would be filtered if the filter were turned on."    

        send_response = _client.chat_postMessage(
            channel=dm_channel,
            text=message,
        )

    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")

    except Exception:
        # Don't crash the server because Slack notifications aren't working.
        return

    user.last_notif_timestamp = datetime.utcnow()
    db.session.add(user)
    db.session.commit()


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
