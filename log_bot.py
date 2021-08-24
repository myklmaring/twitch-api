from irc_commands import *
import argparse
import time
import re
import random
import json
import requests
from flask import Flask, request
app = Flask(__name__)

# global variable to collect chat logs only while online
online = 0  # stream online/offline flag

def get_tunnel():
    req = requests.get("http://localhost:4040/api/tunnels")
    name = req.json()['tunnels'][0]['public_url']

    # check if you got the https url (not always the same order/listed first)
    if name[4] != 's':
        name = name[:4] + 's' + name[4:]

    return name


def create_dict():

    mydict = {
            'users': {
                'name': '',
                'id': '',
                'status': '',
                'logs': []
            },
            'metadata': []
        }

    year, month, day, _, _, _, _, _, _ = time.localtime(time.time())

    file = f'{channel}_{year}_{month}_{day}.json'

    with open(file) as f:
        json.dump(mydict, f)

    return mydict


def generate_token(client_id, client_secret):

    assert type(client_id) == str
    assert type(client_secret) == str

    url_auth = 'https://id.twitch.tv/oauth2/token?client_id={}&' \
               'client_secret={}&grant_type=client_credentials'.format(client_id, client_secret)

    token = requests.post(url_auth).json()['access_token']

    return token


def create_stream_webhook(token, client_id, broadcaster_id, event_type):
    url_post = 'https://api.twitch.tv/helix/eventsub/subscriptions'

    callback = get_tunnel() + '/webhook'

    header = {'Client-ID': client_id,
              'Authorization': 'Bearer ' + token,
              'Content-Type': 'application/json'
              }
    param = \
        {
            "type": event_type,
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

    req = requests.post(url_post, param, headers=header)

    return req.ok


def verify_signature(header, body, credentials):
    salt = header['Twitch-Eventsub-Message-Id'].encode('utf-8') + \
           header['Twitch-Eventsub-Message-Timestamp'].encode('utf-8') + \
           body


    assert isinstance(credentials, str)

    with open(credentials) as f:
        data = json.load(f)
    webhook_key = data['markov_chain_bot']['webhook_key']

    if not isinstance(webhook_key, bytes):
        webhook_key = webhook_key.encode('utf-8')
    if not isinstance(salt, bytes):
        salt = salt.encode('utf-8')

    my_hash = 'sha256=' + hmac.new(webhook_key, salt, hashlib.sha256).hexdigest()

    if my_hash != header['Twitch-Eventsub-Message-Signature']:
        return '403'

    return


@app.route('/webhook', methods=['POST'])
def respond():

    global online   # use global variable online
    req = request.get_json()

    # return challenge and verify signature to finalize webhook subscription
    if 'challenge' in req:
        file = '../not4github/app_credentials.json'
        code = verify_signature(request.headers, request.get_data(), file)

        if code == '403':
            return "Incorrect Webhook Signature"

        return request.get_json()['challenge']

    # webhook sends you info
    if 'event' in req:
        if req['subscription']['type'] == 'stream.online':
            online = 1
        if req['subscription']['type'] == 'stream.offline':
            online = 0

    return 'ok'


def chat_logger(irc, args):

    # open file if it exists, otherwise create the file/dictionary
    if args.output_file:
        with open(args.output_file, 'r') as f:
            mydict = json.load(f)
    else:
        with open(args.output_file, 'w') as f:
            mydict = create_dict()


    flag = 1
    while flag:
        line = irc.get_response()
        if verbose: print(line)

    pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--server", default="irc.chat.twitch.tv", type=str, help="server to connect to")
    parser.add_argument("--port", default=6667, type=int, help="port for irc client connection (if ssl, use 6697)")
    parser.add_argument("--channel", default="#admiralbulldog", type=str,
                        help="channel to connect to on Twitch, must be lower case and prefixed by #")
    parser.add_argument("--user", type=str, help="user profile ")
    parser.add_argument("--password", type=str, help="user oauth password, must be prefixed by oauth:"
                                                     "This can be obtained at https://twitchapps.com/tmi/.")
    parser.add_argument("--duration", type=float, help="length of time to run the program in seconds")
    parser.add_argument("--verbose", help="increases the amount of print-out")
    parser.add_argument("--output-file", type=str, help='json file for storing chat logs and metadata')

    args = parser.parse_args()

    token, header = generate_token(args.client_id, args.client_secret)

    # API style requests
    url_bulldog = 'https://api.twitch.tv/helix/streams?user_id=30816637'
    url_mason = ''
    streamer_id = {'admiralbulldog': '30816637',
                   'masondota2': '40754777',
                   'pyramid_spammer69': '644999039',
                   'sixtyeight_plus_one': '229530515'}

    ignore_patterns = {'':''}

    # IRC Chat logger
    irc = IRC()
    irc.connect(args.server, args.port, args.user, args.password)
    irc.channel_join(args.channel)

    # run the things
    app.run(port=8443)
    chat_logger(irc, args)
