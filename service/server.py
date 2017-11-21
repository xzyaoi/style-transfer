from __future__ import print_function
import sys
import os
import argparse
import json

from http_server import http_server_run

def prepare_dir(key):
    temp_key = key.split('/')
    if len(temp_key)  > 1:
        dir = '/'.join(temp_key[:-1])
        if not os.path.exists(dir):
            os.mkdir(dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Inference parser')
    parser.add_argument("--json_conf", action="store", default="style-transfer.conf",
                        dest="json_conf", help="json configure file")
    parser.add_argument("--port", action="store", default="8080",
                        dest="port", help="http server port")
 
    args = parser.parse_args()
    print (args)

    print (args.json_conf)
    if os.path.isfile(args.json_conf):
        with open(args.json_conf) as data_file:
            data = json.load(data_file)

    http_server_run(data, args.port)

