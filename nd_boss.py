import re
from intern.remote.boss import BossRemote
from intern.resource.boss.resource import ChannelResource
import numpy as np

def create_boss_remote(config_dict):
    remote = BossRemote(config_dict)
    return remote

def boss_push(token,
              col,
              exp,
              z_range,
              y_range,
              x_range,
              data_dict,
              results_key):
    dtype = "uint8"
    config_dict = {"token": token, "host": "api.boss.neurodata.io" , "protocol": "https"}
    remote = create_boss_remote(config_dict)
    links_dict = {}

    for key, data in data_dict.items():
        data = data.astype(np.uint8)
        np.putmask(data, data>0, 255)
        channel = results_key + "_" + key
        print(data.shape)
        z, y, x = data.shape

        channel_resource = ChannelResource(channel, col, exp, 'image', '', 0, dtype, 0)
        print("Pushing to BOSS...")

        for z in range(z_range[0],z_range[1]):
            print(z)
            try:
                old_channel = remote.get_project(channel_resource)
                remote.create_cutout(old_channel, 0, (x_range[0],x_range[1]), (y_range[0],y_range[1]), (z,z+1), data[z-z_range[0]].reshape(-1,data[z-z_range[0]].shape[0],data[z-z_range[0]].shape[1]))
            except:
                channel_resource = ChannelResource(channel, col, exp, 'image', '', 0, dtype, 0)#, sources = ["em_clahe"])
                new_channel = remote.create_project(channel_resource)
                remote.create_cutout(new_channel, 0, (x_range[0],x_range[1]), (y_range[0],y_range[1]), (z,z+1), data[z-z_range[0]].reshape(-1,data[z-z_range[0]].shape[0],data[z-z_range[0]].shape[1]))


        links_dict[key] = ("http://ndwt.neurodata.io/channel_detail/{}/{}/{}/").format(col, exp, channel)
        print("Pushed {} to Boss".format(channel))
    return links_dict
