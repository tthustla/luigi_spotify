#!/bin/bash
sudo yum -y install python36
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
pip3 install luigi --user
pip3 install spotipy --user
pip3 install boto3 --user