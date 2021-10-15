import pickle as pkl
import numpy as np

file = 'model.pkl'

with open(file, 'rb') as f:
    model = pkl.load(f)

