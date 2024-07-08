from abc import ABC, abstractmethod

class AbstractScreen(ABC):
    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def drawImage(self, image):
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def sleep(self):
        pass

    @abstractmethod
    def wakeup(self):
        pass
