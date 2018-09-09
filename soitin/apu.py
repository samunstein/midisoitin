from soitin.asetukset import VIRHE


# Lukee kokonaisluvun annetusta kohdasta, ja palauttaa indeksin viimeiseen
# merkkiin kokonaisluvussa.
def lue_luku(merkit, alku):
    loppu = alku
    while loppu < len(merkit) and merkit[loppu].isdigit():
        loppu += 1

    if loppu > alku:
        return loppu - 1, int(merkit[alku:loppu])
    else:
        raise ValueError("Virheellinen kokonaisluku kohdassa {}.".format(alku), alku)


# Palauttaa seuraavan merkin, paitsi jos ollaan lopussa, jolloin palautuu virhemerkki
def seuraava(merkit, indeksi):
    if indeksi + 1 < len(merkit):
        return merkit[indeksi + 1]
    else:
        return VIRHE
