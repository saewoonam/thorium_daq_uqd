import shm_buffer
import time

buf = shm_buffer.buffer()

f = open('dinner_wed.log','w')
while True:
    f.write('%.2f, %r\n' % (time.time(), buf.singles()))
    f.flush()
