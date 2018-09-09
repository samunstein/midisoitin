from soitin.input_rajapinnat.InputRajapinta import InputRajapinta
from soitin.asetukset import *
from soitin.apu import lue_luku, seuraava


class ArcheAge(InputRajapinta):
    def muunna(self, merkit):
        # Perus replacet alkuun.
        teksti = merkit.replace("c", NUOTIT[0]) \
            .replace("d", NUOTIT[1]) \
            .replace("e", NUOTIT[2]) \
            .replace("f", NUOTIT[3]) \
            .replace("g", NUOTIT[4]) \
            .replace("a", NUOTIT[5]) \
            .replace("b", NUOTIT[6]) \
            .replace("<", KONTROLLI[0]) \
            .replace(">", KONTROLLI[1]) \
            .replace("o", KONTROLLI[2]) \
            .replace("t", KONTROLLI[3]) \
            .replace("l", KONTROLLI[4]) \
            .replace("v", KONTROLLI[5]) \
            .replace(",", KONTROLLI[6]) \
            .replace("r", TAUKO[1]) \
            .replace("&", JATKO[1]) \
            .replace("+", YLENNYKSET[1]) \
            .replace("#", YLENNYKSET[1]) \
            .replace("-", YLENNYKSET[2])
        indeksi = 0
        l = 4
        uusteksti = list()

        # Käydään merkki kerrallaan läpi
        while indeksi < len(teksti):
            merkki = teksti[indeksi]
            # Tämä on toinen archeage-formaatin pihveistä. l-nuotinpitdenasetusmerkki voi sisältää
            # perässään pisteen, joka tarkoittaa 1.5-kertaista pituutta. Tätä varten jaetaan l:n arvo
            # 1.5:llä, ja asetetaan se sellaisenaan tekstiin.
            if merkki == "l":
                indeksi, l = lue_luku(teksti, indeksi + 1)
                if seuraava(teksti, indeksi) == ".":
                    l /= 1.5
                    indeksi += 1
                uusteksti.append(merkki + str(l))

            # Piste tarkoittaa myös nuotin perässä pituuden kertomista 1.5:llä, joten
            # nuottia pitää jatkaa samalla nuotilla, joka on puolet alkuperäisen pituudesta
            elif merkki == ".":
                loppu = indeksi
                alku = loppu
                # Etsitään numeron alku, jos sellainen on
                while teksti[alku - 1].isdigit():
                    alku -= 1

                # Nuotin pituus talteen
                if loppu != alku:
                    pituus = int(teksti[alku:loppu])
                else:
                    pituus = l

                # Jos nuotti on ylennetty tai alennettu niin otetaan se huomioon
                nuotti = teksti[alku - 1]
                if nuotti in YLENNYKSET:
                    nuotti = teksti[alku - 2:alku]

                # Lisätään tarpeeksi tarkka desimaaliluku nuotin pituudesta
                uusteksti.append("&{}{:.6f}".format(nuotti, pituus * 2))

            # Ilman erikoisuuksia lisätään merkki sellaisenaan
            else:
                uusteksti.append(merkki)

            indeksi += 1

        return "".join(uusteksti)
