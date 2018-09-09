import inspect
import multiprocessing
from soitin.asetukset import *
from soitin.apu import lue_luku, seuraava


class Soitin:
    """
    Formaatti:
    Nuotti:         cdefgab
        Nuotin korkeus asetetaan käyttäen (oletuksena) nuotistoa oktaavin
        viimeisenä nuottina epäsuomalaisittain 'b' eikä 'h'.

    Nuotin pituus:  c2de8f8g1
        Nuotille asetetaan pituus laittamalla sen perään numero, joka kertoo
        nuotin pituuden jakajan, kuten musiikissa sanotaan "neljäsosanuotti",
        "kahdeksasosanuotti" jne. Mitä suurempi numero, sitä lyhyempi nuotti.

    Tauko: efg gag e grfgfedecrc
        Tauko asetetaan samalla tavalla kuin nuotti, mutta merkillä ' ' tai 'r'.
        Taukoon pätevät kaikki samat pituudenvaihtelut kuin nuotteihinkin

    Ylennys: ceg ce-g df#a c+ea
        Nuotille voi antaa ylennysmerkin, joka nostaa tai laskee sen korkeutta
        puolella sävelaskeleella. Ylennys ylöspäin annetaan merkillä '+' tai '#',
        alasäpin merkillä '-'.

    Staccato: cde. def. efg. f.e.d.
        Nuotti voi olla nk. staccato-nuotti, joka soitetaan vain lyhyesti,
        mutta joka ei vaikuta seuraavan nuotin ajoitukseen. Staccato asetetaan
        merkillä '.'.

    Jatkomerkit: cdefg_g_a_a_g___ cdefg&gg&ga&aa&ag2&g2
        Jatkomerkillä '_' voi soittaa saman nuotin uudestaan katkaisematta
        sitä välissä, eli jatkaa saman nuotin pituutta sen itsensä verran.
        Merkillä '&' voi jatkaa samaa nuottia uudella nuotilla, jonka pituus
        luetaan normaalisti, kunhan uusi nuotti on korkeudeltaan sama kuin edellinen.

    Kaikki nuotin lisäoptiot yhdessä: c+8_.
        nuotti[ylennys][kesto][jatkomerkit/staccato]

    Oktaavi: ceg >ceg <<cego5ceg
        Oktaavia voi vaihtaa alas ja ylös merkeillä '<' ja '>', tai
        johonkin tiettyyn numeroon (väliltä 1...10) merkinnällä "o*numero*",
        jossa *numero*:n paikalla on numero

    Oletuskesto: l8cccedddfeeddc__ l4cccedddfeeddc1
        Jos nuotille tai tauolle ei anna kestonumeroa, sen pituudeksi tulee
        oletuskesto, joka on oletuksena 4 (neljäsosanuotti). Oletuskestoa
        voi vaihtaa merkinnällä "l*numero*"

    Äänenvoimakkuus: v50cccedddfeeddc1eeeeG2F2ddddF2E2
        Äänenvoimakkuus asetetaan merkinnällä "v*numero*". Nuotin
        äänenvoimakkuutta voi myös lisätä viidelläkymmenellä kirjoittamalla
        nuotti isolla kirjaimella.

    Tempo: t120c.e.c.d.e8d8c.c t240c.e.c.d.e8d8c.c
        Tempor asetetaan antamalla merkintä "m*numero*". Tempo lasketaan
        yksikössä bpm eli iskua minuutissa. Iskulla tarkoitetaan yhden
        neljäsosanuotin kestoa. Tempolla 120 yksi neljäsosanuotti kestää
        siis tasan puoli sekuntia.

    Sointu: (ceg) (<b->df)_.(<a->ce-)_(<b->df)._(ceg)___
        Tavallisten kaarisulkujen sisään voi kirjoittaa soinnun. Käytännössä
        aika ei kulje eteenpäin sulkeiden sisällä, eli kaikki nuotit soitetaan
        samaan aikaan. Soinnun pituutta voi muuttaa kirjoittamalla alaviivoja
        tai pisteitä soinnun jälkeen. '_' ja '.' toimivat samoin kuin
        yksittäisellä nuotilla

    Soitin: [5]cdefg
        Soitinta voi vaihtaa merkinnällä "[*numero*]", jossa soittimen numero
        on midi-speksin mukainen 1-128. Soitin numero 129 on varattu perkussio-
        eli rumpukanavalle.

    Modulaatio: cde2m+1cde2m0cde2
        Merkinnällä "'m'[+/-]*numero*" voi asettaa kaikille seuraaville nuoteille
        modulaation. Jos 'm':n jälkeen on + tai -, nykyiseen modulaatioon lisätään
        tai siitä vähennetään annettu numero. Jos 'm':n jälkeen on pelkkä numero,
        modulaatio vaihtuu suoraan annettuun arvoon. Moduloimaton arvo on 0.

    Raidan vaihto: cccedddfeeddc__,ceg2f2a2ggffe2&e
        Raitaa voi vaihtaa merkillä ','. Pilkuilla erotetut raidat lähtevät soimaan
        samaan aikaan.

    """

    # Lukee liukuluvun annetusta kohdasta ja palauttaa indeksin viimeiseen
    # merkkiin luvussa. Ero lue_luku-funktioon on siinä, että tämä funktio ei pysähdy
    # pisteen kohdalla, vaan ottaa sen mukaan lukuun.
    @staticmethod
    def __lue_float(merkit, alku):
        loppu = alku
        while loppu < len(merkit) and (merkit[loppu].isdigit() or merkit[loppu] == "."):
            loppu += 1

        # Koska formaatin mukaan piste on myös stackato, jos liukuluku loppuu pisteeseen,
        # loppumerkkiä siirretään yksi taakse päin.
        if merkit[loppu - 1] == ".":
            loppu -= 1

        if loppu > alku and merkit[alku:loppu].count(".") <= 1:
            return loppu - 1, float(merkit[alku:loppu])
        else:
            raise ValueError("Virheellinen luku kohdassa {}.".format(alku), alku)

    # Funktio, joka luo midi-tiedoston annetun merkkijonon pohjalta.
    @staticmethod
    def __luo_nuotit(merkit, output, alkuaika=0):

        # Lue_nuotti-funktio, lukee nuotin annetusta kohdasta
        def lue_nuotti(merket, indekse):
            # Katsotaan, onko ylennys- tai alennusmerkkiä.
            if seuraava(merket, indekse) in YLENNYKSET:
                if seuraava(merket, indekse) == YLENNYKSET[2]:
                    ylennys = -1
                else:
                    ylennys = 1

                indekse += 1
            else:
                ylennys = 0

            # Jos perässä on keston ilmaiseva numero, luetaan se kestoksi, muuten oletuskesto
            if seuraava(merket, indekse).isdigit():
                indekse, kestoaika = Soitin.__lue_float(merket, indekse + 1)
                kestoaika = 4 / kestoaika
            else:
                kestoaika = oletuskesto

            # Jos nuotti on staccato, niin annetaan sille lyhyt äänikesto, muuten
            # äänikesto on nuotin koko kestoaika
            if seuraava(merket, indekse) == STACCATO:
                äänikesto = min(1 / 8, kestoaika / 8)
                indekse += 1
                stackato = True
            else:
                stackato = False
                äänikesto = kestoaika

            # Jos ollaan soinnun keskellä, niin aikakesto ja äänikesto muuntuvat soinnun
            # modifierien mukaisesti
            if not aikalisä:
                if stacmod > -1:
                    perusäänikesto = äänikesto
                    äänikesto *= stacmod
                    äänikesto += min(1 / 8, perusäänikesto / 8)
                    stackato = True

                kestoaika += kestoaika * lenmod

            # Jos oli nuotti eikä tauko, niin lisätään nuotti midiin
            # Korkeus lasketaan oktaavin ja nuotin avulla, ja volyymiä
            # lisätään jonkin verran, jos nuotti on isolla kirjoitettu
            if merkki.lower() in nuotit:
                nuotte = (raita, kanava, 12 * oktaavi + nuotit[merkki.lower()] + ylennys + modulaatio,
                          aika, äänikesto, min(volume + (50 if merkki.isupper() else 0), 127), stackato, ylennys)

            # Jos oli tauko, niin tehdään sama mutta äänen pituudella 0
            elif merkki in TAUKO:
                nuotte = (raita, kanava, 60, aika, kestoaika, volume, stackato, ylennys)

            else:
                raise ValueError("Ei nuottia, kohdassa {}.".format(indekse))

            # Palautetaan seuraavan merkin indeksi, ja nuotin aikakesto
            return indekse, kestoaika, nuotte

        # Tästä alkaa funktion luo_midi suoritus
        # Alkuvalmistelut
        nuotit = NUOTISTO

        # Asetetaan alkuarvot nuottien tiedoille
        raita = 0
        aika = alkuaika
        kanava = 0
        oktaavi = 5
        oletuskesto = 1
        volume = 100
        modulaatio = 0

        # Soinnun modifierit ja metatiedot
        maxkesto = 0  # pisimmän nuotin kesto soinnussa
        modmerkit = 0  # pituuteen vaikuttavien merkkien määrä soinnun perässä
        stacmod = 0  # stackaton paikka soinnussa
        lenmod = 0  # pituuden lisäkerroin
        aikalisä = True  # soinnun sisäisiä nuotteja

        # Soittimen tiedot
        soitin = 0  # Nykyinen soitin
        soittimet = dict()  # Kanavat, jotka saadaan soittimien numerolla
        soittimet[soitin] = 0  # Ensimmäinen kanava nollaksi

        # Pisimmän raidan kesto
        maxaika = 0

        # Siivotaan rivinvaihdot pois
        merkit = merkit.replace("\n", "")

        # Jos nuotissa on o1-tyyppinen tempomerkintä, luetaan se
        if merkit.count("/") == 1:
            tempo = int(merkit.split("/")[1])
            merkit = merkit.split("/")[0]
            output.tempo(raita, aika, tempo)

        # Lähdetään lukemaan
        indeksi = 0
        while indeksi < len(merkit):

            merkki = merkit[indeksi]

            # Jos nuotti taikka tauko...
            if merkki.lower() in nuotit or merkki in TAUKO:
                indeksi, aikakesto, nuotti = lue_nuotti(merkit, indeksi)

                lisäkesto = aikakesto

                indeksi += 1

                # Jos on nuotin jatkamismerkki JA seuraana nuotti on ylennyksineen samankorkuinen
                # kuin edellinen, TAI kyseessä on saman nuotin jatkamismerkki, TAI staccato-merkki,
                # niin muutetaan nuotin tietoja jatkomerkkien mukaisella tavalla
                while (seuraava(merkit, indeksi - 1) == JATKO[1] and
                       seuraava(merkit, indeksi).lower() == merkki.lower() and
                       (seuraava(merkit, indeksi + 1) == nuotti[7] or
                       seuraava(merkit, indeksi + 1) not in YLENNYKSET and
                       nuotti[7] == 0)) or \
                      (seuraava(merkit, indeksi - 1) == JATKO[0]) or\
                        seuraava(merkit, indeksi - 1) == STACCATO:

                    # Jos nuotin jatkomerkki, niin luetaan uusi nuotti, ja lisätään kestoa sen mukaan
                    if seuraava(merkit, indeksi - 1) == JATKO[1]:
                        indeksi, lisäkesto, uusnuotti = lue_nuotti(merkit, indeksi + 1)
                        indeksi += 1
                        # Jos uusi nuotti on staccato, niin muutetaan nuotin äänikestoa ja tietoja sen mukaisesti
                        if uusnuotti[6]:
                            nuotti = (nuotti[0], nuotti[1], nuotti[2], nuotti[3], nuotti[4] + uusnuotti[4],
                                      nuotti[5], True, nuotti[7])
                        aikakesto += lisäkesto

                    # Tai jos saman nuotin jatkomerkki, niin lisätään kestoa sen itsensä verran
                    elif seuraava(merkit, indeksi - 1) == JATKO[0]:
                        indeksi += 1
                        aikakesto += lisäkesto

                    # Tai stackato, lisätään stackaton verran pituutta nuotille
                    else:
                        indeksi += 1
                        nuotti = (nuotti[0], nuotti[1], nuotti[2], nuotti[3],
                                  nuotti[4] + min(1 / 8, nuotti[4] / 8), nuotti[5], True)

                # Jos jäätiin jatkomerkin kohdalle, niin korjataan
                if seuraava(merkit, indeksi - 1) == JATKO[1]:
                    indeksi += 1

                # Jos alkuperäinen merkki on nuoteissa, niin lisätään midiin nuotti
                if merkki.lower() in nuotit:
                    output.nuotti(nuotti[0], nuotti[1], nuotti[2], nuotti[3],
                                 nuotti[4] if nuotti[6] else aikakesto, nuotti[5])

                # Jos ei olla soinnussa, niin lisätään aikaa
                if aikalisä:
                    aika += aikakesto

                # Jos taas ollaan, niin pidetään kirjaa maksimipituudesta kyseisessä soinnussa
                else:
                    maxkesto = max(aikakesto, maxkesto)

            # Jos merkki onkin kontrollimerkki
            elif merkki.lower() in KONTROLLI:
                # Oktaavi alas
                if merkki == KONTROLLI[0]:
                    oktaavi = max(oktaavi - 1, 1)

                # Oktaavi ylös
                elif merkki == KONTROLLI[1]:
                    oktaavi = min(oktaavi + 1, 10)

                # Oktaavinvaihto
                elif merkki.lower() == KONTROLLI[2]:
                    indeksi, oktaavi = lue_luku(merkit, indeksi + 1)
                    if not 0 <= oktaavi <= 9:
                        raise ValueError("Oktaavin oltava kokonaisluku väliltä 0...9,\
                                          kohdassa {}.".format(indeksi), indeksi)

                # Tempomuutos
                elif merkki.lower() == KONTROLLI[3]:
                    indeksi, tempo = lue_luku(merkit, indeksi + 1)
                    output.tempo(raita, aika, tempo)
                    if not tempo > 0:
                        raise ValueError("Tempon on oltava positiivinen, kohdassa {}.".format(indeksi),
                                         indeksi)

                # Oletuskeston muutos
                elif merkki.lower() == KONTROLLI[4]:
                    indeksi, oletuskesto = Soitin.__lue_float(merkit, indeksi + 1)
                    oletuskesto = 4 / oletuskesto
                    if not oletuskesto > 0:
                        raise ValueError("Keston on oltava positiivinen, kohdassa {}.".format(indeksi),
                                         indeksi)

                # Äänenvoimakkuuden muutos
                elif merkki.lower() == KONTROLLI[5]:
                    indeksi, volume = lue_luku(merkit, indeksi + 1)
                    if not 0 <= volume <= 127:
                        raise ValueError("Äänenvoimakkuuden on oltava välillä 0...127, kohdassa {}.".format(indeksi),
                                         indeksi)

                # Raidanvaihtomerkki. Lisätään raidan numeroa ja resetoidaan nuottien alkutiedot
                elif merkki == KONTROLLI[6]:
                    raita += 1
                    maxaika = max(aika, maxaika)
                    aika = alkuaika
                    kanava = 0
                    oktaavi = 5
                    oletuskesto = 1
                    volume = 100
                    modulaatio = 0

                # Jos soinnun aloittava sulku
                elif merkki == KONTROLLI[7]:
                    aikalisä = False
                    # Etsitään seuraava sulku kiinni merkki
                    i = indeksi + 1
                    while i < len(merkit) and merkit[i] != KONTROLLI[8]:
                        i += 1

                    stacmod = -1
                    lenmod = 0

                    # Jos se yleensäkään löytyi, niin luetaan jatkomerkkejä ja etsitään, kuinka pitkään soinnun
                    # nuotteja pitää jatkaa ja missä kohdassa on mahdollinen staccato
                    if seuraava(merkit, i - 1) == KONTROLLI[8]:
                        j = i + 1
                        while j < len(merkit) and (merkit[j] == STACCATO or merkit[j] == JATKO[0]):
                            if merkit[j] == STACCATO and stacmod == -1:
                                stacmod = j - i - 1
                            else:
                                lenmod += 1
                            j += 1

                        modmerkit = j - i

                    maxkesto = 0

                # Soinnun lopettava sulku
                elif merkki == KONTROLLI[8]:
                    aikalisä = True
                    aika += maxkesto
                    indeksi += modmerkit - 1

                # Soitinnumeron aloittava sulku
                elif merkki == KONTROLLI[9]:
                    indeksi, soitin = lue_luku(merkit, indeksi + 1)

                    # Tarkastellaan soittimen oikeellisuus
                    if not 1 <= soitin <= 129:
                        raise ValueError("Soittimen on oltava välillä 1...129, kohdassa {}.".format(indeksi), indeksi)

                    # Sekä seuraavan merkin oikeellisuus
                    if not seuraava(merkit, indeksi) == KONTROLLI[10]:
                        raise ValueError("Soittimen oltava pelkkä numero, kohdassa {}.".format(indeksi), indeksi)

                    indeksi += 1

                    # Jos soitin on ekstrasoitin 129, niin vaihdetaan rumpukanavalle
                    if soitin == 129:
                        kanava = 9

                    # Jos normaali soitin, niin jos kyseistä soitinta on käytetty ennenkin, vaihdetaan
                    # sille varatulle kanavalla
                    elif soitin in soittimet:
                        kanava = soittimet[soitin]

                    # jos sitä ei ole käytetty ennen, niin luodaan uusi soitin, mikäli sille on tilaa.
                    elif len(soittimet) < MAXSOITTIMET:
                        kanava = len(soittimet)

                        # Tällä estetään soittimen meno kanavalle 10, joka on perkussiokanava
                        if kanava > 8:
                            kanava += 1

                        soittimet[soitin] = kanava

                        output.soitin(raita, kanava, 0, soitin - 1)
                    else:
                        raise ValueError("Liian monta soitinta, sori, " + str(MAXSOITTIMET)
                                         + " on maksimi :(", indeksi)

                # Modulaatiomerkki
                elif merkki == KONTROLLI[11]:
                    # Jos plus- tai miinusmerkki, niin lisätään tai vähennetään numeron verran
                    if seuraava(merkit, indeksi) in "+":
                        indeksi, moduloi = lue_luku(merkit, indeksi + 2)
                        modulaatio += moduloi
                    elif seuraava(merkit, indeksi) == "-":
                        indeksi, moduloi = lue_luku(merkit, indeksi + 2)
                        modulaatio -= moduloi

                    # Muutoin luetaan modulaationumero
                    else:
                        indeksi, modulaatio = lue_luku(merkit, indeksi + 1)

                indeksi += 1

            else:
                raise ValueError("Syntaksivirhe kohdassa {}.".format(indeksi), indeksi)

        # Palautetaan midiobjekti, ja raitojen maksimipituus
        return max(maxaika, aika)

    # Funktio, joka käsittelee soitettavat merkkijonot, sekä formaatit
    @staticmethod
    def do(merkit, inputclass, outputclass, filename=None):
        # Muunnetaan sisäiseen formaattiin
        try:
            oikeat_merkit = inputclass().muunna(merkit)
        except ValueError as e:
            indeksi = e.args[1]
            print(e.args[0], "\n", merkit[max(0, indeksi - 8):min(indeksi + 8, len(merkit))], sep="")

            raise e

        # Luetaan sisäistä formaattia, ja kirjoitetaan outputtiin
        try:
            # Jos luettavana on vain yksi merkkijono, luodaan siitä midi ilman kommervenkkejä
            if isinstance(oikeat_merkit, str):
                maxraidat = oikeat_merkit.count(KONTROLLI[6]) + 1
                output = outputclass(maxraidat, filename)
                Soitin.__luo_nuotit(oikeat_merkit, output)

            # Jos taas luettavana on lista tai tuple, niin soitetaan ensin ensimmäinen, ja sitten
            # lisätään samaan midiobjektiin nuotteja
            elif isinstance(oikeat_merkit, list) or isinstance(oikeat_merkit, tuple):
                # maxraidat-parametriin lasketaan pilkkujen määrä (+1) siitä raidasta, jossa niitä on eniten
                maxraidat = max(oikeat_merkit, key=lambda m: m.count(KONTROLLI[6]) + 1).count(KONTROLLI[6]) + 1
                output = outputclass(maxraidat, filename)
                aika = Soitin.__luo_nuotit(oikeat_merkit[0], output)

                for jono in oikeat_merkit[1:]:
                    aika = Soitin.__luo_nuotit(jono, output, aika)
            else:
                raise AttributeError("Soitettavat merkit eivät ole merkkijono tai kokoelma niitä")

            output.kirjoita()

        # Jos tuli ValueError, niin printtaillaan siitä ympäriltä merkkejä, jotta lukija näkee
        # vähän että missä kohdassa virhe on.
        except ValueError as e:
            indeksi = e.args[1]
            print(e.args[0], "\n", oikeat_merkit[max(0, indeksi - 8):min(indeksi + 8, len(oikeat_merkit))], sep="")


def soita_ei_block(merkit, inputclass, outputclass):
    module = inspect.getmodule(inspect.stack()[-1][0])
    if module is not None and module.__name__ == "__main__":
        process = multiprocessing.Process(target=Soitin.do, args=[merkit, inputclass, outputclass])
        process.start()
