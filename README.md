# BB84-szimulátor

BB84 kvantumkulcsszétosztó szimulátor Pythonban.
A cél egy léptethető, böngészős felület és egy Windowson önállóan
indítható alkalmazás.

## Követelmények

Python 3.10 vagy újabb.

## Az első művelet

A `bb84.py` fájl `meres(allapot, meresi_bazis)` függvénye egy bitet ad vissza.
Az állapot `(bázis, bit)` tuple, például `("Z", 1)`.

- Egyező bázisnál az eredeti bit az eredmény.
- Eltérő bázisnál a két lehetséges bit közül egyenlő eséllyel választ.
- A függvény nem módosítja az eredeti állapotot.

```python
from bb84 import meres

print(meres(("Z", 1), "Z")) #1 biztosan
print(meres(("Z", 1), "X")) #0 vagy 1
```

Ez ideális modell a négy BB84-állapotra. A függvény érvényes
bemeneteket feltételez: a bázis `"Z"` vagy `"X"`, a bit `0` vagy `1`.
A bemenetellenőrzés későbbi lépés.

## Ellenőrzés

```powershell
py -m unittest discover -s tests -v
```

A tesztek az összes egyező bázisú esetet, az eltérő bázisú mérés mindkét
lehetséges kimenetét és az eredeti állapot megőrzését vizsgálják.
A véletlen választást a tesztekben vezéreljük, ezért nem esetleges a teszteredmény.