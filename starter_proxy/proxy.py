import threading
import argparse
from xml.dom.minidom import parseString
import os
from datetime import datetime
import logging
import requests
import time
import socket
from flask import Flask, Response

app = Flask(__name__)
time_limit = 30
LAST_REQUEST_MS = time.time()
GMT_FORMAT = "%a, %d  %b %Y %H:%M:%S GMT"
T_current = B = Ele = 0
TIME = None
time1=0
remove_log_file_atthebegining = 0
big_buck_bunny_bit_rate = []
first_query_seg = None


@app.before_request
def update_last_request_ms():
    global LAST_REQUEST_MS
    LAST_REQUEST_MS = time.time()
    request_dns()


@app.route("/index.html")
def index():
    url = "http://localhost:" + args.serverport + "/"
    return Response(requests.get(url))


@app.route("/StrobeMediaPlayback.swf")
def StrobeMediaPlayback():
    url = "http://localhost:" + args.serverport + "/StrobeMediaPlayback.swf"
    return Response(requests.get(url))


@app.route("/swfobject.js")
def swfobject():
    url = "http://localhost:" + args.serverport + "/swfobject.js"
    return Response(requests.get(url))


@app.route("/vod/<name>")
def vod(name):
    global first_query_seg, B, Ele, TIME,time1
    if name == "big_buck_bunny.f4m":
        if len(big_buck_bunny_bit_rate) == 0:
            url = "http://localhost:" + args.serverport + "/vod/" + name
            response = requests.get(url)
            response_xml_text = response.text
            parse_big_buck_bunny_f4m(response_xml_text)
        name = "big_buck_bunny_nolist.f4m"
        url = "http://localhost:" + args.serverport + "/vod/" + name
        first_query_seg = True
    else:
        name = modify_request(name)
        url = "http://localhost:" + args.serverport + "/vod/" + name
        first_query_seg = False
    time1 = time.time()
    response_ = requests.get(url)
    time2 = time.time()
    B, Ele = int(response_.headers["Content-Length"]), (
        time2 - time1
    )  # response_.elapsed.total_seconds()

    TIME = datetime.strptime(
        response_.headers["Date"],
        GMT_FORMAT,
    )
    return Response(response_)


def modify_request(name):
    """
    Here you should change the requested bit rate according to your computation of throughput.
    And if the request is for big_buck_bunny.f4m, you should instead request big_buck_bunny_nolist.f4m
    for client and leave big_buck_bunny.f4m for the use in proxy.
    """
    T, T_current = calculate_throughput()
    # 1000Seg3-Frag13
    Seg, Frag = name.split("-")
    bitrate, segmentation = Seg.split("Seg")
    frag = Frag.split("Frag")[-1]
    if first_query_seg:
        bitrate = big_buck_bunny_bit_rate[0]
    else:
        for rate in big_buck_bunny_bit_rate:
            if T_current < int(rate) * 1.5:
                break
            else:
                bitrate = rate
    name = bitrate + "Seg" + segmentation + "-Frag" + frag
    write_log(T, T_current, bitrate, name)
    return name


def parse_big_buck_bunny_f4m(data):
    global big_buck_bunny_bit_rate
    if data != None:
        data = parseString(data).documentElement
        medias = data.getElementsByTagName("media")
        big_buck_bunny_bit_rate = [media.getAttribute("bitrate") for media in medias]


def request_dns():
    """
    Request dns server here.
    """
    request = "GET HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n"  # 需要修改规范发送的包
    sock.send(request.encode("ascii"))
    chunk = sock.recv(4096)  # 确认收到的包完整和解析
    port = str(chunk).split("<body>")[1]
    args.serverport = port


def calculate_throughput():
    """
    Calculate throughput here.
    """
    global T_current, B, Ele
    T = B / Ele  # 单位： Bytes / seconds  bytes大概一千多，elew 0.00几, 此时T是1开头的七位数
    T = (T) / (1024 / 8)  # Kbps T/125000*1024
    T_current = (
        ((1 - float(args.alpha)) * T_current) + T * float(args.alpha)
        if T_current != 0
        else T
    )
    return T, T_current


def write_log(T, T_current, bitrate, chunkname):
    global remove_log_file_atthebegining, TIME, logfile
    # <time> <duration> <tput> <avg-tput> <bitrate> <server-port> <chunkname>
    # Remove existing log file at the beginnig
    # tput is T, avg-tput is T-current

    try:
        if args.log:
            # with open(args.log, 'a') as logfile:
            # 这里是不完整的，还缺一些参数要打印
            logfile.write(
                f"%s %f %f %f %s %s %s\n"
                % (time1, Ele, T, T_current, bitrate, args.serverport, chunkname)
            )

    except Exception as e:
        logging.getLogger(__name__).error(e)


def exit_this():
    global timer
    # 重复构造定时器
    if time.time() - LAST_REQUEST_MS >= time_limit:  # 时长
        logfile.closed
        os._exit(0)
    timer = threading.Timer(int(time_limit * 0.9), exit_this)
    timer.start()


if __name__ == "__main__":
    global timer, logfile, sock
    timer = threading.Timer(2, exit_this)  # 第一个参数是seconds
    timer.start()
    parser = argparse.ArgumentParser(description="Proxy will ne with -l -a -p -s")
    parser.add_argument(
        "-l",
        "--log",
        default=None,
        help="log file for logging events (overwrites file if it already exists)",
    )
    parser.add_argument("-a", "--alpha", default=0.5, help="The alpha for throughtout")
    parser.add_argument("-p", "--listenport", default=7776, help="The listen port")
    parser.add_argument("-P", "--dnsport", default=None, help="dns port")
    parser.add_argument("-s", "--serverport", default="8080", help="server port")
    args = parser.parse_args()

    if remove_log_file_atthebegining == 0:
        if args.log and os.path.isfile(args.log):
            os.remove(args.log)
            remove_log_file_atthebegining = 1
    file = os.path.join(args.log)
    logfile = open(file, "a", buffering=1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("127.0.0.1", 5533))

    app.run(port=args.listenport, threaded=True)
    # 在run的过程中是不会执行到这一行的,关了才有
    logfile.closed