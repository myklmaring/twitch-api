# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# Author: Michael Maring                                                              #
# Date:   8/16/21                                                                     #
#                                                                                     #
# Purpose: Example Python Twitch API Code                                             #
# Description: Finds the broadcaster ID for user with their channel name              #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
#      Find alternate API requests at https://dev.twitch.tv/docs/api/reference        #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


import json
import requests

# your client id and secret can be found by clicking manage on your registered application in the
#   applications tab on the twitch developer console.  Don't upload your secret to Github :)
with open('../../not4github/app_credentials.json') as f:
    data = json.load(f)

client_id = data['markov_chain_bot']['client_id']
client_secret = data['markov_chain_bot']['client_secret']

# reference https://dev.twitch.tv/docs/authentication/getting-tokens-oauth#oauth-client-credentials-flow
url_auth = 'https://id.twitch.tv/oauth2/token?client_id={}&' \
           'client_secret={}&grant_type=client_credentials'.format(client_id, client_secret)

# This is your authentication token
# This does not include any oauth scopes. As such its use is limited
token = requests.post(url_auth).json()['access_token']

# reference: https://dev.twitch.tv/docs/api/reference#get-users
url_get = 'https://api.twitch.tv/helix/users?login=qojqva'
header = {'Authorization': 'Bearer ' + token,
          'Client-ID': client_id}

# make the get request to find user ID
req = requests.get(url_get, headers=header)

print(req.json()['data'][0]['id'])
