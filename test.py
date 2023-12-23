class Hoge:
    def __init__(self, a, b):
        self.a = a
        self.b = b
    
    def test(self):
        return self

g = Hoge(1, 2)
p = g.test()
print(p.a)
