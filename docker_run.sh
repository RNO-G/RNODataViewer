MY_DATA_DIR="/home/sb/Python/scratch/data/inbox/"
sudo docker run -e RNO_DATA_DIR="/data" --mount type=bind,source="${MY_DATA_DIR}",target="/data" -p 8049:8049 test:0.1
