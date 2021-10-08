from irc_commands import *
import argparse
import time
import re
import os
import random
import json
import requests
import hmac
import hashlib
from flask import Flask, request
from multiprocessing import Process

app = Flask(__name__)

def get_tunnel():
    req = requests.get("http://localhost:4040/api/tunnels")
    name = req.json()['tunnels'][0]['public_url']

    # check if you got the https url (not always the same order/listed first)
    if name[4] != 's':
        name = name[:4] + 's' + name[4:]

    return name


def generate_token(client_id, client_secret):

    assert type(client_id) == str
    assert type(client_secret) == str

    url_auth = 'https://id.twitch.tv/oauth2/token?client_id={}&' \
               'client_secret={}&grant_type=client_credentials'.format(client_id, client_secret)

    token = requests.post(url_auth).json()['access_token']

    return token


def create_stream_webhook(token, client_id, broadcaster_id, event_type, webhook_key):
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


def parse_line(line, tag=False):
    pattern = r':([^\n\s]*?)!.*@.*.tmi.twitch.tv PRIVMSG #(.*) :(.*)'
    data = {}

    print(line)
    print("\n")

    if tag:
        pattern1 = r'@badge-info=(.*);badges=(.*);(?:.*)color=(.*);display-name=(.*);emotes=(.*);flags=(.*);id=(.*);mod=(.*);' \
                   r'room-id=(.*);subscriber=(.*);tmi-sent-ts=(.*);turbo=(.*);user-id=(.*);user-type=(.*?) :'
        g = re.search(pattern, line)
        h = re.search(pattern1, line)

        if g:
            data['user-name'] = g.groups()[0]
            data['channel-name'] = g.groups()[1]
            data['msg'] = g.groups()[2].strip()

        if h:
            data['badge-info'] = h.groups()[0]
            data['badges'] = h.groups()[1]
            data['color'] = h.groups()[2]
            # data['display-name'] = h.groups[3]
            data['emotes'] = h.groups()[4]
            data['flags'] = h.groups()[5]
            data['id'] = h.groups()[6]
            data['mod'] = h.groups()[7]
            data['room-id'] = h.groups()[8]
            data['subscriber'] = h.groups()[9]
            data['tmi-sent-ts'] = h.groups()[10]
            data['turbo'] = h.groups()[11]
            data['user-id'] = h.groups()[12]
            data['user-type'] = h.groups()[13]

        return data

    else:
        g = re.match(pattern, line)

        if g:
            data['user-name'] = g.groups[0]
            data['channel-name'] = g.groups[1]
            data['msg'] = g.groups[2]

        return data


@app.route('/webhook', methods=['POST'])
def respond():

    global online   # use global variable online
    global file
    req = request.get_json()

    # return challenge and verify signature to finalize webhook subscription
    if 'challenge' in req:
        code = verify_signature(request.headers, request.get_data(), file)
        if code == '403':
            print("Incorrect Webhook Signature")

        return request.get_json()['challenge']

    # webhook sends you info
    if 'event' in req:
        if req['subscription']['type'] == 'stream.online':
            online = 1
            print('stream turned on')
        if req['subscription']['type'] == 'stream.offline':
            online = 0
            print('stream turned off')

    return 'ok'


def chat_logger(irc, args):
    global online  # use global variable online

    year, month, day, _, _, _, _, _, _ = time.localtime(time.time())
    file = args.savepath + f'/{args.channel[1:]}_{year}_{month}_{day}.json'

    # create dictionary if it does not already exist
    if os.path.exists(file):
        with open(file, 'r') as f:
            mydict = json.load(f)
    else:
        mydict = {'users': {},
                  'date': f'{day}_{month}_{year}',
                  'channel': args.channel}

    # Figure out when to stop running the chat logging
    start = time.time()
    if args.duration >= 0:
        end = start + args.duration
    else:
        end = float('inf')

    try:
        flag = 1
        while flag:

            # check if chat log collection has exceeded duration
            if time.time() > end:
                print('chat log collection duration exceeded')
                with open(file, 'w') as f:
                    json.dump(mydict, f)
                break

            line = irc.get_response()

            # # only store messages when stream is on
            if online:

                data = parse_line(line, tag=args.tag)

                if args.verb:
                    print(line)
                    print("\n")

                # check if line was a message
                if data.keys().__len__() == 0:
                    continue

                if args.tag:
                    # check if chatter is in dictionary, if not create an entry for them
                    if data['user-name'] not in mydict['users'].keys():
                        mydict['users'][data['user-name']] = {'id': data['user-id'],
                                                              'sub': data['subscriber'],
                                                              'mod': data['mod'],
                                                              'logs': []}

                    mydict['users'][data['user-name']]['logs'].append(data['msg'])

                else:
                    if data['user-name'] not in mydict['users'].keys():
                        mydict['users'][data['user-name']] = {'logs': []}

                    mydict['users'][data['user-name']]['logs'].append(data['msg'])

    # save dictionary upon exiting program on terminal
    except (KeyboardInterrupt, ConnectionResetError):
        with open(file, 'w') as f:  # save dictionary before exiting
            json.dump(mydict, f)
        print('chat log collection stopped manually')
        print('dictionary saved')

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
    parser.add_argument("--duration", type=float, help="length of time to run the program in seconds. Put (-1) if you "
                                                       "want to run it indefinitely")
    parser.add_argument("--broadcaster-id", type=str, help="ID of the channel")
    parser.add_argument('--savepath', type=str, default='logs', help='folder to save chat log output')

    parser.add_argument('--tags', dest='tag', action='store_true')
    parser.add_argument('--no-tags', dest='tag', action='store_false')
    parser.set_defaults(tag=False)
    parser.add_argument('--verbose', dest='verb', action='store_true')
    parser.add_argument('--no-verbose', dest='verb', action='store_false')
    parser.set_defaults(verb=False)

    args = parser.parse_args()

    # global variable to collect chat logs only while online
    online = 1  # stream online/offline flag
    file = '../not4github/app_credentials.json'

    with open(file) as f:
        data = json.load(f)
    client_id = data['markov_chain_bot']['client_id']
    client_secret = data['markov_chain_bot']['client_secret']
    webhook_key = data['markov_chain_bot']['webhook_key']

    # generate token and webhooks
    token = generate_token(client_id, client_secret)
    create_stream_webhook(token, client_id, args.broadcaster_id, 'stream.online', webhook_key)
    create_stream_webhook(token, client_id, args.broadcaster_id, 'stream.offline', webhook_key)
    print('webhooks created')

    # IRC Chat logger
    irc = IRC()
    irc.connect(args.server, args.port, args.user, args.password)
    irc.channel_join(args.channel, tag=args.tag)

    # run the things
    year, month, day, hour, min, sec, _, _, _ = time.localtime(time.time())
    print(f'starting chat log collection: date {day}/{month}/{year} | {hour}h : {min}m : {sec}s')

    keywords = {'port': 8443}
    p1 = Process(target=app.run, kwargs=keywords)
    p1.start()

    chat_logger(irc, args)

    # code terminates normally
    p1.terminate()
    p1.join()
