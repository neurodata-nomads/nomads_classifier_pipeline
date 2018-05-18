FROM ubuntu:16.04
#installing ubuntu essentials
RUN apt-get update && apt-get -y install python3 python-dev python3-dev build-essential python3-pip libnuma-dev
RUN apt-get install -y python3-tk

# create directory
RUN mkdir /workdirectory

WORKDIR /workdirectory

ADD *.py ./
ADD *.npy ./
ADD *.ipynb ./
ADD model.pkl ./
ADD requirements.txt ./
Run mkdir ./results

RUN pip3 install -r requirements.txt 
RUN pip3 install matplotlib==2.1.0 --ignore-installed

CMD jupyter-notebook —-ip 0.0.0.0 —-no-browser —-allow-root