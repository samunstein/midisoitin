import abc


class OutputRajapinta(abc.ABC):
    @abc.abstractmethod
    def nuotti(self, track, channel, pitch, time, duration, volume):
        pass

    @abc.abstractmethod
    def tempo(self, track, time, tempo):
        pass

    @abc.abstractmethod
    def soitin(self, track, channel, time, program):
        pass

    @abc.abstractmethod
    def kirjoita(self):
        pass
