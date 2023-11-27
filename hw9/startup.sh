#!/bin/bash

# check if the directory exists; if not, copy the files from the bucket to the directory
if [ -d "/root/ds561hw8bucket" ]; then
    echo "Directory /root/ds561hw8bucket exists."
else
    # copy the files from the bucket to the directory
    gsutil -m cp -r gs://ds561hw8bucket/ /root/
fi

# go to the directory where the flask app is located
cd /root/ds561hw8bucket

# install dependencies from requirements.txt
apt install python3-pip -y
pip3 install -r requirements.txt

# run the flask app
python3 main.py