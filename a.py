from soitin.soitin import Soitin
import soitin.input_rajapinnat as inp
import soitin.output_rajapinnat as out

a = "t135l8>c2<b>cd2cde4 cefg4__f<a>df<a>de<g>ce<g>cd<eb>d<eb>e4<e>dc<b>c2<b>cd2cde4 cefg4__f2<a>de2d<ba  >ed<ba"
b = "l8 <ea>cea <gb>dgb <ceg>ce <g>cegb+ <af2 ag2 gb2e4__l4>> (a<ce)  (<gb>d)  (<ceg) (egb+)  (fab+)  (egb)  (eab+)  "

Soitin.do(a + "," + b, inp.Default, out.GW2, "ahk.ahk")
