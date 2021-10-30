import itertools
import numpy as np
import os
import json
import pickle as pkl
import re


def main(args):
    path = 'logs/' + args.channel + '/'
    files = os.listdir(path)

    corpus = []
    vocab = {}
    users_ignore = ['nightbot', '9kmmrbot', 'ayayayaboat', 'moobot', 'admiralbullbot', 'streamelements']

    for file in files:
        with open(path + file) as f:
            mydict = json.load(f)

        corpus = [mydict['users'][user]['logs'] for user in mydict['users'].keys() if user not in users_ignore]

    corpus = list(itertools.chain.from_iterable(corpus))

    corpus = [sent.split() for sent in corpus]
    vocab_list = list(itertools.chain.from_iterable(corpus))

    for word in vocab_list:
        vocab[word] = vocab.get(word, 0) + 1

    # We want to filter out infrequently used words because there aren't sufficient examples to model the behavior properly
    #    This can also be used to model unknown words in sentence seeds provided by people using the command in twitch chat
    #    I keep track of the commonly used ones because there are many more infrequent ones

    threshold = 3
    freq = set()
    for key, counts in vocab.items():
        if counts > threshold:
            freq.add(key)

    # command filtering (!mmr, !g)
    pattern = r'(!\w+)'
    commands = set()
    for word in freq:
        match = re.match(pattern, word)
        if match:
            commands.add(match.group(0))
    freq = freq.difference(commands)

    # garbage filtering
    garbage = {'\x01ACTION', '\x01'}
    freq = freq.difference(garbage)

    # Remove copies of words (e.g. hello, HELLO)

    # Remove hyperlinks

    # eliminate infrequent words
    corpus = [[word for word in sent if word in freq] for sent in corpus]
    corpus = [sent for sent in corpus if sent != []]
    vocab = {key: value for key, value in vocab.items() if key in freq}

    transition = {}
    first = {}      # dictionary of words that begin sentences
    last = {}       # dictionary of words that terminate sentences
    unk = {}        # dictionary of words that appear after unknown words

    for sent in corpus:

        if args.token:
            if len(sent) == 1:
                continue

        first[sent[0]] = first.get(sent[0], 0) + 1
        last[sent[-1]] = last.get(sent[-1], 0) + 1

        if len(sent) == 1:
            continue

        for word1, word2 in zip(sent[:-1], sent[1:]):
            if word1 not in freq and word2 in freq:     # don't want UNK to UNK transition
                unk[word2] = unk.get(word2, 0) + 1

        prevWord = sent[1]
        for word in sent[1:]:
            transition[(prevWord, word)] = transition.get((prevWord, word), 0) + 1
            prevWord = word

    # convert dictionaries into numpy arrays
    vocabSort = sorted(list(vocab.keys()))
    N = len(vocabSort)

    firstMat = np.zeros((N, 1))
    transMat = np.zeros((N + 1, N + 1))                                 # extra row for UNK, extra col for END (last)

    for key in transition.keys():
        index1 = vocabSort.index(key[0])
        index2 = vocabSort.index(key[1])
        transMat[index1, index2] = transition.get(key, 0)

    for key in unk.keys():
        index1 = vocabSort.index(key)
        transMat[N, index1] = unk.get(key, 0)

    for key in last.keys():
        index1 = vocabSort.index(key)
        transMat[index1, N] = last.get(key, 0)

    for key in first.keys():
        index1 = vocabSort.index(key)
        firstMat[index1, 0] = first.get(vocabSort[index1], 0)

    # normalize matrix rows
    firstMat /= np.sum(firstMat)
    transMat /= (np.sum(transMat, axis=1)[:, None] + np.finfo(float).eps)        # add machine precision so not div by 0

    # k-Smoothing
    k = args.ksmooth
    transMat += k
    transMat[N, N] = 0                                                  # Don't smooth UNK, END Transition
    transMat /= (np.sum(transMat, axis=1)[:, None] + np.finfo(float).eps)

    # Precompute Cumulative Sums
    firstMat = np.cumsum(firstMat, axis=0)
    transMat = np.cumsum(transMat, axis=1)

    print('Model Complete')
    data = {'transMat': transMat, 'firstMat': firstMat, 'vocabSort': vocabSort}

    file = 'model.pkl'
    with open(file, 'wb') as f:
        pkl.dump(data, f)

    return


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default="admiralbulldog", type=str, help="The channel to make markov model from")
    parser.add_argument("--ksmooth", default=0.0, type=float, help="Increase (higher) / Decrease (lower) low frequency"
                                                                   "token to token transition. Minimum of 0")
    parser.add_argument("--user-blacklist")
    parser.add-argument("--token-blacklist")
    parser.add_argument("--single", dest='token', action='store_true', help="Include single token sentences in the model")
    parser.set_defaults(token=False)

    main(args)
