# ----------------------------------- IMPORTS -----------------------------------
import socket
import datetime
from tcp_by_size import recv_by_size, send_with_size
import pygame
from test2 import RsaWrapping
import pickle
import threading
import time
import re
from random import shuffle
import sys
from msgs import Message

# ----------------------------------- GRAPHICS RELATED -----------------------------------

pygame.init()

# window
WINDOW_WIDTH = 1250
WINDOW_HEIGHT = 750
SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
SCREEN = pygame.display.set_mode(SIZE)

# colours
WHITE = (255, 255, 255)

# jpg / png files
FILE_NAME = 'media/intro.jpg'
IMG = pygame.image.load(FILE_NAME)
my_msg_img = 'media/text_bubble.png'
not_mymsg_img = 'media/not_mymsg_bubble.png'

# ----------------------------------- INITIALISING -----------------------------------
SRV_STATION_ADDR = 'stationsrv_address.txt'
STOP = False
DST_PUB_KEY = None
DST_ADDRESS = ()
dst_lock = threading.Lock()
WRAP = RsaWrapping(117, 128)

msgs = []
msgs_lock = threading.Lock()
msg_counter = 0
msg_counter_lock = threading.Lock()
SCREEN_LOCK = threading.Lock()


# ----------------------------------- ACTUAL CODE -----------------------------------
def log(action: str, ip: str, port: int):
    s = '----------------------------------- ' + action + ' -----------------------------------'
    print(s)
    print('IP: ' + ip + ' | PORT: ' + str(port))
    print('TIME: ' + str(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")))
    print('-' * len(s))


def read_file(filename: str, permission: str):
    with open(filename, permission) as f:
        ip = f.readline().strip('\n')
        port = int(f.readline().strip('\n'))
    return ip, port


def main():
    global DST_PUB_KEY
    if len(sys.argv) == 2:
        with open(sys.argv[1], 'rb') as f:
            DST_PUB_KEY = f.read()

    station_sock = socket.socket()
    ip, port = read_file(SRV_STATION_ADDR, 'r')  # complementary server only
    station_sock.connect((ip, port))
    log('NEW CONNECTION', ip, port)

    public_k = recv_by_size(station_sock)

    all_socket = socket.socket()

    ip_ss, port_ss = read_file('supersrv_address.txt', 'r')
    all_socket.connect((ip_ss, port_ss))
    to_send = ['HI', ip, port, public_k]
    send_with_size(all_socket, pickle.dumps(to_send))

    all_socket.close()

    t = threading.Thread(target=user_)
    t.start()

    all_socket = socket.socket()
    while not STOP:
        data = pickle.loads(recv_by_size(station_sock))
        if type(data) != list:
            msg = got_mail(data)
            next_stop = ''

        else:
            msg = data[0]
            next_stop = data[1].split(':')
            next_stop = (next_stop[0], int(next_stop[1]))

        if next_stop != '':
            all_socket.connect(next_stop)
            send_with_size(all_socket, msg)
        else:
            new_message(False, msg, 'media/not_mymsg_bubble.png')


def got_mail(data: str):
    global DST_ADDRESS
    data = data.rsplit('[', 1)
    msg = data[0].rstrip(' ')
    dst_addr = data[1].strip(']').split(':')[1:]
    with dst_lock:
        DST_ADDRESS = dst_addr[0], int(dst_addr[1])
    return msg


def change_screen(img_path: str):
    global IMG
    global FILE_NAME
    FILE_NAME = img_path
    IMG = pygame.image.load(img_path)
    with SCREEN_LOCK:
        SCREEN.fill(WHITE)
        SCREEN.blit(IMG, (0, 0))
    pygame.display.flip()


def connect_supersrv():
    supersrv_socket = socket.socket()
    supersrv_addr = read_file('supersrv_address.txt', 'r')
    supersrv_socket.connect(supersrv_addr)

    send_with_size(supersrv_socket, pickle.dumps(['MSG']))
    route = pickle.loads(recv_by_size(supersrv_socket))
    return route


def ip_validation(ip: str) -> bool:
    regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    if re.search(regex, ip):
        return True
    return False


def remix_route(route: dict, dst_ip: str) -> dict:
    new_route = {dst_ip: DST_PUB_KEY}
    keys = list(route.keys())
    shuffle(keys)
    for i in route:
        new_route[i] = route[i]
    return new_route


def new_message(sent: bool, text: str, image_file):
    global msg_counter
    with msg_counter_lock:
        msg_counter += 1
        with msgs_lock:
            if msg_counter >= 5:
                y_place = msgs[len(msgs) - 1].get_placement()[1]
                for i in range(len(msgs)):
                    msgs[i].set_placement((msgs[i].get_placement()[0], msgs[i].get_placement()[1] - 102))
                    print(msgs[i].get_text())
                    if msgs[i].get_placement()[1] < 141:
                        msgs[i].erase()
            elif len(msgs) == 0:
                y_place = 141
            else:
                y_place = msgs[len(msgs) - 1].get_placement()[1] + 102
    x_place = 0
    if sent:
        x_place = 1002
    m = Message(sent, text, image_file, (x_place, y_place))
    with msgs_lock:
        msgs.append(m)
    update_msgs()


def update_msgs():
    with msgs_lock:
        if len(msgs) >= 5:
            with SCREEN_LOCK:
                print(msgs[len(msgs) - 5].get_placement())
                msgs[len(msgs) - 5].delete(SCREEN)
        for i in range(len(msgs)):
            if msgs[i].get_seen():
                with SCREEN_LOCK:
                    msgs[i].print(SCREEN)
    pygame.display.flip()
    pygame.display.update()


def send_msg(data: str, destination_ip: tuple):
    route = connect_supersrv()
    new_route = remix_route(route, destination_ip)
    ip, port = read_file(SRV_STATION_ADDR)
    data = data + ' [return to: myaddr: ' + ip + ':' + str(port) + ']'
    data = [WRAP.wrap_single(data, DST_PUB_KEY)]
    for i in range(1, len(list(new_route.keys()))):
        data.append(list(new_route.keys())[i] + ':' + str(route[list(new_route.keys())[i]][0]))
    WRAP.wrapping(new_route, data)


def user_():
    global STOP
    global IMG

    input_box = pygame.Rect(523, 388, 140, 32)
    font = pygame.font.Font(None, 25)
    active = True
    colour_inactive = (166, 166, 166)
    colour_active = WHITE

    colour = colour_inactive
    text = ''

    destination_station = ''
    change_screen('media/intro.jpg')
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if FILE_NAME == 'media/intro.jpg':
                        change_screen('media/made_by.jpg')
                        time.sleep(1.5)
                        change_screen('media/meeting_setting.jpg')
                    elif FILE_NAME == 'media/meeting_setting.jpg' or FILE_NAME == 'media/meeting_setting2.jpg' and text != '':
                        if ':' in text:
                            text = text.split(':')
                            ip = text[0]
                            if text[1].isdigit():
                                if 1 <= int(text[1]) <= 65535:
                                    port = text[1]
                                    if ip_validation(ip) == True:
                                        destination_station = (text[0], text[1])
                                        change_screen('media/chat.jpg')
                                        input_box = pygame.Rect((77, 627), (5000, 100))
                                    else:
                                        change_screen('media/meeting_setting2.jpg')
                                else:
                                    change_screen('media/meeting_setting2.jpg')
                            else:
                                change_screen('media/meeting_setting2.jpg')
                        else:
                            change_screen('media/meeting_setting2.jpg')
                        text = ''
                        colour = colour_inactive
                        active = not active
                    elif FILE_NAME == 'media/chat.jpg':
                        with open('my_messages.txt', 'a+') as msgs_file:
                            msgs_file.write(text + '\n')
                            # send_msg(text, destination_station)
                            new_message(True, text, my_msg_img)
                        text = ''
                        # change_screen(FILE_NAME)
                elif event.key == pygame.K_BACKSPACE:
                    if FILE_NAME == 'media/chat.jpg' or FILE_NAME == 'media/meeting_setting.jpg' or 'media/meeting_setting2.jpg':
                        text = text[:-1]
                else:
                    if FILE_NAME == 'media/chat.jpg' or FILE_NAME == 'media/meeting_setting.jpg' or 'media/meeting_setting2.jpg':
                        text += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN and FILE_NAME != 'media/intro.jpg' and FILE_NAME != 'media/made_by.jpg':
                if input_box.collidepoint(event.pos):
                    # Toggle the active variable.
                    active = not active
                else:
                    active = False
                # Change the current color of the input box.
                colour = colour_active if active else colour_inactive

        if FILE_NAME != 'media/intro.jpg' and FILE_NAME != 'media/made_by.jpg':
            if FILE_NAME != 'media/chat.jpg':
                change_screen(FILE_NAME)
            else:
                txtbox = pygame.image.load('media/txt_box.jpg')
                with SCREEN_LOCK:
                    SCREEN.blit(txtbox, (0, 592))
            # Render the current text.
            txt_surface = font.render(text, True, colour)
            # Resize the box if the text is too long.
            if FILE_NAME == 'media/chat.jpg':
                width = max(954, txt_surface.get_width() + 10)
                font = pygame.font.Font(None, 36)
            else:
                width = max(227, txt_surface.get_width() + 10)
            input_box.w = width
            # Blit the text.
            with SCREEN_LOCK:
                SCREEN.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
                # Blit the input_box rect.
                pygame.draw.rect(SCREEN, colour, input_box, 2)
            pygame.display.update()
            # If the user clicked on the input_box rect.


if __name__ == '__main__':
    # send_msg('my name is jeff', '8.8.8.8')
    user_()
    # ip_validation('123.0.0.1')
    # main()
