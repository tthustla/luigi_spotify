#!/bin/bash
# Install Python3
sudo yum -y install python36
# Install PIP3
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
# Install required Python packages in user-specific directories
pip3 install luigi --user
pip3 install spotipy --user
pip3 install boto3 --user
