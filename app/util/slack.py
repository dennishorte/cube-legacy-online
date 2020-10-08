from slack import WebClient
from slack.errors import SlackApiError

from app.config import Config


_client = WebClient(token=Config.SLACK_BOT_TOKEN)

clo_channel = 'C01AV1RGJSK'


def send_your_pick_notification(user_id):
    try:
        open_response = _client.conversations_open(users=[user_id])
        dm_channel = open_response['channel']['id']

        send_response = _client.chat_postMessage(
            channel=dm_channel,
            text="Someone has passed you a pack. Time to make a pick."
        )
        
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")

    except Exception:
        # Don't crash the server because Slack notifications aren't working.
        pass


def test_direct_message():
    try:
        open_response = _client.conversations_open(users=['U3SHZPJF5'])
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
