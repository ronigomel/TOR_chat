__author__ = 'Yossi'

# from  tcp_by_size import send_with_size ,recv_by_size


SIZE_HEADER_FORMAT = "000000000|"  # n digits for data size + one delimiter
size_header_size = len(SIZE_HEADER_FORMAT)
TCP_DEBUG = True

VER = 'Python3'


def str_byte(_s, direction):
    if VER == 'Python3':
        if direction == 'encode':
            return _s.encode()
        else:
            return _s.decode('utf8')
    else:
        return _s


def recv_by_size(sock):
    size_header = b''
    data_len = 0
    while len(size_header) < size_header_size:
        _s = sock.recv(size_header_size - len(size_header))
        if _s == b'':
            break
        else:
            size_header += _s
    data = b''
    if size_header != b'':
        data_len = int(size_header[:size_header_size - 1])
        while len(data) < data_len:
            _d = sock.recv(data_len - len(data))
            if _d == b'':
                break
            else:
                data += _d

        """
        if TCP_DEBUG and size_header != b'':
            print("\n" + " Recv(%s)>>>%s" % (size_header, data.decode('utf-8')[:min(100, len(data))]), end='')
            """

    if data_len != len(data):
        data = b''  # Partial data is like no data !
    return data  # ( or data.decode() if want it as string)


def send_with_size(sock, bdata):
    len_data = len(bdata)
    header_data = str(len(bdata)).zfill(size_header_size - 1) + "|"

    bytea = bytearray(header_data, encoding='utf8') + bdata

    sock.send(bytea)

    """if TCP_DEBUG and len_data > 0:
        print('\n' + " Sent(%s)>>>%s" % (len_data, bdata.decode('utf-8')[:min(100, len(bdata))]), end='')"""
