import inspect
import io
import multiprocessing
import sys
from Randomjuttuja.midisoitin.gw2interface import MidiInterface

# Miditiedoston luomiseen käytetty kirjasto
from Randomjuttuja.midisoitin.midiutil.MidiFile3 import MIDIFile

# Systeemialustan mukainen miditiedoston soittamiseen käytetty tiedosto
if sys.platform == "win32":
    from Randomjuttuja.midisoitin.mplaymaster.win32midi import midiDevice
elif sys.platform == "darwin":
    from Randomjuttuja.midisoitin import midiDevice
else:
    #raise ImportError("Sori, soitto ei tue (vielä) muuta kuin Windowsia ja Mac OS X:ää :(")
    from Randomjuttuja.midisoitin import midiDevice


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
    # Määritellään käytettävät merkit. Näitä voi tästä muuttaa, mutta en ihmettelisi, jos
    # joku paikka vahingossa nojaa literaaliin, eikä tästä löytyviin vakioihin
    NUOTIT = "cdefgab"
    YLENNYKSET = "#+-"
    KONTROLLI = "<>otlv,()[]m"
    STACCATO = "."
    TAUKO = " r"
    JATKO = "_&"
    VIRHE = "?"

    # Eri nuottien korkeudet dictiin
    NUOTISTO = dict(zip([c for c in NUOTIT], [0, 2, 4, 5, 7, 9, 11]))

    # Midi-formaatti asettaa rajoituksen eri kanavien määrälle.
    MAXSOITTIMET = 15

    # Muuntofunktio, jolla saa muunnettua kappaleita muutamasta eri formaatista
    # sellaiseksi, jota tämä soitin osaa soittaa.
    @staticmethod
    def muunna(mistä, teksti):
        try:
            ma = ["mabinogi", "mab", "ma"]
            o1 = ["o1", "aalto"]
            aa = ["aa", "archeage"]

            # Archeage MML
            if mistä.lower() in aa:

                # Perus replacet alkuun.
                teksti = teksti.replace("c", Soitin.NUOTIT[0])\
                               .replace("d", Soitin.NUOTIT[1])\
                               .replace("e", Soitin.NUOTIT[2])\
                               .replace("f", Soitin.NUOTIT[3])\
                               .replace("g", Soitin.NUOTIT[4])\
                               .replace("a", Soitin.NUOTIT[5])\
                               .replace("b", Soitin.NUOTIT[6])\
                               .replace("<", Soitin.KONTROLLI[0])\
                               .replace(">", Soitin.KONTROLLI[1])\
                               .replace("o", Soitin.KONTROLLI[2])\
                               .replace("t", Soitin.KONTROLLI[3])\
                               .replace("l", Soitin.KONTROLLI[4])\
                               .replace("v", Soitin.KONTROLLI[5])\
                               .replace(",", Soitin.KONTROLLI[6])\
                               .replace("r", Soitin.TAUKO[1])\
                               .replace("&", Soitin.JATKO[1])\
                               .replace("+", Soitin.YLENNYKSET[1])\
                               .replace("#", Soitin.YLENNYKSET[1])\
                               .replace("-", Soitin.YLENNYKSET[2])
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
                        indeksi, l = Soitin.__lue_luku(teksti, indeksi + 1)
                        if Soitin.__seuraava(teksti, indeksi) == ".":
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
                        if nuotti in Soitin.YLENNYKSET:
                            nuotti = teksti[alku - 2:alku]

                        # Lisätään tarpeeksi tarkka desimaaliluku nuotin pituudesta
                        uusteksti.append("&{}{:.6f}".format(nuotti, pituus * 2))

                    # Ilman erikoisuuksia lisätään merkki sellaisenaan
                    else:
                        uusteksti.append(merkki)

                    indeksi += 1

            # O1-formaatti tarkoittaa Aalto-yliopiston Ohjelmointi 1 -kurssin formaattia
            # O1 formaatti on jonkin verran riisutumpi kuin tämän soittimen, joten pärjätään
            # melkein vain muuttamalla merkit toisiksi
            elif mistä.lower() in o1:
                i = 0
                teksti = teksti.replace("#", Soitin.YLENNYKSET[1])\
                               .replace("-", Soitin.JATKO[0])\
                               .replace("b", Soitin.YLENNYKSET[2])\
                               .replace("h", Soitin.NUOTIT[-1])\
                               .replace("H", Soitin.NUOTIT[-1].upper())\
                               .replace("&", Soitin.KONTROLLI[6])
                uusteksti = list()

                # Alkuun pitää laitta nuotit puolipituisiksi, koska O1-kurssin soitin tekee näin
                uusteksti.append("l8")
                oktaavi = 5
                while i < len(teksti):
                    # Jos O1-kurssilla nuotin perässä on numero, se kertoo nuotin oktaavin. Meillä
                    # tämä ei käy päinsä, joten kyseinen numero korvataan oktaavivaihdoksilla sen ympärillä
                    if teksti[i].lower() in Soitin.NUOTIT and Soitin.__seuraava(teksti, i).isdigit():
                        okt = int(teksti[i + 1])
                        uusteksti.append("{}{}{}{}{}".format(Soitin.KONTROLLI[2], okt,
                                                             teksti[i], Soitin.KONTROLLI[2], oktaavi))
                        i += 1

                    # Pidetään oktaavia muistissa
                    else:
                        if teksti[i] in Soitin.KONTROLLI[:2]:
                            if teksti[i] == Soitin.KONTROLLI[1]:
                                oktaavi += 1
                            else:
                                oktaavi -= 1

                        uusteksti.append(teksti[i])
                    i += 1

            # Mabinogi-formaatti on hyvin samanlainen kuin Archeage-formaatti, mutta mabinogissa
            # tekstistä löytyy n-kirjaimia, jotka lisäävät nuotin miltä vain korkeudelta välittämättä
            # nykyisestä oktaavista.
            elif mistä.lower() in ma:

                # Ensin muunnetaan teksti Archeage-formaatilla.
                teksti = Soitin.muunna("aa", teksti)
                uusteksti = list()
                indeksi = 0
                o = 5
                while indeksi < len(teksti):
                    merkki = teksti[indeksi]

                    # Muunnellaan n:t oktaavivaihdoksiksi ja oikeaksi nuotiksi
                    if merkki.lower() == "n":
                        indeksi, n = Soitin.__lue_luku(teksti, indeksi + 1)
                        # Nuotin korkeus oktaavissa
                        num = n % 12
                        nuotteksti = ""
                        # Etsitään oikea nuottimerkki
                        for nuotti in sorted(Soitin.NUOTISTO, key=lambda x: Soitin.NUOTISTO[x]):
                            # Jos löytyi niin asetetaan nuotin tekstiksi vastaava kirjain ja tarvittaessa alennus,
                            # jos nuotti ei osu suoraan valkoisen painikkeen kohdalle.
                            if nuotteksti == "" and Soitin.NUOTISTO[nuotti] >= num:
                                nuotteksti = nuotti + (Soitin.NUOTISTO[nuotti] - num) * Soitin.YLENNYKSET[2]

                        uusteksti.append("{}{}{}{}{}".format(Soitin.KONTROLLI[2], n // 12, nuotteksti,
                                                             Soitin.KONTROLLI[2], o))

                    # Koska Mabinogi soittaa musiikkia paljon kovemmalla kuin mikään muu, sen volume-arvoja
                    # pitää korottaa (kerrotaan seitsemällä), jotta musiikista kuuluisi mitään.
                    elif merkki.lower() == "v":
                        indeksi, v = Soitin.__lue_luku(teksti, indeksi + 1)
                        uusteksti.append(Soitin.KONTROLLI[5] + str(min(127, v * 7)))

                    # Ja pidetään oktaavia muistissa.
                    else:
                        if merkki.lower() == "o":
                            _, o = Soitin.__lue_luku(teksti, indeksi + 1)

                        uusteksti.append(merkki)

                    indeksi += 1

            else:
                raise AttributeError("Lähdeformaattia ei tunneta.")

            # Yhdistetään listan alkiot ja palautetaan merkkijono
            return "".join(uusteksti)

        except ValueError as e:
            indeksi = e.args[1]
            print(e.args[0], "\n", teksti[max(0, indeksi - 8):min(indeksi + 8, len(teksti))], sep="")

            raise e

    # Palauttaa seuraavan merkin, paitsi jos ollaan lopussa, jolloin palautuu virhemerkki
    @staticmethod
    def __seuraava(merkit, indeksi):
        if indeksi + 1 < len(merkit):
            return merkit[indeksi + 1]
        else:
            return Soitin.VIRHE

    # Lukee kokonaisluvun annetusta kohdasta, ja palauttaa indeksin viimeiseen
    # merkkiin kokonaisluvussa.
    @staticmethod
    def __lue_luku(merkit, alku):
        loppu = alku
        while loppu < len(merkit) and merkit[loppu].isdigit():
            loppu += 1

        if loppu > alku:
            return loppu - 1, int(merkit[alku:loppu])
        else:
            raise ValueError("Virheellinen kokonaisluku kohdassa {}.".format(alku), alku)

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
    def __luo_midi(merkit, alkumidi=None, alkuaika=0, maxraidat=None):

        # Lue_nuotti-funktio, lukee nuotin annetusta kohdasta
        def lue_nuotti(merket, indekse):
            # Katsotaan, onko ylennys- tai alennusmerkkiä.
            if Soitin.__seuraava(merket, indekse) in Soitin.YLENNYKSET:
                if Soitin.__seuraava(merket, indekse) == Soitin.YLENNYKSET[2]:
                    ylennys = -1
                else:
                    ylennys = 1

                indekse += 1
            else:
                ylennys = 0

            # Jos perässä on keston ilmaiseva numero, luetaan se kestoksi, muuten oletuskesto
            if Soitin.__seuraava(merket, indekse).isdigit():
                indekse, kestoaika = Soitin.__lue_float(merket, indekse + 1)
                kestoaika = 4 / kestoaika
            else:
                kestoaika = oletuskesto

            # Jos nuotti on staccato, niin annetaan sille lyhyt äänikesto, muuten
            # äänikesto on nuotin koko kestoaika
            if Soitin.__seuraava(merket, indekse) == Soitin.STACCATO:
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
            elif merkki in Soitin.TAUKO:
                nuotte = (raita, kanava, 60, aika, kestoaika, volume, stackato, ylennys)

            else:
                raise ValueError("Ei nuottia, kohdassa {}.".format(indekse))

            # Palautetaan seuraavan merkin indeksi, ja nuotin aikakesto
            return indekse, kestoaika, nuotte

        # Tästä alkaa funktion luo_midi suoritus
        # Alkuvalmistelut
        nuotit = Soitin.NUOTISTO

        # Jos miditiedosto annetaan valmiina, niin sitä käytetään
        if alkumidi is None:
            # Jos ei, niin luodaan uusi, jossa on parametrin mukaisesti raitoja, tai
            # jos parametria ei ole, lasketaan itse raitojen määrä raidanvaihtomerkkien määrästä
            if maxraidat is None:
                midi = MIDIFile(merkit.count(Soitin.KONTROLLI[6]) + 1)
            else:
                midi = MIDIFile(maxraidat)
        else:
            midi = alkumidi

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
            midi.addTempo(raita, aika, tempo)

        # Lähdetään lukemaan
        indeksi = 0
        while indeksi < len(merkit):

            merkki = merkit[indeksi]

            # Jos nuotti taikka tauko...
            if merkki.lower() in nuotit or merkki in Soitin.TAUKO:
                indeksi, aikakesto, nuotti = lue_nuotti(merkit, indeksi)

                lisäkesto = aikakesto

                indeksi += 1

                # Jos on nuotin jatkamismerkki JA seuraana nuotti on ylennyksineen samankorkuinen
                # kuin edellinen, TAI kyseessä on saman nuotin jatkamismerkki, TAI staccato-merkki,
                # niin muutetaan nuotin tietoja jatkomerkkien mukaisella tavalla
                while (Soitin.__seuraava(merkit, indeksi - 1) == Soitin.JATKO[1] and
                       Soitin.__seuraava(merkit, indeksi).lower() == merkki.lower() and
                       (Soitin.__seuraava(merkit, indeksi + 1) == nuotti[7] or
                       Soitin.__seuraava(merkit, indeksi + 1) not in Soitin.YLENNYKSET and
                       nuotti[7] == 0)) or \
                      (Soitin.__seuraava(merkit, indeksi - 1) == Soitin.JATKO[0]) or\
                        Soitin.__seuraava(merkit, indeksi - 1) == Soitin.STACCATO:

                    # Jos nuotin jatkomerkki, niin luetaan uusi nuotti, ja lisätään kestoa sen mukaan
                    if Soitin.__seuraava(merkit, indeksi - 1) == Soitin.JATKO[1]:
                        indeksi, lisäkesto, uusnuotti = lue_nuotti(merkit, indeksi + 1)
                        indeksi += 1
                        # Jos uusi nuotti on staccato, niin muutetaan nuotin äänikestoa ja tietoja sen mukaisesti
                        if uusnuotti[6]:
                            nuotti = (nuotti[0], nuotti[1], nuotti[2], nuotti[3], nuotti[4] + uusnuotti[4],
                                      nuotti[5], True, nuotti[7])
                        aikakesto += lisäkesto

                    # Tai jos saman nuotin jatkomerkki, niin lisätään kestoa sen itsensä verran
                    elif Soitin.__seuraava(merkit, indeksi - 1) == Soitin.JATKO[0]:
                        indeksi += 1
                        aikakesto += lisäkesto

                    # Tai stackato, lisätään stackaton verran pituutta nuotille
                    else:
                        indeksi += 1
                        nuotti = (nuotti[0], nuotti[1], nuotti[2], nuotti[3],
                                  nuotti[4] + min(1 / 8, nuotti[4] / 8), nuotti[5], True)

                # Jos jäätiin jatkomerkin kohdalle, niin korjataan
                if Soitin.__seuraava(merkit, indeksi - 1) == Soitin.JATKO[1]:
                    indeksi += 1

                # Jos alkuperäinen merkki on nuoteissa, niin lisätään midiin nuotti
                if merkki.lower() in nuotit:
                    midi.addNote(nuotti[0], nuotti[1], nuotti[2], nuotti[3],
                                 nuotti[4] if nuotti[6] else aikakesto, nuotti[5])

                # Jos ei olla soinnussa, niin lisätään aikaa
                if aikalisä:
                    aika += aikakesto

                # Jos taas ollaan, niin pidetään kirjaa maksimipituudesta kyseisessä soinnussa
                else:
                    maxkesto = max(aikakesto, maxkesto)

            # Jos merkki onkin kontrollimerkki
            elif merkki.lower() in Soitin.KONTROLLI:
                # Oktaavi alas
                if merkki == Soitin.KONTROLLI[0]:
                    oktaavi = max(oktaavi - 1, 1)

                # Oktaavi ylös
                elif merkki == Soitin.KONTROLLI[1]:
                    oktaavi = min(oktaavi + 1, 10)

                # Oktaavinvaihto
                elif merkki.lower() == Soitin.KONTROLLI[2]:
                    indeksi, oktaavi = Soitin.__lue_luku(merkit, indeksi + 1)
                    if not 0 <= oktaavi <= 9:
                        raise ValueError("Oktaavin oltava kokonaisluku väliltä 0...9,\
                                          kohdassa {}.".format(indeksi), indeksi)

                # Tempomuutos
                elif merkki.lower() == Soitin.KONTROLLI[3]:
                    indeksi, tempo = Soitin.__lue_luku(merkit, indeksi + 1)
                    midi.addTempo(raita, aika, tempo)
                    if not tempo > 0:
                        raise ValueError("Tempon on oltava positiivinen, kohdassa {}.".format(indeksi),
                                         indeksi)

                # Oletuskeston muutos
                elif merkki.lower() == Soitin.KONTROLLI[4]:
                    indeksi, oletuskesto = Soitin.__lue_float(merkit, indeksi + 1)
                    oletuskesto = 4 / oletuskesto
                    if not oletuskesto > 0:
                        raise ValueError("Keston on oltava positiivinen, kohdassa {}.".format(indeksi),
                                         indeksi)

                # Äänenvoimakkuuden muutos
                elif merkki.lower() == Soitin.KONTROLLI[5]:
                    indeksi, volume = Soitin.__lue_luku(merkit, indeksi + 1)
                    if not 0 <= volume <= 127:
                        raise ValueError("Äänenvoimakkuuden on oltava välillä 0...127, kohdassa {}.".format(indeksi),
                                         indeksi)

                # Raidanvaihtomerkki. Lisätään raidan numeroa ja resetoidaan nuottien alkutiedot
                elif merkki == Soitin.KONTROLLI[6]:
                    raita += 1
                    maxaika = max(aika, maxaika)
                    aika = alkuaika
                    kanava = 0
                    oktaavi = 5
                    oletuskesto = 1
                    volume = 100
                    modulaatio = 0

                # Jos soinnun aloittava sulku
                elif merkki == Soitin.KONTROLLI[7]:
                    aikalisä = False
                    # Etsitään seuraava sulku kiinni merkki
                    i = indeksi + 1
                    while i < len(merkit) and merkit[i] != Soitin.KONTROLLI[8]:
                        i += 1

                    stacmod = -1
                    lenmod = 0

                    # Jos se yleensäkään löytyi, niin luetaan jatkomerkkejä ja etsitään, kuinka pitkään soinnun
                    # nuotteja pitää jatkaa ja missä kohdassa on mahdollinen staccato
                    if Soitin.__seuraava(merkit, i - 1) == Soitin.KONTROLLI[8]:
                        j = i + 1
                        while j < len(merkit) and (merkit[j] == Soitin.STACCATO or merkit[j] == Soitin.JATKO[0]):
                            if merkit[j] == Soitin.STACCATO and stacmod == -1:
                                stacmod = j - i - 1
                            else:
                                lenmod += 1
                            j += 1

                        modmerkit = j - i

                    maxkesto = 0

                # Soinnun lopettava sulku
                elif merkki == Soitin.KONTROLLI[8]:
                    aikalisä = True
                    aika += maxkesto
                    indeksi += modmerkit - 1

                # Soitinnumeron aloittava sulku
                elif merkki == Soitin.KONTROLLI[9]:
                    indeksi, soitin = Soitin.__lue_luku(merkit, indeksi + 1)

                    # Tarkastellaan soittimen oikeellisuus
                    if not 1 <= soitin <= 129:
                        raise ValueError("Soittimen on oltava välillä 1...129, kohdassa {}.".format(indeksi), indeksi)

                    # Sekä seuraavan merkin oikeellisuus
                    if not Soitin.__seuraava(merkit, indeksi) == Soitin.KONTROLLI[10]:
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
                    elif len(soittimet) < Soitin.MAXSOITTIMET:
                        kanava = len(soittimet)

                        # Tällä estetään soittimen meno kanavalle 10, joka on perkussiokanava
                        if kanava > 8:
                            kanava += 1

                        soittimet[soitin] = kanava

                        midi.addProgramChange(raita, kanava, 0, soitin - 1)
                    else:
                        raise ValueError("Liian monta soitinta, sori, " + str(Soitin.MAXSOITTIMET)
                                         + " on maksimi :(", indeksi)

                # Modulaatiomerkki
                elif merkki == Soitin.KONTROLLI[11]:
                    # Jos plus- tai miinusmerkki, niin lisätään tai vähennetään numeron verran
                    if Soitin.__seuraava(merkit, indeksi) in "+":
                        indeksi, moduloi = Soitin.__lue_luku(merkit, indeksi + 2)
                        modulaatio += moduloi
                    elif Soitin.__seuraava(merkit, indeksi) == "-":
                        indeksi, moduloi = Soitin.__lue_luku(merkit, indeksi + 2)
                        modulaatio -= moduloi

                    # Muutoin luetaan modulaationumero
                    else:
                        indeksi, modulaatio = Soitin.__lue_luku(merkit, indeksi + 1)

                indeksi += 1

            else:
                raise ValueError("Syntaksivirhe kohdassa {}.".format(indeksi), indeksi)

        # Palautetaan midiobjekti, ja raitojen maksimipituus
        return midi, max(maxaika, aika)

    # Funktio, joka käsittelee soitettavat merkkijonot ja itse tiedo-objektin luomisen, sekä
    # threadin luonnin itse musiikin soittamiseen.
    @staticmethod
    def soittele(merkit):
        try:
            # Haetaan soittolaite tiedoston alussa importatusta kirjastosta
            laite = midiDevice()

            # Jos soitettavana on vain yksi merkkijono, luodaan siitä midi ilman kommervenkkejä
            if isinstance(merkit, str):
                midi, aika = Soitin.__luo_midi(merkit)

            # Jos taas soitettavana on lista tai tuple, niin soitetaan ensin ensimmäinen, ja sitten
            # lisätään samaan midiobjektiin nuotteja
            elif isinstance(merkit, list) or isinstance(merkit, tuple):
                # maxraidat-parametriin lasketaan pilkkujen määrä (+1) siitä raidasta, jossa niitä on eniten
                midi, aika = Soitin.__luo_midi(merkit[0],
                                               maxraidat=max(merkit, key=
                                                             lambda m: m.count(Soitin.KONTROLLI[6]) + 1).
                                               count(Soitin.KONTROLLI[6]) + 1)  # PyCharmin tyylisäännöt...
                for jono in merkit[1:]:
                    midi, aika = Soitin.__luo_midi(jono, midi, aika)
            else:
                raise AttributeError("Soitettavat merkit eivät ole merkkijono tai kokoelma niitä")

            # Luodaan BytesIO-objekti, joka toimii kuin bytes-tilassa avattu tiedosto
            tiedosto = io.BytesIO()
            midi.writeFile(tiedosto)
            tiedosto.seek(0)

            # Ja kutsutaan laitteen soittofunktiota omassa säikeessään. Tämä tehdään siksi, että
            # ohjelma pääsee jatkamaan suoritustaan musiikin soidessa taustalla.
            laite.play(tiedosto)

        # Jos tuli ValueError, niin printtaillaan siitä ympäriltä merkkejä, jotta lukija näkee
        # vähän että missä kohdassa virhe on.
        except ValueError as e:
            indeksi = e.args[1]
            print(e.args[0], "\n", merkit[max(0, indeksi - 8):min(indeksi + 8, len(merkit))], sep="")

    @staticmethod
    # Tällä funktiolla voi muuntaa nuotiston erilaiseksi kuin oletus cdefgab
    def muunna_nuotisto(nuotit):
        Soitin.NUOTIT = nuotit
        Soitin.NUOTISTO = dict(zip([c for c in Soitin.NUOTIT], [0, 2, 4, 5, 7, 9, 11]))

    @staticmethod
    # Tällä funktiolla voit kirjoittaa autohotkey-skriptin GW2:een
    def kirjoita_gw2(merkit):
        try:
            # Haetaan soittolaite tiedoston alussa importatusta kirjastosta
            midiInterface = MidiInterface()

            # Jos soitettavana on vain yksi merkkijono, luodaan siitä midi ilman kommervenkkejä
            if isinstance(merkit, str):
                midi, aika = Soitin.__luo_midi(merkit, alkumidi=midiInterface)

            # Jos taas soitettavana on lista tai tuple, niin soitetaan ensin ensimmäinen, ja sitten
            # lisätään samaan midiobjektiin nuotteja
            elif isinstance(merkit, list) or isinstance(merkit, tuple):
                # maxraidat-parametriin lasketaan pilkkujen määrä (+1) siitä raidasta, jossa niitä on eniten
                midi, aika = Soitin.__luo_midi(merkit[0],
                                               alkumidi=midiInterface,
                                               maxraidat=max(merkit, key=
                                                             lambda m: m.count(Soitin.KONTROLLI[6]) + 1).
                                               count(Soitin.KONTROLLI[6]) + 1)  # PyCharmin tyylisäännöt...
                for jono in merkit[1:]:
                    midi, aika = Soitin.__luo_midi(jono, midi, aika)
            else:
                raise AttributeError("Soitettavat merkit eivät ole merkkijono tai kokoelma niitä")

            midiInterface.writeFile()

        # Jos tuli ValueError, niin printtaillaan siitä ympäriltä merkkejä, jotta lukija näkee
        # vähän että missä kohdassa virhe on.
        except ValueError as e:
            indeksi = e.args[1]
            print(e.args[0], "\n", merkit[max(0, indeksi - 8):min(indeksi + 8, len(merkit))], sep="")




def soita(merkit):
    module = inspect.getmodule(inspect.stack()[-1][0])
    if module is not None and module.__name__ == "__main__":
        process = multiprocessing.Process(target=soittele, args=[merkit])
        process.start()


def soittele(merkit):
    Soitin.soittele(merkit)


def muunna(mistä, merkit):
    return Soitin.muunna(mistä, merkit)