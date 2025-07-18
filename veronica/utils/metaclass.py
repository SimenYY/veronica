class NoInstances(type):
    """元类实现禁止实例化
    """
    def __call__(self, *args, **kwargs):
        raise TypeError("Can't instantiate directly")
    

class Singleton(type):
    """元类实现单例模式
    
    """
    def __init__(self, *args, **kwargs):
        print("singleton init")
        self.__instance = None
        super().__init__(*args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        print("singleton call")
        if self.__instance is None:
            self.__instance = super().__call__(*args, **kwargs)

        return self.__instance