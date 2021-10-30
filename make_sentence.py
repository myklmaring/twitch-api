from irc_commands import *
import argparse
import pickle as pkl
import numpy as np
import re


def main(args):

    with open(args.model_path, 'rb') as f:
        data = pkl.load(f)

    firstMat = data['firstMat']
    transMat = data['transMat']
    vocabSort = data['vocabSort']

    flag = 1
    N = transMat.shape[1]
    pattern = r'!kek'
    pattern1 = r'!kek (.+)'
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
            match = re.match(pattern, chat_msg)
            if match:

                seed = re.match(pattern1, chat_msg)

                sent = []
                # user does not provide the start of the sentence
                if not seed:
                    sample = np.random.random()
                    ind = np.argmax(firstMat > sample)
                    sent.append(ind)

                # user provides the start of the sentence
                else:
                    seed = seed.groups()[0]
                    seed = seed.split()[-1]

                    # seed word in vocab, use word's row to initiate transition mat
                    if seed in vocabSort:
                        ind = vocabSort.index(seed)

                    # seed word was unknown, use UNK row in transition mat
                    else:
                        ind = N-1

                    sent.append(ind)

                # N-1 because of python indexing
                while sent[-1] != (N-1) and len(sent) < 50:
                    row = transMat[sent[-1], :]
                    sample = np.random.random()
                    sent.append(np.argmax(row > sample))

                # make sentence from vocab indexes
                sent = [vocabSort[index] for index in sent[:-1]]
                sent = ' '.join(sent)

                irc.send(args.channel, sent)

    return


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="irc.chat.twitch.tv", type=str, help="server to connect to")
    parser.add_argument("--port", default=6667, type=int, help="port for irc client connection (if ssl, use 6697)")
    parser.add_argument("--channel", default="#admiralbulldog", type=str,
                        help="channel to connect to on Twitch, must be lower case and prefixed by #")
    parser.add_argument("--user", type=str, help="user profile ")
    parser.add_argument("--token", type=str, help="user oauth password, must be prefixed by oauth:"
                                                     "This can be obtained at https://twitchapps.com/tmi/.")
    parser.add_argument("--model-path", default="model.pkl", type=str, help="path to markov model")
    parser.add_argument('--verbose', dest='verb', action='store_true')
    parser.set_defaults(verb=False)

    args = parser.parse_args()


    # IRC Chat logger
    irc = IRC()
    irc.connect(args.server, args.port, args.user, args.token)
    irc.channel_join(args.channel)

    main(args)
