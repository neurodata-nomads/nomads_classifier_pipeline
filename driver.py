from nomads import pipeline
from NeuroDataResource import NeuroDataResource
import pymeda_driver
import argparse
import pickle
import numpy as np
#import boto3, glob
from gaba_driver import gaba_classifier_pipeline
from nd_boss import boss_push
import csv
import logging
from traceback import print_exc
import intern.utils.parallel as intern
# pull data from BOSS

def get_data(host, token, col, exp, z_range, y_range, x_range):
    print("Downloading {} from {} with ranges: z: {} y: {} x: {}".format(exp,
                                                                         col,
                                                                         str(z_range),
                                                                         str(y_range),
                                                                         str(x_range)))
    resource = NeuroDataResource(host, token, col, exp)

    data_dict = {}
    blocks = intern.block_compute(x_range[0], x_range[1], y_range[0], y_range[1], z_range[0], z_range[1], (0, 0, 0), (5000, 5000, 20))
    orig_shape = (z_range[1] - z_range[0], y_range[1] - y_range[0], x_range[1] - x_range[0])
    for chan in resource.channels:
        test = resource.get_cutout(chan, [1, 50], [1, 50], [1, 50])
        type = test.dtype
        merged_array = np.zeros(orig_shape, dtype = type)
        for block in blocks:
            x_r, y_r, z_r = block
            merged_array[z_r[0] - z_range[0]:z_r[1] - z_range[0], y_r[0] - y_range[0]:y_r[1] - y_range[0], x_r[0] - x_range[0]:x_r[1] - x_range[0]] = \
            resource.get_cutout(chan, z_r, y_r, x_r)
        data_dict[chan] = merged_array
    return data_dict

# normalize data
def load_and_preproc(data_dict, z_transform=True):
    raw = data_dict
    if z_transform:
        for channel in raw.keys():
            #dont want to z transform annotations
            if channel != 'annotation':
                data = raw[channel]

                #get z transform stats
                for z_idx in range(data.shape[0]):
                    mu = np.mean(data[z_idx])
                    sigma = np.std(data[z_idx])
                    raw[channel][z_idx] = (raw[channel][z_idx] - mu)/sigma
    return raw

def format_data(data_dict):
    data = []
    for chan, value in data_dict.items():
        if "psd" in chan.lower() or "synapsin" in chan.lower():
            format_chan = []

            for z in range(value.shape[0]):
                raw = value[z]

                if (raw.dtype != np.dtype("uint8")):
                    info = np.iinfo(raw.dtype) # Get the information of the incoming image type
                    raw = raw.astype(np.float64) / info.max # normalize the data to 0 - 1
                    raw = 255 * raw # Now scale by 255
                    raw = raw.astype(np.uint8)
                #raw = pool(raw, (32, 32), np.mean)

                format_chan.append(raw)
            data.append(np.stack(format_chan))
    data = np.stack(data)
    return data

def run_nomads(data_dict):
    print("Beginning NOMADS Pipeline...")
    input_data = format_data(data_dict)
    results = pipeline(input_data)
    print("Finished NOMADS Pipeline.")
    return results
'''
def upload_results(bucket_key, path, results_key):
    client = boto3.client('s3')
    s3 = boto3.resource('s3')
    s3_bucket_exists_waiter = client.get_waiter('bucket_exists')
    bucket = client.create_bucket(Bucket=bucket_key)
    s3_bucket_exists_waiter.wait(Bucket=bucket_key)

    bucket = s3.Bucket(bucket_key)
    bucket.Acl().put(ACL='public-read')
    files = glob.glob(path+"*")
    for file in files:
        key = results_key + "/" + file.split("/")[-1]
        client.upload_file(file, bucket_key, key)
        response = client.put_object_acl(ACL='public-read', Bucket=bucket_key, \
        Key=key)

    return
'''
def split_vol_by_id(vol, ids, num_vols):
    outvols = [np.zeros_like(vol) for _ in range(num_vols)]
    for idx, outvol in enumerate(ids):
        num = idx+1
        locs = list(zip(*(np.where(vol == num))))
        for i, j, k in locs:
            outvols[outvol][i][j][k] = 1

    return outvols

## PLEASE HAVE / AT END OF PATH
## BETTER YET DONT TOUCH PATH
def driver(host, token, col, exp, z_range, y_range, x_range, path = "./results/"):
    print("Starting Nomads Classifier...")
    results_key = "_".join(["nomads-classifier", col, exp, "z", str(z_range[0]), str(z_range[1]), "y", \
    str(y_range[0]), str(y_range[1]), "x", str(x_range[0]), str(x_range[1])])

    info = locals()
    try:
        data_dict = get_data(host, token, col, exp, z_range, y_range, x_range)
    except Exception as e:
        logging.info("Failed to pull data from BOSS. Run with smaller cube of data or check if BOSS is online.")
        logging.info(e)
        logging.info("Exiting...")
        #upload_results(bucket, path, results_key)
        print_exc()
        return

    try:
        results = run_nomads(data_dict)
    except Exception as e:
        logging.info("Failed to run Nomads-Unsupervised detection algorithm on data.")
        logging.info(e)
        logging.info("Exiting...")
        #upload_results(bucket, path, results_key)
        print_exc()
        return

    results = results.astype(np.uint8)
    np.putmask(results, results, 255)

    pickle.dump(results, open(path + "nomads-unsupervised-predictions" + ".pkl", "wb"))
    print("Saved pickled predictions (np array) {} in {}".format("nomads-unsupervised-predictions.pkl", path))

    norm_data = load_and_preproc(data_dict)
    print("Running Nomads-classifier...")
    try:
        #results = pickle.load(open("results/nomads-unsupervised-predictions.pkl", "rb"))
        connected_components, label_vol = pymeda_driver.label_predictions(results)
        synapse_centroids = pymeda_driver.calculate_synapse_centroids(connected_components)
        class_list = gaba_classifier_pipeline(data_dict, synapse_centroids)
        no_pred_vol, non_gaba_vol, gaba_vol = split_vol_by_id(label_vol, class_list, 3)
    except Exception as e:
        logging.info("Failed to run Nomads-Classfier algorithm on data.")
        logging.info(e)
        logging.info("Exiting...")
        #upload_results(bucket, path, results_key)
        print_exc()
        return

    gaba_vol = gaba_vol.astype(np.uint8)
    np.putmask(gaba_vol, gaba_vol, 255)
    non_gaba_vol = non_gaba_vol.astype(np.uint8)
    np.putmask(non_gaba_vol, non_gaba_vol, 255)

    pickle.dump(gaba_vol, open(path + "gaba" + ".pkl", "wb"))
    print("Saved pickled gaba (np array) {} in {}".format("gaba.pkl", path))
    pickle.dump(non_gaba_vol, open(path + "non_gaba" + ".pkl", "wb"))
    print("Saved pickled gaba (np array) {} in {}".format("non_gaba.pkl", path))

    print("Generating plots...")
    try:
        pymeda_driver.pymeda_pipeline(results, norm_data, title = "PyMeda Plots on All Predicted Synapses", path = path)
    except:
        logging.info("Failed to generate plots for all predictions. No synapses detected.")
    try:
        pymeda_driver.pymeda_pipeline(non_gaba_vol, norm_data, title = "PyMeda Plots on Predicted NonGaba Synapses", path = path)
    except:
        logging.info("PyMeda failed to generate plots for NonGaba. No Non-Gaba synapses found.")
    try:
        pymeda_driver.pymeda_pipeline(gaba_vol, norm_data, title = "PyMeda Plots on Predicted Gaba Synapses", path = path)
    except:
        logging.info("PyMeda failed to generate plots for Gaba. No Gaba synapses found.")




    print("Uploading results to BOSS...")
    results_dict = {"All": results, "Gaba": gaba_vol, "NonGaba": non_gaba_vol}
    try:
        boss_links = boss_push(token, "collman_nomads", "nomads_predictions", z_range, y_range, x_range, results_dict, results_key)
        with open('results/NDVIS_links.csv', 'w') as csv_file:
            writer = csv.writer(csv_file)
            for key, value in boss_links.items():
                writer.writerow([key, value])
    except Exception as e:
        logging.info("Failed to push results to BOSS. Check permissions and Boss online status.")
        logging.info(e)

    logging.info("Finished, uploading results. END")
    return info, results

'''
    upload_results(bucket, path, results_key)
'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NOMADS Classifier driver.')
    parser.add_argument('--host', required = True, type=str, help='BOSS Api host, do not include "https"')
    parser.add_argument('--token', required = True, type=str, help='BOSS API Token Key')
    parser.add_argument('--col', required = True, type=str, help='collection name')
    parser.add_argument('--exp', required = True, type=str, help='experiment name')
    parser.add_argument('--z-range', required = True, type=str, help='zstart,zstop   NO SPACES. zstart, zstop will be casted to ints')
    parser.add_argument('--y-range', required = True, type=str, help='ystart,ystop   NO SPACES. ystart, ystop will be casted to ints')
    parser.add_argument('--x-range', required = True, type=str, help='xstart,xstop   NO SPACES. xstart, xstop will be casted to ints')
    args = parser.parse_args()

    z_range = list(map(int, args.z_range.split(",")))
    y_range = list(map(int, args.y_range.split(",")))
    x_range = list(map(int, args.x_range.split(",")))

    logging.basicConfig(filename='./results/job.log',level=logging.INFO)
    driver(args.host, args.token, args.col, args.exp, z_range, y_range, x_range)
