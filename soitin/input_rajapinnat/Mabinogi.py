from soitin.input_rajapinnat.InputRajapinta import InputRajapinta
from soitin.input_rajapinnat.ArcheAge import ArcheAge
from soitin.asetukset import *
from soitin.apu import lue_luku

class Mabinogi(InputRajapinta):
    def muunna(self, merkit):
        # Ensin muunnetaan teksti Archeage-formaatilla.
        teksti = ArcheAge().muunna(merkit)
        uusteksti = list()
        indeksi = 0
        o = 5
        while indeksi < len(teksti):
            merkki = teksti[indeksi]

            # Muunnellaan n:t oktaavivaihdoksiksi ja oikeaksi nuotiksi
            if merkki.lower() == "n":
                indeksi, n = lue_luku(teksti, indeksi + 1)
                # Nuotin korkeus oktaavissa
                num = n % 12
                nuotteksti = ""
                # Etsitään oikea nuottimerkki
                for nuotti in sorted(NUOTISTO, key=lambda x: NUOTISTO[x]):
                    # Jos löytyi niin asetetaan nuotin tekstiksi vastaava kirjain ja tarvittaessa alennus,
                    # jos nuotti ei osu suoraan valkoisen painikkeen kohdalle.
                    if nuotteksti == "" and NUOTISTO[nuotti] >= num:
                        nuotteksti = nuotti + (NUOTISTO[nuotti] - num) * YLENNYKSET[2]

                uusteksti.append("{}{}{}{}{}".format(KONTROLLI[2], n // 12, nuotteksti,
                                                     KONTROLLI[2], o))

            # Koska Mabinogi soittaa musiikkia paljon kovemmalla kuin mikään muu, sen volume-arvoja
            # pitää korottaa (kerrotaan seitsemällä), jotta musiikista kuuluisi mitään.
            elif merkki.lower() == "v":
                indeksi, v = lue_luku(teksti, indeksi + 1)
                uusteksti.append(KONTROLLI[5] + str(min(127, v * 7)))

            # Ja pidetään oktaavia muistissa.
            else:
                if merkki.lower() == "o":
                    _, o = lue_luku(teksti, indeksi + 1)

                uusteksti.append(merkki)

            indeksi += 1

        return "".join(uusteksti)
