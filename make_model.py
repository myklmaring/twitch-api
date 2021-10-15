import itertools
import numpy as np
import os
import json
import pickle as pkl

channel = 'admiralbulldog'
path = 'logs/' + channel + '/'
files = os.listdir(path)

corpus = []
vocab = {}

for file in files:
    with open(path + file) as f:
        mydict = json.load(f)

    for user in mydict['users'].keys():
        corpus.append(mydict['users'][user]['logs'])

corpus = list(itertools.chain.from_iterable(corpus))
corpus = [sent.split() for sent in corpus]
vocab_list = list(itertools.chain.from_iterable(corpus))

# need to add some sentence filtering for commands (!mmr, !g)
#   and channel bots (e.g. Nightbot, 9kmmrbot, ayayabot, moobot)
# remove garbage words as well

for word in vocab_list:
    vocab[word] = vocab.get(word, 0) + 1

# We want to filter out infrequently used words because there aren't sufficient examples to model the behavior properly
#    This can also be used to model unknown words in sentence seeds provided by people using the command in twitch chat
#    I keep track of the commonly used ones because there are many more infrequent ones

threshold = 3
freq = set()
unk = {}
for key, counts in vocab.items():
    if counts > threshold:
        freq.add(key)

for sent in corpus:
    for word1, word2 in zip(sent[:-1], sent[1:]):
        if word1 not in freq and word2 in freq:                         # don't want UNK to UNK transition
            unk[word2] = unk.get(word2, 0) + 1

# eliminate infrequent words
corpus = [[word for word in sent if word in freq] for sent in corpus]
corpus = [sent for sent in corpus if sent != []]

# remove short sentences (i.e. only one word)
corpus = [sent for sent in corpus if len(sent) > 1]

# Count tuples of (t-1, t)
transition = {}
for sent in corpus:
    prevWord = sent[1]
    for word in sent[1:]:
        transition[(prevWord, word)] = transition.get((prevWord, word), 0) + 1
        prevWord = word

first = {}      # dictionary of words that begin sentences
last = {}       # dictionary of words that terminate sentences
for sent in corpus:
    first[sent[0]] = first.get(sent[0], 0) + 1
    last[sent[-1]] = last.get(sent[-1], 0) + 1

# convert dictionaries into numpy arrays
vocabSort = sorted(list(vocab))
N = len(vocabSort)

firstMat = np.zeros((N, 1))
lastMat = np.zeros((1, N))
transMat = np.zeros((N + 1, N + 1))                                 # extra row for UNK, extra col for END

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

# normalize matrices
firstMat /= np.sum(firstMat, axis=0)
transMat /= (np.sum(transMat, axis=0) + np.finfo(float).eps)        # add machine precision so not div by 0

# k-Smoothing
k = 0.0005
transMat += k
transMat[N, N] = 0                                                  # Don't smooth UNK, END Transition
transMat /= np.sum(transMat, axis=0)

print('Model Complete')

file = 'model.pkl'
with open(file, 'wb') as f:
    pkl.dump(transMat, f)
