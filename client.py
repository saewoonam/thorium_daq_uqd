#
#   simple client in Python to test the new bell server
#   Connects REQ socket to tcp://localhost:5555
#

import zmq
import time

context = zmq.Context()

#  Socket to talk to server
print("Connecting to new bell server...")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")


def send_message(msg):
    if type(msg) is str:
        msg = msg.encode('UTF-8')
    socket.send(msg)
    response = socket.recv()
    if len(response) < 256:
        print("[ request: %s ]: %s" % (msg, response))
    else:
        print("[ request: %s]: length: %d" % (msg, len(response)))
    if msg.startswith(b'stream'):
        return response
    else:
        return response.decode('UTF-8')

send_message('start')

send_message(b'getcounts')
send_message('getcounts 0.1')
data = send_message(b'stream 0.1')
send_message(b'log')
time.sleep(1)
send_message(b'log off')
