#! /usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation

"""
Script to be used with V2 Telemetry.
Allows the user input commands and read the Telemetry response.
"""

import socket
import os
import glob
import json
import time
from flask import Flask
import flask


def read_socket(sock, buf_len, echo=True):
    """ Read data from socket and return it in JSON format """
    reply = sock.recv(buf_len).decode()
    try:
        ret = json.loads(reply)
    except json.JSONDecodeError:
        print("Error in reply: ", reply)
        sock.close()
        raise
    if echo:
        print(json.dumps(ret))
    return ret


def _read_socket(sock, buf_len, echo=True):
    """ Read data from socket and return it in JSON format """
    reply = sock.recv(buf_len).decode()
    try:
        ret = json.loads(reply)
    except json.JSONDecodeError:  
        # print("Error in reply: ", reply)
        sock.close()
        raise
    if echo:
        return ret["/ethdev/stats"]["q_opackets"][0]
        # return ret["/ethdev/stats"]["obytes"]
    return 0




def getPortStats(path):
    """ Connect to socket and handle user input """
    res={"path":path}
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    # print("Connecting to " + path)
    try:
        sock.connect(path)
    except OSError:
        print("Error connecting to " + path)
        sock.close()
        return
    json_reply = read_socket(sock, 1024)
    output_buf_len = json_reply["max_output_len"]

    text = "/ethdev/list"
    sock.send(text.encode())
    portList = read_socket(sock, output_buf_len)["/ethdev/list"]
    # print("Detect ", len(portList), " DPDK Ports......")

    portStats = []
    timer = time.perf_counter()
    res["timestamp"]=timer
    for i in portList:
        text = "/ethdev/stats,{}".format(i)
        sock.send(text.encode())
        stats = read_socket(sock, output_buf_len, echo=False)["/ethdev/stats"]
        portStats.append(stats)
    sock.close()
    res["stats"]=portStats
    return res


# Path to sockets for processes run as a root user
def getDPDKStats():
    # res=[{"path": "/var/run/dpdk/rte/dpdk_telemetry.v2", "timestamp": 166509.930383073, "stats": [{"ipackets": 3263, "opackets": 0, "ibytes": 211612, "obytes": 0, "imissed": 0, "ierrors": 0, "oerrors": 0, "rx_nombuf": 0, "q_ipackets": [3138, 18, 6, 7, 0, 0, 7, 12, 7, 12, 16, 17, 13, 10, 0, 0], "q_opackets": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "q_ibytes": [189640, 3528, 933, 1003, 0, 0, 1372, 1866, 1372, 1866, 2804, 3332, 1936, 1960, 0, 0], "q_obytes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "q_errors": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}, {"ipackets": 3171, "opackets": 0, "ibytes": 202209, "obytes": 0, "imissed": 0, "ierrors": 0, "oerrors": 0, "rx_nombuf": 0, "q_ipackets": [3076, 17, 7, 22, 9, 2, 10, 0, 3, 2, 10, 0, 3, 10, 0, 0], "q_opackets": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "q_ibytes": [184560, 3332, 1372, 4060, 1638, 266, 1960, 0, 373, 266, 1960, 0, 462, 1960, 0, 0], "q_obytes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "q_errors": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}]}]
    res=[]
    for f in glob.glob('/var/run/dpdk/*/dpdk_telemetry.%s' % 'v2'):
        # handle_socket(f)
        res.append(getPortStats(f))
    return res;
    
    
 
app = Flask(__name__)
@app.route('/')
def index():
    return flask.render_template('index.html',name='index') #使用模板插件，引入index.html。此处会自动Flask模板文件目录寻找index.html文件。

@app.route('/stats')
def hello_world():
    # getDPDKStats()
    return json.dumps(getDPDKStats())
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7788)