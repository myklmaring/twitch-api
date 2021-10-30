from irc_commands import *
import argparse
import re
import time


def main(args):

    flag = 1
    start = time.time()
    end = start + args.duration

    #####################   This is your command you are listening for   ################################
    command_pattern = r'!command (.+)'

    # (.+) is a capturing group that captures the remaining text after the !COMMAND
    ########################################################################################################

    while flag:

        # Sometimes get UnicodeDecodeError trying to process message from twitch
        try:
            line = irc.get_response()
        except UnicodeDecodeError:
            continue

        if args.verb:
            print(line)

        chat_pattern = r':([^\n\s]*?)!.*@.*.tmi.twitch.tv PRIVMSG #(.*) :(.*)'
        match = re.match(chat_pattern, line)

        # If IRC message is a chat message, check if it contains a command
        if match:

            chat_msg = match.groups()[2]

            # check for command
            match = re.match(command_pattern, chat_msg)

            # if there is a command, check for additional information
            if match:
                command = re.match(command_pattern, chat_msg).groups()[0]

                # Parse your command #
                print(command)
                ######################

                # echo command to twitch channel
                irc.send(args.channel, command)

            if time.time() > end:
                break

    return


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="irc.chat.twitch.tv", type=str, help="server to connect to")
    parser.add_argument("--port", default=6667, type=int, help="port for irc client connection (if ssl, use 6697)")
    parser.add_argument("--channel", default="#admiralbulldog", type=str,
                        help="channel to connect to on Twitch, must be lower case and prefixed by #")
    parser.add_argument("--user", type=str, help="user profile ")
    parser.add_argument("--duration", type=float, default=60,  help="duration for listening in seconds")
    parser.add_argument("--token", type=str, help="IRC chat token. This can be obtained at https://twitchapps.com/tmi/")
    parser.add_argument('--verbose', dest='verb', action='store_true')
    parser.set_defaults(verb=False)


    args = parser.parse_args()

    # IRC Chat logger
    irc = IRC()
    irc.connect(args.server, args.port, args.user, args.token)
    irc.channel_join(args.channel)

    main(args)
