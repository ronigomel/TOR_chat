from Crypto.PublicKey import RSA
import socket
from tcp_by_size import recv_by_size, send_with_size
import threading
import pickle
import datetime
from onion_wrapping import RsaWrapping


K_PUBLIC = RSA.RsaKey
K_PRIVATE = RSA.RsaKey
STOP = False
MAIL = []
MAILBOX_LOCK = threading.Lock()

NEXT_STOP = ''
NEXT_STOP_LOCK = threading.Lock()


def log(action: str, ip: str, port: int):
    s = '----------------------------------- ' + action + ' -----------------------------------'
    print(s)
    print('IP: ' + ip + ' | PORT: ' + str(port))
    print('TIME: ' + str(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")))
    print('-' * len(s))


def generate_keys():
    global K_PRIVATE
    global K_PUBLIC

    with open('publickey8822.pem', 'r') as pub:
        K_PUBLIC = RSA.import_key(pub.read())
    with open('privatekey8822.pem', 'r') as priv:
        K_PRIVATE = RSA.import_key(priv.read())




def main(ip: str, port: int):
    global MAILBOX_LOCK
    global NEXT_STOP_LOCK
    global MAIL
    global NEXT_STOP
    cipher = RsaWrapping(86, 128)
    generate_keys()

    srv_socket = socket.socket()
    srv_socket.bind((ip, port))
    srv_socket.listen(1)
    print('listening...')
    cli_sock, addr = srv_socket.accept()  # first connection is always 127.0.0.1
    log('NEW CONNECTION', addr[0], addr[1])

    send_with_size(cli_sock, pickle.dumps(K_PUBLIC.exportKey()))  # sending the public key to the

    t = threading.Thread(target=mailbox, args=(srv_socket,))
    t.start()

    while not STOP:
        if len(MAIL) > 0 and NEXT_STOP != '':
            with MAILBOX_LOCK:
                to_send = MAIL
                MAIL = ''
            with NEXT_STOP_LOCK:
                next_ip = NEXT_STOP
                log('SENT', NEXT_STOP.split(':')[0], int(NEXT_STOP.split(':')[1]))
                NEXT_STOP = ''
            to_send = pickle.dumps([to_send, next_ip])
            send_with_size(cli_sock, to_send)
        elif len(MAIL) > 0 and NEXT_STOP == '':
            with MAILBOX_LOCK:
                send_with_size(cli_sock, pickle.dumps(MAIL))
                log('SENT DATA', '', 0)
                MAIL = ''




def mailbox(srv_sock: socket.socket):
    global K_PRIVATE
    global MAIL
    global NEXT_STOP

    cipher = RsaWrapping(86, 128)
    while not STOP:
        srv_sock.listen(1)
        mail_sock, mail_addr = srv_sock.accept()
        data = recv_by_size(mail_sock)
        log('RECEIVED', mail_addr[0], mail_addr[1])
        data = pickle.loads(data)
        print(data)

        if data[0] == 'PING':
            send_with_size(mail_sock, pickle.dumps('ALIVE'))
            log('PING / ALIVE', 'super server', 0)
        else:
            if len(data[0]) != 0:
                decrypted_data = cipher.unwrap(data[0], data[1], K_PRIVATE)
                if type(decrypted_data) == tuple:
                    next_stop = decrypted_data[0]
                    decrypted_data = decrypted_data[1:]
                    print(next_stop)
                    with MAILBOX_LOCK:
                        MAIL = decrypted_data
                    with NEXT_STOP_LOCK:
                        NEXT_STOP = next_stop
            else:
                decrypted = cipher.unwrap_single(data[1], K_PRIVATE)
                with MAILBOX_LOCK:
                    MAIL = decrypted
                with NEXT_STOP_LOCK:
                    NEXT_STOP = ''
                print(decrypted)



if __name__ == '__main__':
    main('192.168.1.240', 8821)