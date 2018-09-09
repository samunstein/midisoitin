from soitin.output_rajapinnat.OutputRajapinta import OutputRajapinta

from midiutil.MidiFile3 import MIDIFile


class MidiPlay(OutputRajapinta):
    def __init__(self, max_tracks, filename):
        self.midi = MIDIFile(max_tracks)

    def nuotti(self, track, channel, pitch, time, duration, volume):
        self.midi.addNote(track, channel, pitch, time, duration, volume)

    def tempo(self, track, time, tempo):
        self.midi.addTempo(track, time, tempo)

    def soitin(self, track, channel, time, program):
        self.midi.addProgramChange(track, channel, time, program)

    def kirjoita(self, file=None):
        import sys
        import io

        # Systeemialustan mukainen miditiedoston soittamiseen käytetty tiedosto
        if sys.platform == "win32":
            from mplaymaster.win32midi import midiDevice
        elif sys.platform == "darwin":
            from mplaymaster.darwinmidi import midiDevice
        else:
            raise ImportError("Sori, soitto ei tue muuta kuin Windowsia ja Mac OS X:ää :(")

        # Haetaan soittolaite tiedoston alussa importatusta kirjastosta
        laite = midiDevice()

        # Luodaan BytesIO-objekti, joka toimii kuin bytes-tilassa avattu tiedosto
        tiedosto = file if file is not None else io.BytesIO()
        self.midi.writeFile(tiedosto)
        tiedosto.seek(0)

        # Ja kutsutaan laitteen soittofunktiota omassa säikeessään. Tämä tehdään siksi, että
        # ohjelma pääsee jatkamaan suoritustaan musiikin soidessa taustalla.
        laite.play(tiedosto)


class MidiWrite(OutputRajapinta):
    def __init__(self, max_tracks, filename):
        self.filename = filename
        self.midi = MIDIFile(max_tracks)

    def nuotti(self, track, channel, pitch, time, duration, volume):
        self.midi.addNote(track, channel, pitch, time, duration, volume)

    def tempo(self, track, time, tempo):
        self.midi.addTempo(track, time, tempo)

    def soitin(self, track, channel, time, program):
        self.midi.addProgramChange(track, channel, time, program)

    def kirjoita(self):
        file = open(self.filename, "wb")
        self.midi.writeFile(file)
        file.close()
