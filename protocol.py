class Protocol(object):
    def __init__(self):
        pass

    def construct_msg(self, command: str, args: list) -> str:
        command = command.lower()

        if command == 'hi':
            data = 'HI-NAME: ' + args[0] + '-PUBKEY: ' + str(args[1])
            return data
        elif command == 'msg':
            data = 'MSG-' + args[0]
            return data
        elif command == 'route':
            data = 'ROUTE-[' + ','.join(args[0]) + ']'
            return data
        elif command == 'ping':
            return 'PING'
        elif command == 'alive':
            return 'ALIVE'


    def deconstruct_msg(self, msg: str) -> list:
        msg = msg.split('-')   # msg[0] --> command
        msg[0] = msg[0].lower()
        if msg[0] == 'route':
            msg[1] = msg[1].replace('[', '')
            msg[1] = msg[1].replace(']', '')
            msg_list = msg[1].split(',')
            msg[1] = msg_list
            return msg
        elif msg[0] == 'hi':
            msg[1] = msg[1].split(': ')[1]
            msg[2] = msg[2].split(': ')[1]
            return msg

