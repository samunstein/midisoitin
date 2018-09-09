from soitin.input_rajapinnat.InputRajapinta import InputRajapinta
from soitin.asetukset import *
from soitin.apu import seuraava


class O1(InputRajapinta):
    def muunna(self, merkit):
        i = 0
        teksti = merkit.replace("#", YLENNYKSET[1]) \
            .replace("-", JATKO[0]) \
            .replace("b", YLENNYKSET[2]) \
            .replace("h", NUOTIT[-1]) \
            .replace("H", NUOTIT[-1].upper()) \
            .replace("&", KONTROLLI[6])
        uusteksti = list()

        # Alkuun pitää laitta nuotit puolipituisiksi, koska O1-kurssin soitin tekee näin
        uusteksti.append("l8")
        oktaavi = 5
        while i < len(teksti):
            # Jos O1-kurssilla nuotin perässä on numero, se kertoo nuotin oktaavin. Meillä
            # tämä ei käy päinsä, joten kyseinen numero korvataan oktaavivaihdoksilla sen ympärillä
            if teksti[i].lower() in NUOTIT and seuraava(teksti, i).isdigit():
                okt = int(teksti[i + 1])
                uusteksti.append("{}{}{}{}{}".format(KONTROLLI[2], okt,
                                                     teksti[i], KONTROLLI[2], oktaavi))
                i += 1

            # Pidetään oktaavia muistissa
            else:
                if teksti[i] in KONTROLLI[:2]:
                    if teksti[i] == KONTROLLI[1]:
                        oktaavi += 1
                    else:
                        oktaavi -= 1

                uusteksti.append(teksti[i])
            i += 1

        return "".join(uusteksti)
