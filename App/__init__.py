# __init__.py
from flask import Flask, request, render_template, Blueprint
from views import views 
#import redis 
import json
import networkx as nx
from networkx.readwrite import json_graph
#from gensim.test.utils import common_texts
#from gensim.models import Word2Vec
#import gensim.downloader as api
from sklearn.metrics import pairwise_distances_argmin_min
import numpy as np
#from rq import Worker, Queue, Connection
#from tasks import load_info

app = Flask(__name__)

#r = redis.Redis()
#q = Queue(connection=r)

