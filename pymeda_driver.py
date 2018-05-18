import numpy as np
import pandas as pd
from skimage import measure
from skimage import filters
import pymeda
import sys, os
import pickle

def label_predictions(result):
    synapse_labels = measure.label(result, background=0)
    connected_components = {}
    for z in range(synapse_labels.shape[0]):
        for y in range(synapse_labels.shape[1]):
            for x in range(synapse_labels.shape[2]):
                if (synapse_labels[z][y][x] in connected_components.keys()):
                    connected_components[synapse_labels[z][y][x]].append((z, y, x))
                else:
                    connected_components[synapse_labels[z][y][x]] = [(z, y, x)]
    connected_components.pop(0)
    return connected_components, synapse_labels

# Input: dictionary of connected_components
def calculate_synapse_centroids(connected_components):
    synapse_centroids = []
    for key, value in connected_components.items():
        z, y, x = zip(*value)
        synapse_centroids.append((int(sum(z)/len(z)), int(sum(y)/len(y)), int(sum(x)/len(x))))
    return synapse_centroids

# Data should be z transformed
def get_aggregate_sum(synapse_centroids, data):
    z_max, y_max, x_max = data[next(iter(data))].shape
    data_dictionary = dict((key, []) for key in data.keys())
    for centroid in synapse_centroids:
        z, y, x = centroid
        z_lower = z - 2
        z_upper = z + 2
        y_lower = y - 5
        y_upper = y + 5
        x_lower = x - 5
        x_upper = x + 5
        # prob a better way but w/e tired rn
        # ignore boundary synapses

        if z_lower < 0 or z_upper >= z_max:
            continue
        if y_lower < 0 or y_upper >= y_max:
            continue
        if x_lower < 0 or x_upper >= x_max:
            continue
        for key in data.keys():
            data_dictionary[key].append(np.sum(data[key][z_lower:z_upper, y_lower:y_upper, x_lower: x_upper]))
    return data_dictionary

def get_data_frame(data_dict):
    df = pd.DataFrame(data_dict)
    df = df.loc[:, (df != 0).any(axis=0)]
    return df

def pymeda_pipeline(predictions, raw_data, title = "PyMeda Plots", cluster_levels = 2, path = "./"):
    connected_components = label_predictions(predictions)[0]
    synapse_centroids = calculate_synapse_centroids(connected_components)
    features = get_aggregate_sum(synapse_centroids, raw_data)
    df = get_data_frame(features)
    sys.stdout = open(os.devnull, 'w')
    meda = pymeda.Meda(data = df, title = title, cluster_levels = cluster_levels)
    sys.stdout = sys.__stdout__
    #try:
    meda.generate_report(path)
    #except:
    #    print("Too many points, cannot generate plots. Fix incoming!")
    return
