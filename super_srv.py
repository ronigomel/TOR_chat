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
    sock.bind(('192.168.1.172', 8820))
    sock.listen()
    print('listening...')

    while not STOP:
        cli_sock, cli_addr = sock.accept()
        log('NEW CONNECTION', cli_addr[0], cli_addr[1])
        if cli_addr[0] in STATIONS.keys():
            online_station(cli_sock, cli_addr)
        else:
            new_station(cli_sock)


def new_station(cli_sock: socket.socket):
    global STATIONS
    global STATIONS_LOCK
    data = pickle.loads(recv_by_size(cli_sock))
    if data[0].lower() == 'hi':
        with STATIONS_LOCK:
            pubkey = RSA.importKey(data[3])
            STATIONS[data[1]] = [data[2], pubkey]  # data[1] = ip, data[2] = port, data[3] = public key


def online_station(cli_sock, cli_addr: tuple):
    global STATIONS
    global STATIONS_LOCK
    data = pickle.loads(recv_by_size(cli_sock))
    if data[0].lower() == 'msg':
        ping()
        route = get_route(1, cli_addr[0], data[1])
        send_with_size(cli_sock, pickle.dumps(['ROUTE', route]))
        log('SENT', cli_addr[0], cli_addr[1])


def get_route(n: int, ip, dst):
    global STATIONS
    global STATIONS_LOCK
    with STATIONS_LOCK:
        if n > len(STATIONS):
            return 'ERROR'
    print('generating route...')
    route = {}
    with STATIONS_LOCK:
        for i in range(n):
            previous = random.randint(0, len(STATIONS) - 1)
            while ip == list(STATIONS.keys())[previous] and list(STATIONS.keys())[previous] not in list(route.keys()) or dst == list(STATIONS.keys())[previous]:
                previous = random.randint(0, len(STATIONS) - 1)
            else:
                route[(list(STATIONS.keys())[previous], STATIONS[list(STATIONS.keys())[previous]][0])] = STATIONS[list(STATIONS.keys())[previous]][1].exportKey()
    return route


def ping():
    global STATIONS
    delete_stations = []
    with STATIONS_LOCK:
        for addr in list(STATIONS.keys()):
            try:
                ping_sock = socket.socket()
                ping_sock.connect((addr, STATIONS[addr][0]))
                send_with_size(ping_sock, pickle.dumps(['PING']))
                log('PING', addr, STATIONS[addr][0])
                ans = recv_by_size(ping_sock)
                if len(ans) > 0:
                    ans = pickle.loads(ans)
                    if ans.upper() == 'ALIVE':
                        print(addr, ' online')
                ping_sock.close()
            except socket.error or socket.timeout:
                delete_stations.append(addr)
        if len(delete_stations) > 0:
            remove_station(delete_stations)


def remove_station(stations_list: list):
    global STATIONS
    with STATIONS_LOCK:
        for address in stations_list:
            del STATIONS[address]


if __name__ == '__main__':
    main()

