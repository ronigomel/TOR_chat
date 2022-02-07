from Crypto.PublicKey import RSA
import socket
from tcp_by_size import recv_by_size, send_with_size
import threading
import pickle
from onionwrapping import OnionWrapping

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
    generate_keys()

    srvr_socket = socket.socket()
    srvr_socket.bind((ip, port))
    srvr_socket.listen(1)
    cli_sock, addr = srvr_socket.accept()  # first connection is always 127.0.0.1

    send_with_size(cli_sock, K_PUBLIC)  # sending the public key to the

    t = threading.Thread(target=mailbox, args=(srvr_socket,))
    t.start()

    while not STOP:
        if len(MAIL) > 0 and NEXT_STOP != '':
            with MAILBOX_LOCK:
                to_send = pickle.dumps(MAIL)
            with NEXT_STOP_LOCK:
                next_ip = NEXT_STOP

            send_with_size(cli_sock, to_send)
            send_with_size(cli_sock, next_ip)


def mailbox(srvr_sock: socket.socket):
    global K_PRIVATE
    global MAIL
    global NEXT_STOP

    wrap = OnionWrapping()
    while not STOP:
        srvr_sock.listen(1)
        mail_sock, mail_addr = srvr_sock.accept()
        data = recv_by_size(mail_sock)
        data = pickle.loads(data)

        decrypted_data = wrap.unwrap_with_rsa(data, K_PRIVATE)
        next_stop = decrypted_data[len(decrypted_data) - 1]
        next_stop = wrap.unpad(next_stop)
        decrypted_data.pop(len(decrypted_data) - 1)  # removes the ip of the next stop

        with MAILBOX_LOCK:
            MAIL = decrypted_data

        with NEXT_STOP_LOCK:
            NEXT_STOP = next_stop
