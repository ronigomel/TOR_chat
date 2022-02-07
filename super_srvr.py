import socket
from tcp_by_size import recv_by_size, send_with_size
from protocol import Protocol

STATIONS = {}
p = Protocol()


def main():
    sock = socket.socket()
    sock.bind(('0.0.0.0', 8820))
    sock.listen()
    cli_sock, cli_addr = sock.accept()

    if cli_addr[0] in STATIONS.keys():
        online_station(cli_sock, cli_addr)
    else:
        new_station(cli_sock)


def new_station(cli_sock: socket.socket):
    global STATIONS
    data = recv_by_size(cli_sock).decode('utf-8')
    data = p.deconstruct_msg(data)
    if data[0] == 'hi':
        STATIONS[data[1]] = data[2].encode()


def online_station(cli_sock, cli_addr):
    ping()
    pass


def ping():
    pass


if __name__ == '__main__':
    main()
