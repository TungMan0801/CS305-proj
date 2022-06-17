from threading import Thread, Lock
import socket
import argparse

hello = [
    b"HTTP/1.0 200 OK\r\n",
    b"Connection: close" b"Content-Type:text/html; charset=utf-8\r\n",
    b"\r\n",
]


index = 0
lock = Lock()
thread_list = []
MAX_THREAD_NUM=4


class DNSServer:
    def __init__(self, source_ip, source_port, servers, ip="127.0.0.1", port=5533):
        self.source_ip = source_ip
        self.source_port = source_port
        self.ip = ip
        self.port = port
        self.servers = servers
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))

    def start(self):
        # reply_thread = Thread(target=self.thread_reply, args=())
        # reply_thread.start()

        while True:
            message, address = self.receive()
            thread=Thread(target=self.handle, args=(message, address))
            thread.start()

    # def thread_reply(self):
    #     while True:
    #         for future in as_completed(thread_list):
    #             response, address = future.result()
    #             self.reply(address, response)

    def receive(self):
        return self.socket.recvfrom(8192)

    def reply(self, address, response):
        self.socket.sendto(response, address)

    def handle(self, message, address):
        result = b""
        for line in hello:
            result += line
        serverport = self.RR()
        body = "<html><body>" + str(serverport) + "<body></html>\r\n\r\n"
        result += bytes(body, "utf-8")
        print(result)
        self.reply(address, result)
        # return result, address

    def RR(self):
        global index, lock
        lock.acquire()
        picked = self.servers[index]
        index = (index + 1) % len(servers)
        lock.release()
        return picked


def read_servers_pack():
    servers = []
    file = "docker_setup/netsim/" + args.serverpath
    with open(file, "r") as f:
        for line in f:
            servers.append(line.replace("\n", ""))
    return servers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DNS will ne with -i -p")
    parser.add_argument(
        "-i", "--sourceip", default="127.0.0.1", help="The source ip of client"
    )
    parser.add_argument(
        "-p", "--sourceport", default=7776, help="The listen port of client"
    )
    parser.add_argument(
        "-s", "--serverpath", default="servers/5servers", help="The running apache servers"
    )
    args = parser.parse_args()
    source_ip = args.sourceip
    source_port = args.sourceport
    servers = read_servers_pack()
    local_dns_server = DNSServer(source_ip, source_port, servers)
    local_dns_server.start()
