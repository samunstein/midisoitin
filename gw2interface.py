from collections import defaultdict

KEYS = ["1", "2", "3", "4", "5", "x", "q", "e", "r", "0"]

class MidiInterface():
    def __init__(self):
        self.nuotit = defaultdict(lambda: [])
        self.inputit = []

    def __sendInput(self, inputst):
        self.inputit.append("SendInput " + inputst)

    def __sleep(self, kauan):
        self.inputit.append("Sleep, " + str(int(kauan)))

    def addNote(self, track, channel, pitch, time, duration, volume):
        self.nuotit[time].append(("n", pitch))

    def addTempo(self, track, time, tempo):
        self.nuotit[time].append(("t", tempo))

    def addProgramChange(self, *args):
        pass

    def writeFile(self):
        self.inputit = []
        tempo = 60
        prevtime = 0
        prevokt = 0
        for time in sorted(self.nuotit):
            # Sleep until next note
            väli = time - prevtime
            if väli > 0:
                self.__sleep(väli * 60 / tempo * 1000)
                prevtime = time

            for n in self.nuotit[time]:
                (tyyppi, numero) = n
                if tyyppi == "t":
                    tempo = float(numero)
                elif tyyppi == "n":
                    korkeus = int(numero)
                    oktr = (korkeus - 60) // 12
                    # Ei alle -1 tai yli 1
                    okt = max(min(oktr, 1), -1)
                    # Ei pysty ylennyksiin
                    nuotnums = {
                        0: 0,
                        1: 0,
                        2: 1,
                        3: 1,
                        4: 2,
                        5: 3,
                        6: 3,
                        7: 4,
                        8: 4,
                        9: 5,
                        10: 5,
                        11: 6
                    }
                    nuotnum = nuotnums[korkeus % 12]

                    # Erikoiscase yläoktaavin ylä C (koska se on mahollinen soittaa)
                    if korkeus == 84:
                        nuotnum = 7
                        okt = 1

                    oktvaihd = okt - prevokt
                    if oktvaihd > 0:
                        self.__sendInput(oktvaihd * KEYS[-1])
                    elif oktvaihd < 0:
                        self.__sendInput(-oktvaihd * KEYS[-2])
                    prevokt = okt

                    self.__sendInput(KEYS[nuotnum])

        print("\n".join(self.inputit))
