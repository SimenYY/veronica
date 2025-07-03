



class Demo:
    
    __slots__ = ()
    

# class Demo1(Demo):
    
    def set_name(self, name: str):
        print(self.__dict__)
        self.name = name
        print(self.__dict__)
        



d = Demo()

d.set_name("set_name")
print(d.name)