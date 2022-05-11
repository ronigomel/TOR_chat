from Crypto.PublicKey import RSA
import socket
from tcp_by_size import recv_by_size, send_with_size
import threading
import pickle
from test2 import RsaWrapping

K_PUBLIC = RSA.RsaKey
K_PRIVATE = RSA.RsaKey
STOP = False
MAIL = []
MAILBOX_LOCK = threading.Lock

NEXT_STOP = ''
NEXT_STOP_LOCK = threading.Lock


def generate_keys():
    global K_PRIVATE
    global K_PUBLIC

    K_PRIVATE = RSA.generate(1024)
    K_PUBLIC = K_PRIVATE.publickey()


def main(ip: str, port: int):
    cipher = RsaWrapping(117, 128)
    generate_keys()

    srv_socket = socket.socket()
    srv_socket.bind((ip, port))
    srv_socket.listen(1)
    cli_sock, addr = srv_socket.accept()  # first connection is always 127.0.0.1

    send_with_size(cli_sock, K_PUBLIC)  # sending the public key to the

    t = threading.Thread(target=mailbox, args=(srv_socket,))
    t.start()

    while not STOP:
        if len(MAIL) > 0 and NEXT_STOP != '':
            with MAILBOX_LOCK:
                to_send = pickle.dumps(MAIL)
            with NEXT_STOP_LOCK:
                next_ip = NEXT_STOP
            to_send = pickle.dumps([to_send, next_ip])
            send_with_size(cli_sock, to_send)
        else:
            with MAILBOX_LOCK:
                send_with_size((pickle.dumps(MAIL)))


def mailbox(srv_sock: socket.socket):
    global K_PRIVATE
    global MAIL
    global NEXT_STOP

    cipher = RsaWrapping()
    while not STOP:
        srv_sock.listen(1)
        mail_sock, mail_addr = srv_sock.accept()
        data = recv_by_size(mail_sock)
        data = pickle.loads(data)

        if data[0] == 'PING':
            send_with_size(mail_sock, pickle.dumps('ALIVE'))

        decrypted_data = cipher.unwrap(data[0], data[1], K_PRIVATE)
        if type(decrypted_data) == tuple:
            next_stop = decrypted_data[0]
            decrypted_data = decrypted_data[1:]
            with MAILBOX_LOCK:
                MAIL = decrypted_data
            with NEXT_STOP_LOCK:
                NEXT_STOP = next_stop
        else:
            decrypted_data = cipher.unwrap_single(decrypted_data, K_PRIVATE)
            with MAILBOX_LOCK:
                MAIL = decrypted_data
            with NEXT_STOP_LOCK:
                NEXT_STOP = ''



if __name__ == '__main__':
    k = [1,2,3,4]
    print(k[1:])