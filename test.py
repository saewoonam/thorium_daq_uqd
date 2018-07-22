class A:
    def __init__(self):
        self.a = 1
        self.b = B()
class B:
    def __init__(self):
        self.b = 2
        print('init class B')
