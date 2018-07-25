""" Use simple subclassing example from numpy docs:
https://docs.scipy.org/doc/numpy-1.14.0/user/basics.subclassing.html
"""
import numpy as np

class RealisticInfoArray(np.ndarray):

    def __new__(cls, input_array, info=None):
        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        obj = np.asarray(input_array).view(cls)
        # add the new attribute to the created instance
        obj.info = info
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # see InfoArray.__array_finalize__ for comments
        if obj is None: return
        self.info = getattr(obj, 'info', None)


import numpy as np

class RingArray(np.ndarray):

    def __new__(cls, input_array, info=None, start_index=0):
        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        obj = np.asarray(input_array).view(cls)
        # add the new attribute to the created instance
        obj.info = info
        obj.start_index = start_index
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # see InfoArray.__array_finalize__ for comments
        if obj is None: return
        self.info = getattr(obj, 'info', None)

    def add(self, data, new_start_index=-1):
        if new_start_index > 0:
            self.start_index = new_start_index
        idx = (self.start_index + np.arange(len(data)) ) % len(self)
        self[idx] = data
        self.start_index = self.start_index + len(data)

    def __getitem__(self, i):
        if False:
                if (isinstance(i, slice)):
                    start = i.start
                    stop = i.stop
                    step = i.step
                    print(start, stop, step)       
        else:
            return super(RingArray, self).__getitem__(i)
