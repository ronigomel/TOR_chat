from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad


class RsaWrapping(object):
    def __init__(self, blocksize: int, e_blocksize: int):
        self.BLOCK_SIZE = blocksize
        self.E_BLOCKSIZE = e_blocksize

    def wrapping(self, route: dict, data: list) -> tuple:
        next_stop = data[len(data) - 1]
        data = data[:len(data) - 1]
        keys = list(route.values())
        msg = data[0]
        halves = []
        counter = 1
        for i in range(len(keys)-1):
            print(len(msg))
            msg = pad(msg, self.BLOCK_SIZE)
            msg = PKCS1_OAEP.new(keys[i]).encrypt(msg)
            halves.append(msg[(len(msg) // 2):])
            msg = msg[:(len(msg) // 2)] + data[i + 1]

        msg = pad(msg, self.BLOCK_SIZE)
        msg = PKCS1_OAEP.new(keys[len(keys) - 1]).encrypt(msg)
        print(msg)
        return halves, msg, next_stop

    def unwrap(self, halves: list, msg, key):
        print(len(msg))
        decrypted = PKCS1_OAEP.new(key).decrypt(msg)
        decrypted = unpad(decrypted, self.BLOCK_SIZE)
        next = decrypted[:self.E_BLOCKSIZE // 2] + halves[len(halves) - 1]
        ip = decrypted[self.E_BLOCKSIZE // 2:].decode()
        halves.pop(len(halves) - 1)

        return ip, next, halves

    def wrap_single(self, msg: str, pubkey: RSA.generate(1024).publickey()):
        msg = pad(msg.encode(), self.BLOCK_SIZE)
        encrypted = PKCS1_OAEP.new(pubkey).encrypt(msg)
        return encrypted

    def unwrap_single(self, cipher, privkey: RSA.generate(1024)):
        decrypted = PKCS1_OAEP.new(privkey).decrypt(cipher)
        decrypted = unpad(decrypted, self.BLOCK_SIZE).decode()
        return decrypted



if __name__ == '__main__':
    r = RsaWrapping(86, 128)
    e1 = RSA.generate(1024)
    ep1 = e1.publickey()

    e2 = RSA.generate(1024)
    ep2 = e2.publickey()

    e3 = RSA.generate(1024)
    ep3 = e3.publickey()

    e4 = RSA.generate(1024)
    ep4 = e4.publickey()

    route = {'127.0.0.1': ep1, '211.110.13.2': ep2, '115.11.11.11': ep3, '0.0.0.0': ep4}
    data = ['hi my name is jeff'.encode(), '127.0.0.1'.encode(), '211.110.13.2'.encode(), '115.11.11.11'.encode(),
            '0.0.0.0'.encode()]
    w = r.wrapping(route, data)
    print(w)
    w = r.unwrap(w[0], w[1], e4)
    print(w)
    w = r.unwrap(w[2], w[1], e3)
    print(w)
    w = r.unwrap(w[2], w[1], e2)
    print(w)
    w = r.unwrap(w[2], w[1], e1)
    print(w)