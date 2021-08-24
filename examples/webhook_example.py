# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# Author: Michael Maring                                                                          #
# Date:   8/16/21                                                                                 #
#                                                                                                 #
# Purpose: Example Python Twitch Webhook Code                                                     #
# Description: This code listens for channel follows for moonmoon                                 #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# Find alternate webhook events at https://dev.twitch.tv/docs/eventsub/eventsub-reference#events  #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

import requests
import json
import hmac
import hashlib
from flask import Flask, request

app = Flask(__name__)

# Flask Server Application
# Flask is used here to make a server that can interface with python. This is only on your local
#   network. The flask server will speak to the ngrok server, which will speak externally with Twitch.
@app.route('/webhook', methods=['POST'])
def respond():
    req = request.get_json()

    # return challenge and verify signature to finalize webhook subscription
    if 'challenge' in req:

        code = verify_signature(request.headers, request.get_data())

        if code == '403':
            return "Incorrect Webhook Signature"

        return request.get_json()['challenge']

    return 'ok'


def verify_signature(header, body):
    # reference https://dev.twitch.tv/docs/eventsub#verify-a-signature
    salt = header['Twitch-Eventsub-Message-Id'].encode('utf-8') + \
           header['Twitch-Eventsub-Message-Timestamp'].encode('utf-8') + \
           body

    # - - - - - - - - - - - - - - - - - - - REPLACE THIS HERE - - - - - - - - - - - - - - - - - - - #
    with open('../../not4github/app_credentials.json') as f:
        data = json.load(f)
    webhook_key = data['markov_chain_bot']['webhook_key']
    # - - - - - - - - - - - - - - - - - - - REPLACE THIS HERE - - - - - - - - - - - - - - - - - - - #

    if not isinstance(webhook_key, bytes):
        webhook_key = webhook_key.encode('utf-8')
    if not isinstance(salt, bytes):
        salt = salt.encode('utf-8')

    my_hash = 'sha256=' + hmac.new(webhook_key, salt, hashlib.sha256).hexdigest()

    if my_hash != header['Twitch-Eventsub-Message-Signature']:
        return '403'

    return

# Grab the ngrok tunnel url automatically
def get_tunnel():
    req = requests.get("http://localhost:4040/api/tunnels")
    name = req.json()['tunnels'][0]['public_url']

    # check if you got the https url (not always the same order/listed first)
    if name[4] != 's':
        name = name[:4] + 's' + name[4:]

    return name


if __name__ == "__main__":

    # your client id and secret can be found by clicking manage on your registered application in the
    #   applications tab on the twitch developer console.  Don't upload your secret to Github :)

    # - - - - - - - - - - - - - - - - - - - REPLACE THIS HERE - - - - - - - - - - - - - - - - - - - #
    with open('../../not4github/app_credentials.json') as f:
        data = json.load(f)
    client_id = data['markov_chain_bot']['client_id']
    client_secret = data['markov_chain_bot']['client_secret']
    webhook_key = data['markov_chain_bot']['webhook_key']
    # - - - - - - - - - - - - - - - - - - - REPLACE THIS HERE - - - - - - - - - - - - - - - - - - - #

    broadcaster_id = '121059319'  # moonmoon


    # reference https://dev.twitch.tv/docs/authentication/getting-tokens-oauth#oauth-client-credentials-flow
    url_auth = 'https://id.twitch.tv/oauth2/token?client_id={}&' \
               'client_secret={}&grant_type=client_credentials'.format(client_id, client_secret)

    # This is your authentication token
    # This does not include any oauth scopes. As such its use is limited to certain
    # types of webhooks (user follows, stream on/off, etc)
    token = requests.post(url_auth).json()['access_token']

    # This is where you post your Twitch EventSub requests
    # reference: https://dev.twitch.tv/docs/eventsub
    url_post = 'https://api.twitch.tv/helix/eventsub/subscriptions'

    # ngrok reference: https://ngrok.com/
    # ngrok provides a public (accessible by the webhook) url that you can use to connect to your local flask server
    #
    # As per EventSub standards you must use port 443 and https forwarding url
    #    port 8443 is an alternative to 443 because 443 is protected and can't be used without root privileges
    # download ngrok then launch it using the command in the terminal:
    #    ./ngrok http 8443
    callback = get_tunnel() + '/webhook'  # This is your ngrok url + /webhook

    # format reference: https://dev.twitch.tv/docs/eventsub#verify-a-signature
    header = {'Client-ID': client_id,
              'Authorization': 'Bearer ' + token,
              'Content-Type': 'application/json'
              }
    param = \
        {
            "type": "channel.follow",
            "version": "1",
            "condition": {
                "broadcaster_user_id": broadcaster_id
            },
            "transport": {
                "method": "webhook",
                "callback": callback,
                "secret": webhook_key
            }
        }

    param = json.dumps(param)  # must be json object

    # make the post request to get your webhook subscription
    req = requests.post(url_post, param, headers=header)

    app.run(port=8443)
