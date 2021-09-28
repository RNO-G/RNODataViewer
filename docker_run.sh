MY_DATA_DIR="/Users/shallmann/Desktop/rnog_field_data"
docker run -e RNO_DATA_DIR="/data" --mount type=bind,source="${MY_DATA_DIR}",target="/data" -d -p 8049:8049 test:0.1
