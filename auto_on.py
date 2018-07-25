import auto_reset
import compressor
import datetime
import pause
import time

# target = 69
# time_target = datetime.datetime(2018, 7, 24, 17, 10)
target = 273+5
time_target = datetime.datetime(2018, 7, 25, 5)
print('Waiting for %r' % time_target)
pause.until(time_target)
print('Done waiting, waiting to warm up more %f' % target)
while auto_reset.get_temp() < target:
    time.sleep(60)
print('Done warming up')
compressor.on()
