import itertools
import numpy as np
import os
import json

channel = 'admiralbulldog'
path = 'logs/' + channel
files = os.listdir(path)

corpus = []
vocab = {}
last = {}
first = {}

for file in files:
    with open(file) as f:
        mydict = json.load(f)

    for user in mydict['users'].keys():
        corpus.append(mydict[user]['logs'])

corpus = list(itertools.chain.from_iterable(corpus))
corpus = [sent.split() for sent in corpus]
vocab_list = list(itertools.chain.from_iterable(corpus))
vocab_set = set(list(itertools.chain.from_iterable(corpus)))

# need to add some sentence filtering for commands (!mmr, !g)
#   and channel bots (e.g. Nightbot, 9kmmrbot, ayayabot, moobot)

for word in vocab_set:
    vocab[word] = vocab_list.count(word)

for sent in corpus:
    first[sent[0]] = first.get(sent[0], 0) + 1
    last[sent[-1]] = last.get(sent[-1], 0) + 1


# We want to filter out infrequently used words because there aren't sufficient examples to model the behavior properly
#    This can also be used to model unknown words in sentence seeds provided by people using the command in twitch chat

# create set of words with counts less than your threshold
threshold = 3
infreqwords = set()
for key, counts in vocab.items():
    if counts < threshold:
        infreqwords.add(key)

# replace words in unfrequent set found in the data with UNKA
for i, sent in enumerate(data):
    for j, word in enumerate(sent[::2]):
        if word in unfreqWords:
            data[i][2*j] = 'UNKA'

