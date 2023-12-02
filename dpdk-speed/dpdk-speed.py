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
import readline
import time

# global vars
TELEMETRY_VERSION = "v2"
CMDS = []


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


def handle_socket(path):
    """ Connect to socket and handle user input """
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    global CMDS
    print("Connecting to " + path)
    try:
        sock.connect(path)
    except OSError:
        print("Error connecting to " + path)
        sock.close()
        return
    json_reply = read_socket(sock, 1024)
    output_buf_len = json_reply["max_output_len"]

    # get list of commands for readline completion
    sock.send("/".encode())
    CMDS = read_socket(sock, output_buf_len, False)["/"]

    # interactive prompt
    text = input('--> ').strip()
    while text != "quit":
        if text.startswith('/'):
            sock.send(text.encode())
            read_socket(sock, output_buf_len)
        text = input('--> ').strip()
    sock.close()


def deal(company_name_list):
    with open('data.txt', 'w') as f:
        for i in company_name_list:
            data = "{} {}\n".format(i[0], i[1])
            f.write(data)
    f.close()

# /ethdev/stats,0


def getPortStats(path):
    """ Connect to socket and handle user input """
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    global CMDS
    print("Connecting to " + path)
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
    print("Detect ", len(portList), " DPDK Ports......")

    portStats = []
    timer = time.perf_counter()
    for i in portList:
        text = "/ethdev/stats,{}".format(i)
        sock.send(text.encode())
        stats = read_socket(sock, output_buf_len, echo=False)["/ethdev/stats"]
        portStats.append(stats)

    while True:
        time.sleep(1)
        print("===========================================================================================")
        cur = time.perf_counter()
        interval = cur-timer
        timer = cur
        for p in portList:
            #print("Interval:",interval)
            text = "/ethdev/stats,{}".format(p)
            sock.send(text.encode())
            stats = read_socket(sock, output_buf_len, echo=False)[
                "/ethdev/stats"]
            q_ipackets = []
            for i in range(0, len(stats["q_ipackets"])):
                q_ipackets.append(stats["q_ipackets"]
                                  [i]-portStats[p]["q_ipackets"][i])
                q_ipackets[i] /= interval
                q_ipackets[i] = int(q_ipackets[i])
            q_opackets = []
            for i in range(0, len(stats["q_opackets"])):
                q_opackets.append(stats["q_opackets"]
                                  [i]-portStats[p]["q_opackets"][i])
                q_opackets[i] /= interval
                q_opackets[i] = int(q_opackets[i])
            q_ibytes = []
            for i in range(0, len(stats["q_ibytes"])):
                q_ibytes.append(stats["q_ibytes"][i] -
                                portStats[p]["q_ibytes"][i])
                q_ibytes[i] /= interval
                q_ibytes[i] = int(q_ibytes[i]*8)
            q_obytes = []
            for i in range(0, len(stats["q_obytes"])):
                q_obytes.append(stats["q_obytes"][i] -
                                portStats[p]["q_obytes"][i])
                q_obytes[i] /= interval
                q_obytes[i] = int(q_obytes[i]*8)
            print("Port ", p)
            print("RX-PPS:", q_ipackets, ":", sum(q_ipackets))
            print("RX-BPS:", q_ibytes, ":", sum(q_ibytes))
            print("TX-PPS:", q_opackets, ":", sum(q_opackets))
            print("TX-BPS:", q_obytes, ":", sum(q_obytes))
            portStats[p] = stats

    # deal(res)
    sock.close()


def readline_complete(text, state):
    """ Find any matching commands from the list based on user input """
    all_cmds = ['quit'] + CMDS
    if text:
        matches = [c for c in all_cmds if c.startswith(text)]
    else:
        matches = all_cmds
    return matches[state]


readline.parse_and_bind('tab: complete')
readline.set_completer(readline_complete)
readline.set_completer_delims(readline.get_completer_delims().replace('/', ''))

# Path to sockets for processes run as a root user
for f in glob.glob('/var/run/dpdk/*/dpdk_telemetry.%s' % TELEMETRY_VERSION):
    # handle_socket(f)
    getPortStats(f)
# Path to sockets for processes run as a regular user
for f in glob.glob('%s/dpdk/*/dpdk_telemetry.%s' %
                   (os.environ.get('XDG_RUNTIME_DIR', '/tmp'), TELEMETRY_VERSION)):
    handle_socket(f)
