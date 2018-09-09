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
