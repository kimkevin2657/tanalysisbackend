'''
input: single query, list of candidate documents
output: ranks of candidate documents for the input query
'''

import numpy as np
import pandas as pd
import pickle
import os
import random
import torch
import torch.nn as nn
from transformers import BertPreTrainedModel, BertModel, BertTokenizerFast, AdamW
from colbert.modeling.colbert import ColBERT
from colbert.modeling.inference import ModelInference
from tqdm import tqdm

# due to some conflicting installations
os.environ['KMP_DUPLICATE_LIB_OK']='True'

# load model on CPU
checkpoint = torch.load("colbert-32000.dnn",map_location=torch.device('cpu'))
colbert = ColBERT.from_pretrained('bert-base-uncased',
                                   query_maxlen=512,
                                   doc_maxlen=512,
                                   dim=128,
                                   similarity_metric='cosine',
                                   mask_punctuation=True)
colbert.load_state_dict(checkpoint['model_state_dict'])
# inference mode
colbert.eval()
# wrapper
inference_bot = ModelInference(colbert=colbert)

def sort_tuple(tup):
    tup.sort(key=lambda x: x[1])
    return tup[::-1]

# calculate score given query and document embedding
def calculate_score(Q,D):
    score = Q@D.permute(0,2,1)
    score = score.max(1)
    score = score.values.sum(-1).cpu()
    return score

def extract_candidate_doc_embeddings(documents):
    d_embeddings = []
    for i in tqdm(range(len(documents)), position=0, leave=True):
        d = [documents[i]]
        d_embedding = inference_bot.docFromText(d)
        d_embeddings.append(d_embedding)
    return d_embeddings

def ranking_function(query, doc_embeddings):
    scores = [] # array of tuples, each tuple represents (index, score)
    query = [query]
    query_embedding = inference_bot.queryFromText(query)
    for j in range(len(doc_embeddings)):
        document_embedding = doc_embeddings[j]
        score = calculate_score(query_embedding, document_embedding)
        scores.append((j, score))
    ranks = sort_tuple(scores)
    return ranks

# example run
if __name__ == "__main__":
    # load test data
    test_df = pd.read_csv("test_df.tsv", sep="\t")
    # get query and candidate documents
    queries = test_df['queries'].values
    positive = test_df['positive'].values
    negative = test_df['negative'].values
    collections = np.concatenate([positive, negative])
    # we use the query with id 0 as an example
    # the positive sample for query with id i also has id i in collections
    # there could be more positives for query with id i, and you can find their information in query_positive_dict.pkl
    # i.e. positive sample for queries[0] is collections[0]
    # we test with 200 candidate documents - it takes too long to calculate document embeddings using CPU
    query, candidates = queries[0], collections[:200]
    # extract candidate document embeddings
    doc_embeddings = extract_candidate_doc_embeddings(candidates)
    ranks = ranking_function(query, doc_embeddings)

    print("========== Top 100 documents ==========")
    for i, tup in enumerate(ranks):
        if i == 100:
            break
        print("Top {}: id={}, score={}".format(i, tup[0], tup[1]))
