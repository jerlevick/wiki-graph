import numpy as np
import scipy as sp
import networkx as nx
import pylab as pylab
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min
import matplotlib as mpl
import json
import scipy.linalg.interpolative as sli
import functools
from gensim.test.utils import common_texts
from gensim.models import Word2Vec
import gensim.downloader as api

def project_graph(G, dim, condition = None):
    """A function to project a graph into a set of points in dim-dimensional space. These points can then be clustered later.
    
    We use the normalized, random-walk Laplacian (aka transition matrix) of the graph as that generally has better properties--we can search
    for large eigenvalues rather than small, and it implicitly normalizes cluster sizes so that, essentially, it measures closeness of clusters
    by how likely a random walk is to stay in a cluster vs to leave. 

    The transition matrix is T = D^{-1}A where D is the degree matrix, and A the adjacency matrix. Then t_{ij} is the probability of taking a 
    step from node i to node j. Note that the if Tv = lambda v, then (I-T)v = (1-lambda)v so the ordering of the eigenvalues of T is the reverse
    of the ordering of the eigenvalues of I - T; then D(I-T) = D - A = L is the regular Laplacian, so this finds 'weighted' eigenvectors of the Laplacian.

    By find the top dim eigenvectors of T, we are equivalently then finding the bottom dim weighted eigenvectors of L, and if these eigenvectors
    are v_i, with entries v_{ij}, we map node j to the vector (v_{ij})_{i=1}^dim.

    Parameters
    -------------------------------
    G : A NetworkX graph
        The input graph for which we want to do the analysis 
    dim : int 
        The dimension of the vector space to project the points to. 
    
    """
    n = len(G.nodes)
    A = nx.adj_matrix(G) 
    D_inv = sp.sparse.csr_matrix(sp.sparse.spdiags([float(i) for i in 1/A.sum(axis=1)], 0, n, n))
    T = D_inv*A
    T = sp.sparse.csr_matrix(T)
    try:
        evals, evecs = sp.sparse.linalg.eigsh(T, dim)

    
    except RuntimeError or RuntimeWarning:
        if not condition:
            condition = 10**(-8)
            T += condition * sp.eye(n)
            evals, evecs = sp.sparse.linalg.eigsh(T, dim)
        
    return evecs

def get_clusters(nodes, labels):
    """Returns a dictionary of cluster labels as keys with values the list of associated nodes in that cluster
    
    Parameters
    ---------------------

    nodes : NewtorkX nodes object
            Usually will be G.nodes for the original graph
    lables : Iterable of label assignments from a clustering algorithm
            Usually will be kmeans.labels_ or something of the sort
    """
    return {j: list(np.array(nodes)[[i == j for i in labels]]) for j in set(labels)}


def get_cluster_categories(clusters, category_dict):
    """Returns a dictionary whose keys are the clusters, and whose values are a list of all categories of nodes in that cluster, obtained from 
    a node-keyed dictionary of clusters
    
    Parameters
    ------------------------
    clusters : Dict
            A dictionary like the output of get_clusters, keyed by cluster indices and valued with lists of nodes in the cluster
    category_dict : Dict
            A dictionary keyed by nodes, and valued with lists of all categories associated to each node
    """
    return  {j: functools.reduce(lambda x, y: x + y, (category_dict[k] if k in category_dict else [] for k in clusters[j])) for j in clusters}

def get_cluster_names(cluster_categories, cluster_centers):
    """A function to use word2vec to look at the cluster categories and try and name each cluster
    
    Parameters
    ----------------------
    clusters: Dict
            A dictionary like the output of get_clusters, keyed by cluster_indices and valued with lists of nodes in the cluster
    cluster_centeres: Dict
            A dictionary like the second output of find_clusters, with the most central cluster from the kmeans algorithm as the representative
            of each cluster

    Uses gensim's pre-trained glove-wiki-gigaword-300 word2vec model to find a word2vec vector to name each cluster
    """
    
    cluster_names = dict()
    model = api.load("glove-wiki-gigaword-300")
    
    for i in cluster_categories:
        words = ([word.lower() for cat in cluster_categories[i] for word in cat.split(' ')]
                    + [word.lower() for title in clusters[i] for word in title.split(' ')])
        if i in cluster_centers and cluster_centers[i][1]:
            words += [word.lower() for cat in cluster_centers[i][1] for word in cat.split(' ')] 
        
        avg_vect = np.zeros(300)
        count = 0
        
        for word in words:
            try:
                avg_vect += model.get_vector(word)
                count += 1
            except KeyError:
                pass
            
        
        avg_vect /= count
        cluster_names[i] = avg_vect

    return cluster_names

def make_cluster_graph(G, clusters):
    """Makes a new graph of the connectivity between clusters, based on the original graph G, and the clusters.
    
    Parameters
    ---------------
    G : NetworkX graph
        The original graph from which the clusters derive
    clusters : Dict
        The dictionary whose keys are cluster indices and values are lists of all nodes in each cluster
    """

    new_G = {i : [] for i in range(len(clusters))}
    for node1, node2 in G.edges:
        i = [node1 in clusters[k] for k in clusters].index(True)
        j = [node2 in clusters[k] for k in clusters].index(True)
        new_G[i].append(j)
        new_G[j].append(i)

    return new_G


def find_clusters(projected_graph, G, category_dict):
    """A function to take a given graph, the projection of it into a lower dimensional space via a spectral projection, and a dictionary of 
    categories for each node in the graph, to perform kmeans clustering on the spectral projection, and return the cluster labels for each node
    and the central node for each cluster
    
    Parameters
    ---------------------
    projected_graph: Array
            Like the output of project_graph; this is a truncation of the lowest-modulus eigenvectors which function as a low-dimensional
            representation of the nodes in the graph. KMeans clustering is performed on these points to create clusters
    G : NetworkX graph object
            The graph of which projected_graph is the projection; useful for finding cluster_centers
    category_dict : Dict
            Used to return a dictionary keyed by clusters, and whose values are the cluster center, and the categories corresponding 
            to the cluster center
    """
    kmeans = KMeans(n_clusters=1000)
    kmeans.fit(projected_graph)
    cluster_centers = dict()
    for i in set(kmeans.labels_):
        points = projected_graph[[j for j in range(len(kmeans.labels_)) if kmeans.labels_[j] == i]]
        center = sum(points) / len(points)
        closest = pairwise_distances_argmin_min(points, center.reshape(1,-1), axis=0)
        idx = [j for j in range(len(kmeans.labels_)) if kmeans.labels_[j] == i][closest[0][0]]
        center = list(G.nodes)[idx]
        try:
            cluster_centers[i] = (center, category_dict[center])
        except KeyError:
            cluster_centers[i] = (center, None)

    return kmeans.labels_, cluster_centers