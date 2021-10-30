# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# Author: Michael Maring                                                              #
# Date:   9/16/21                                                                     #
#                                                                                     #
# Purpose: Example Python IRC Code                                                    #
# Description: Use IRC socket to save Twitch chat messages                            #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
import argparse
import time
import os
import requests
import json
from irc_commands import IRC


def chat_logger(irc, args):

    start = time.time()

    if args.duration > 0:
        end = start + args.duration
    else:
        end = float('inf')

    if args.save == 'true':
        if os.path.exists('irc_example_log.txt'):
            f = open('irc_example_log.txt', 'a')
        else:
            f = open('irc_example_log.txt', 'w')

    while True:
        line = irc.get_response()

        if args.save == 'true':
            f.write(line)
            f.write('\n')

        if args.verbose == 'true':
            print(line)

        if time.time() > end:
            break

    f.close()

    return

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--server", default="irc.chat.twitch.tv", type=str, help="server to connect to")
    parser.add_argument("--port", default=6667, type=int, help="port for irc client connection (if ssl, use 6697)")
    parser.add_argument("--channel", default="#admiralbulldog", type=str,
                        help="channel to connect to on Twitch, must be lower case and prefixed by #")
    parser.add_argument("--user", type=str, help="user profile ")
    parser.add_argument("--duration", type=float, help="length of time to run the program in seconds."
                                                       "Runs indefinitely if value is negative")
    parser.add_argument("--token", type=str, help="IRC chat token. This can be obtained at https://twitchapps.com/tmi/")
    parser.add_argument("--save", type=str, default='true', help="Save chat logs or not. Options are false or true.")
    parser.add_argument("--verbose", type=str, default='false', help="print output from twitch chat in terminal."
                                                                     "Options are false or true")
    parser.add_argument('--tags', dest='tag', action='store_true')
    parser.add_argument('--no-tags', dest='tag', action='store_false')
    parser.set_defaults(tag=False)

    args = parser.parse_args()

    # IRC Chat logger
    irc = IRC()
    irc.connect(args.server, args.port, args.user, args.token)
    irc.channel_join(args.channel, tag=args.tag)

    chat_logger(irc, args)

