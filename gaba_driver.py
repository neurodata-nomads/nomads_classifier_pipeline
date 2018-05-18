import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier


def get_cubes(raw_data, centroids):
    """
    Parameters
    ----------
    raw_data : dict
        Each key represents channel and value represents raw data
    centroids : list
        In [z, y, x] format
    """
    """exclude_list = ['dapi', 'mbp']
    channels = [x for x in raw_data.keys() if x.lower() not in exclude_list]
    channels = list(raw_data.keys())"""

    channels, _ = get_channels(raw_data.keys())

    max_size = raw_data[channels[0]].shape
    centroids = np.array(centroids)

    cube_size = (7, 4, 4)  # Results in 15 x 9 x 9 cubes
    out = []
    ids = []


    for row in centroids:
        cubes = []
        z, y, x = row
        z_idx = (z - cube_size[0], z + cube_size[0] + 1)
        y_idx = (y - cube_size[1], y + cube_size[1] + 1)
        x_idx = (x - cube_size[2], x + cube_size[2] + 1)

        if (z_idx[0] >= 0) and (y_idx[0] >= 0) and (x_idx[0] >= 0) and (
                    z_idx[1] <= max_size[0]) and (y_idx[1] <= max_size[1]) and (
                        x_idx[1] <= max_size[2]):
            ids.append(1)
        else:
            ids.append(0)

        for chan in channels:
            data = raw_data[chan]
            z_idx = (z - cube_size[0], z + cube_size[0] + 1)
            y_idx = (y - cube_size[1], y + cube_size[1] + 1)
            x_idx = (x - cube_size[2], x + cube_size[2] + 1)

            # Dont deal with cubes on the edge of data
            if (z_idx[0] >= 0) and (y_idx[0] >= 0) and (x_idx[0] >= 0) and (
                    z_idx[1] <= max_size[0]) and (y_idx[1] <= max_size[1]) and (
                        x_idx[1] <= max_size[2]):
                cube = data[z_idx[0]:z_idx[1], y_idx[0]:y_idx[1], x_idx[0]:
                            x_idx[1]]
                cubes.append(cube)

        # Flatten array
        if len(cubes) != 0:
            out.append(np.array(cubes, dtype=np.uint8).ravel())

    return np.array(out, dtype=np.uint8), np.asarray(ids)


def get_channels(dict_keys):
    include_list = [
        'GABA', 'GAD', 'Gephyrin', 'GluN', 'PSD', 'synapsin', 'TdTomato',
        'VGlut'
    ]

    out_include_list = []
    out = []

    for include_key in include_list:
        for input_key in dict_keys:
            if include_key.lower() in input_key.lower():
                out.append(input_key)
                out_include_list.append(include_key)
                break

    return out, out_include_list

def create_channel(dimensions, centroids):
    data = np.zeros(dimensions, dtype=np.uint8)

    for row in centroids:
        z, y, x = row
        data[z - 7:z + 7, y - 4:y + 4, x - 4:x + 4] = 255

    return data


def gaba_classifier_pipeline(raw_data, centroids):
    """
    Parameters
    ----------
    raw_data : dict
        Each key represents channel and value represents raw data
    centroids : list
        In [z, y, x] format
    """
    X, ids = get_cubes(raw_data, centroids)
    centroids = np.array(centroids)
    channels = [x for x in raw_data.keys()]
    channels = list(raw_data.keys())
    max_size = raw_data[channels[0]].shape

    components = np.load('./components.npy')

    # Some data managing
    if X.shape[1] > components.shape[1]:
        X = X[:, :components.shape[1]]
    elif X.shape[1] < components.shape[1]:
        components = components[:, :X.shape[1]]

    X = X @ components.T

    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)

    predictions = model.predict(X)

    # gaba_centroids = centroids[predictions == 1]
    # ext_centroids = centroids[predictions == 0]

    # gaba_channel = create_channel(max_size, gaba_centroids)
    # ext_channels = create_channel(max_size, ext_centroids)

    # Relabel things
    pointer = 0
    print('ids: ', ids)
    for idx, val in enumerate(ids):
        if val == 1:
            if predictions[pointer] == 1:
                ids[val] = 2
            pointer += 1

    return ids
