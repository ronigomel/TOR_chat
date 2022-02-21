import socket
from tcp_by_size import recv_by_size, send_with_size
import pickle
import threading
import random

STATIONS = {}
STATIONS_LOCK = threading.Lock


def main():
    sock = socket.socket()
    sock.bind(('0.0.0.0', 8820))
    sock.listen()
    cli_sock, cli_addr = sock.accept()

    if cli_addr[0] in STATIONS.keys():
        online_station(cli_sock, cli_addr, sock)
    else:
        new_station(cli_sock)


def new_station(cli_sock: socket.socket):
    global STATIONS
    data = pickle.loads(recv_by_size(cli_sock))
    if data[0].lower() == 'hi':
        STATIONS[data[1]] = [data[2], data[3]]


def online_station(cli_sock, cli_addr, sock: socket.socket):
    global STATIONS
    global STATIONS_LOCK
    data = pickle.loads(recv_by_size(sock))
    if data[0].lower() == 'route':
        ping()
        route = get_route(3)


def get_route(n: int):
    prev_num = random.randint(len(STATIONS))
    route = []
    for i in range(n):
        with STATIONS_LOCK:
            route.append(list(STATIONS.keys())[prev_num])

        current_num = random.randint(len(STATIONS))
        with STATIONS_LOCK:
            if list(STATIONS.keys())[current_num] not in route:
                prev_num = current_num
    return route


def ping():
    global STATIONS
    ping_sock = socket.socket()
    delete_stations = []
    with STATIONS_LOCK:
        for addr in STATIONS.keys():
            try:
                ping_sock.connect((addr[0], STATIONS[addr][1]))
                send_with_size(ping_sock, pickle.dumps('PING'))
            except socket.error or socket.timeout:
                delete_stations.append(addr)

        remove_station(delete_stations)


def remove_station(stations_list: list):
    global STATIONS
    with STATIONS_LOCK:
        for address in stations_list:
            del STATIONS[address]


if __name__ == '__main__':
    main()
