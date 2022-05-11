import socket
from tcp_by_size import recv_by_size, send_with_size
import pickle
import threading
import random
import datetime
from Crypto.PublicKey import RSA

STATIONS = {}
STATIONS_LOCK = threading.Lock()
STOP = False


def log(action: str, ip: str, port: int):
    s = '----------------------------------- ' + action + ' -----------------------------------'
    print(s)
    print('IP: ' + ip + ' | PORT: ' + str(port))
    print('TIME: ' + str(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")))
    print('-' * len(s))


def main():
    sock = socket.socket()
    sock.bind(('0.0.0.0', 8820))
    sock.listen()

    while not STOP:
        cli_sock, cli_addr = sock.accept()
        if cli_addr[0] in STATIONS.keys():
            online_station(cli_sock, cli_addr, sock)
        else:
            new_station(cli_sock)


def new_station(cli_sock: socket.socket):
    global STATIONS
    global STATIONS_LOCK
    data = pickle.loads(recv_by_size(cli_sock))
    if data[0].lower() == 'hi':
        with STATIONS_LOCK:
            STATIONS[data[1]] = [data[2], data[3]]    # data[1] = ip, data[2] = port, data[3] = public key
            print(STATIONS)


def online_station(cli_sock, cli_addr: tuple, sock: socket.socket):
    global STATIONS
    global STATIONS_LOCK
    data = pickle.loads(recv_by_size(cli_sock))
    if data[0].lower() == 'msg':
        print('here')
        # ping()
        route = get_route(3, cli_addr[0])
        print(route)
        send_with_size(cli_sock, pickle.dumps(['ROUTE', route]))


def get_route(n: int, ip):
    print('Generating route...')
    prev_num = random.randint(0, len(STATIONS) - 2)
    while ip == list(STATIONS.keys())[prev_num]:
        prev_num = random.randint(0, len(STATIONS) - 2)
    route = []
    for i in range(n):
        with STATIONS_LOCK:
            route.append(list(STATIONS.keys())[prev_num])

        current_num = random.randint(0, len(STATIONS) - 2)
        with STATIONS_LOCK:
            if list(STATIONS.keys())[current_num] not in route:
                prev_num = current_num

    full_route = {}
    for i in route:
        full_route[i] = STATIONS[i]

    return full_route


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
    #
    """
    sock = socket.socket()
    sock.bind(('0.0.0.0', 8820))
    sock.listen()"""
    STATIONS = {'1.2.3.4': [1263, RSA.generate(1024).publickey()], '127.0.0.1': [1273, RSA.generate(1024).publickey()], '111.222.32.43': [1283, RSA.generate(1024).publickey()], '111.21.34.45': [1293, RSA.generate(1024).publickey()], '11.21.34.45': [1201, 1123123]}
    main()

    """
    while True:
        s, address = sock.accept()
        if address[0] in STATIONS:
            route = online_station(s, address, sock)
            print(route)
            if route != None:
                break
    """
    # main()
