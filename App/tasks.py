import json
import gensim.downloader as api

def load_info():
    """We load all the data we will need; most importantly the gensim word2vec model"""

    model = api.load("glove-wiki-gigaword-300")
    with open('community_graph_dict.json') as json_file:
        community_graph_dict = json.load(json_file)
    with open('cluster_names.json') as json_file:
        cluster_names = json.load(json_file)
    with open('cluster_centers.json') as json_file:
        cluster_centers = json.load(json_file)
    with open('category_dict.json') as json_file:
        category_dict = json.load(json_file)
    with open('clusters.json') as json_file:
        clusters = json.load(json_file)
    with open('titlelink.json') as json_file:
        title_link = json.load(json_file)
    
    return model, community_graph_dict, cluster_names, cluster_centers, category_dict, clusters, title_link

def make_community_graph(community_graph_dict):
    community_graph = nx.MultiGraph()
    for i in community_graph_dict:
        for j in community_graph_dict[i]:
            community_graph.add_edge(i,j)

def make_clust_names(cluster_names):
    return {k: np.array(cluster_names[k]) for k in cluster_names}