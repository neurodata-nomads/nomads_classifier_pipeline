import numpy as np
from skimage.measure import label
from skimage.filters import threshold_otsu
from scipy.ndimage.filters import convolve
from skimage.measure import block_reduce as pool


def compute_convolutional_cov(vol1, vol2, kernel_shape):
    mu_kernel = np.ones(kernel_shape)/float(np.sum(np.ones(kernel_shape)))
    e1 = convolve(vol1, mu_kernel)
    e2 = convolve(vol2, mu_kernel)

    e12 = convolve(vol1 + vol2, mu_kernel)
    cov = e12 - e1 + e2
    return cov


def remove_low_volume_predictions(label_img, thresh):
    keep_list = []
    for idx in np.unique(label_img):
        if not idx == 0:
            if(np.sum(label_img == idx)) > thresh:
                keep_list.append(idx)

    return np.isin(label_img, keep_list)


def z_transform(img):
    sigma = np.std(img)
    mu = np.average(img)
    return (img - mu)/sigma


def normalize_data(data):
    return np.stack([z_transform(chan) for chan in data])


def predict_from_feature_map(feature_map):
    foreground = feature_map > threshold_otsu(feature_map)
    predictions = label(foreground)
    return predictions
    
def pipeline(data, verbose=False):
    
    if verbose:
        print('Normalizing Data')
    normed_data = normalize_data(data)
    if verbose:
        print('Generating Covariance Map')
    cov_map = compute_convolutional_cov(normed_data[0],
                                        normed_data[1],
                                        (3, 3, 3))

    if verbose:
        print('Binarizing Covariance Map')
    predictions = predict_from_feature_map(cov_map)

    if verbose:
        print('Pruning Predictions')
    filtered_predictions = remove_low_volume_predictions(predictions, 30)
                                
    return filtered_predictions
