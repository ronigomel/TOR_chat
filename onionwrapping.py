from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

_err = 'ERROR: FAILED TO DECRYPT'


class OnionWrapping(object):
    def __init__(self):
        pass

    def cut_to_blocks(self, data: list) -> list:
        n = 117  # length of block is 1024bits aka 128bytes minus 11 for the RSA module
        for i in range(len(data)):
            data[i] = data[i].encode('utf-8')

        excess_padding = n - len(data[0])
        if excess_padding > 1:
            print(excess_padding)
            leave_space_for = len(str(excess_padding)) + 1
            excess_padding = ('!' + str(excess_padding)).encode()
        elif excess_padding < 0:
            excess_padding = n + excess_padding
            leave_space_for = len(str(excess_padding)) + 1
            excess_padding = ('!' + str(excess_padding)).encode()
        else:
            leave_space_for = 1
            excess_padding = '!'.encode()

        chunks = [data[0][i:i + n] for i in range(0, len(data[0]), n)]
        if len(chunks[len(chunks) - 1]) < n:
            chunks[len(chunks) - 1] = chunks[len(chunks) - 1].ljust(n - leave_space_for, b'0')
            chunks[len(chunks) - 1] += excess_padding

        for i in range(1, len(data)):
            excess_padding = n - len(data[i])
            leave_space_for = len(str(excess_padding)) + 1
            excess_padding = ('!' + str(excess_padding)).encode()

            chunks.append(data[i].ljust(n - leave_space_for, b'0'))
            chunks[len(chunks) - 1] += excess_padding

        return chunks

    def unwrap_with_rsa(self, data: list, private_key: bytes) -> list:
        for i in range(len(data)):
            data[i] = PKCS1_v1_5.new(private_key).decrypt(data[i], _err)

        return data

    def wrap_with_rsa(self, route: dict, data: list) -> list:  ### ORI
        data = self.cut_to_blocks(data)
        counter = len(route)

        for i in range(len(data) - len(route)):
            for j in route.keys():
                print(len(data[i]))
                data[i] = PKCS1_v1_5.new(route[j]).encrypt(data[i])

        counter = len(route) - 1
        for i in range(len(data) - len(route), len(route) - 1):
            for ip in list(route.keys())[:counter]:
                data[i] = PKCS1_v1_5.new(route[ip]).encrypt(data[i])
            counter -= 1
        return data

    def unpad(self, data: str) -> str:
        num_pads = data[data.rfind('!'):]
        if num_pads == '!':
            data = data[:len(data) - 1]
        else:
            num_pads = num_pads.strip('!')
            data = data[:len(data) - int(num_pads)]

        return data


if __name__ == '__main__':
    o = OnionWrapping()
    k_priv = RSA.generate(1024)
    k_pub = k_priv.publickey()

    w = {'o': 1, 'b': 1, 'c': 3, 'd': 5}
    l = ['aaaaaaaaaaaaaaaaaaaa', '127.0.0.1', '0.0.0.0', '83.192.1.25']
    r = {'127.0.0.1': RSA.generate(1024).publickey(), '0.0.0.0': RSA.generate(1024).publickey(), '83.192.1.25': RSA.generate(1024).publickey()}
    w = o.wrap_with_rsa(r, l)
    print(w)

