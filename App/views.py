# from App import app
# from App import r
# from App import q
import os
import secrets
import time
from flask import render_template, request, Blueprint, redirect, url_for
from tasks import load_info
#from gensim.test.utils import common_texts
#from gensim.models import Word2Vec
#import gensim.downloader as api
import json
import numpy as np
import networkx as nx
from networkx.readwrite import json_graph
from sklearn.metrics import pairwise_distances_argmin_min
import requests
#from rq import Queue
#from worker import conn

#q = Queue(connection=conn)

views = Blueprint('views',__name__)

def load_info():
    """We load all the data we will need; most importantly the gensim word2vec model"""

    with open('answer_dict.json') as json_file:
        subject_dict = json.load(json_file)
    
    return subject_dict

@views.route('/')
def home():
    
    # jobs = q.jobs

    # task = q.enqueue(load_info)

    subject_dict = load_info()
           
    
    if not request.args.get("subject"):
        return render_template('home.html', subject_dict=subject_dict)
    
    subject = request.args.get("subject")
    top_ten = subject_dict[subject]
    return render_template('results.html', subject_dict=subject_dict, top_ten=top_ten)




        




