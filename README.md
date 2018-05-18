# nomads-classifier-pipeline
Nomads classifier with PyMeda and Boss functionality.  
This pipeline will:
1. Pull data from BOSS (assuming correct permissions)
2. Run [Nomads-unsupervised](https://github.com/neurodata-nomads/nomads_deploy)
3. Run [Nomads-classifier](https://github.com/neurodata-nomads/nomads_classifier)
4. Run [PyMeda](https://github.com/neurodata-nomads/pymeda)
5. Upload results to BOSS (assuming correct permissions to push to channel "collman_nomads" and experiment "nomads_predictions").

## How to Run using Docker
Prequisites:  
Have Docker installed on machine. Instructions [here]()

### Method 1. Run using Jupyter Notebook
0. Open Terminal

1. Pull built image from [DockerHub](https://hub.docker.com/r/rguo123/nomads-classifier/) by running:  
  ```
  docker pull rguo123/nomads-classifier
  ```
2. Start image with the following command
  ```
  docker run -it -p 8888:8888 rguo123/nomads-classifier:latest bash
  ```
   You will ssh into running docker container.
  
3. Start notebook with the command:  
  ```
  jupyter notebook --ip 0.0.0.0 --allow-root --no-browser
  ```
4. A url that looks like the following should appear:
  ```
  Copy/paste this URL into your browser when you connect for the first time,
   to login with a token:
   http://<host>:8888/?token=<long token>

  ```
5. Copy URL into your browser and replace whatever is in <host> with "localhost"
  ```
  http://localhost:8888/?token=....
  ```
   You should now be able to access the Nomads-Classifier jupyter notebook. Leave the container running and follow the       
   instructions in there to run the pipeline!
  
6. To get results after your pipeline is done running, press ```Ctr-C``` in the docker container. Type:
  ```
  cd results
  ```
7. You are now inside the results directory and can checkout the results. If you want to move results to your computer follow instructions in this [link](https://stackoverflow.com/questions/22049212/copying-files-from-docker-container-to-host?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa).  

  Inside the results directory, you should have NDVis_links.csv which contains links to NDVis, pickled numpy arrays of the      predictions, and PyMeda HTML files.

8. You can exit container by typing ```exit```
  
  
### Method 2. Run using Python
0. Go into Terminal (can skip step 1 if you already have image)

1. Pull built image from [DockerHub](https://hub.docker.com/r/rguo123/nomads-classifier/) by running:  
  ```
  docker pull rguo123/nomads-classifier
  ```
2. Start image with the following command
  ```
  docker run -it rguo123/nomads-classifier:latest bash
  ```
  You will ssh into running docker container.  
3. Run the command
```
python3 driver.py --host api.boss.neurodata.io --token <insert BOSS API token> --col <insert BOSS collection> --exp <insert  BOSS experiment> --z-range <z_start>,<z_end> --y-range <y_start>,<y_end> --x-range <x_start>,<x_end>
```
4. See steps 6 and 7 in Method 1 to retrieve results.

## How to run without Docker:
Prequisites: Have python3 and pip3 working on computer.
1. ``` git clone https://github.com/rguo123/nomads-classifier-pipeline.git```
2. ```pip3 install -r requirements.txt```
3. Run the command step 3 in Running with Docker Method 2.
