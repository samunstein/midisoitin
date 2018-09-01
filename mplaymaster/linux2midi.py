#try:
#    import pypm as pm
#except:
#    print('unable to import portmidi module')


class midiDevice:
    def __init__(self):
        self.device = None

    def midievent(self, buf):
        if self.device != None:
            if len(buf) == 1:
                self.device.WriteShort(buf[0])
            elif len(buf) == 2:
                self.device.WriteShort(buf[0], buf[1])
            elif len(buf) == 3:
                self.device.WriteShort(buf[0], buf[1], buf[2])

    def mididataset1(self, address, data):
        pass

    def close(self):
        #if self.device != None:
        #    self.device.Close()
        pass

    # TODO: Add some kind of sensible linux implementation
    def play(self, midi):
        file = open("mid.mid", "wb")
        file.writelines(midi.readlines())

        file.close()

        import subprocess
        import time

        c = time.perf_counter()

        subprocess.call(["timidity", "mid.mid"], stdout=subprocess.PIPE)

        while time.perf_counter() < c + 0.2:
            pass

        subprocess.call(["rm", "mid.mid"])