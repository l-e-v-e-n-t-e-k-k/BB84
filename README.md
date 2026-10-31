# BB84-szimulátor

Oktatási célú BB84 kvantumkulcsszétosztó szimulátor Pythonban.
A cél egy léptethető, böngészős felület és egy Windowson önállóan
indítható alkalmazás. Jelenleg az első elemi mérési függvény készült el.

## Követelmények

Python 3.10 vagy újabb. Külső Python-csomag egyelőre nem szükséges.

## Az első művelet

A `bb84.py` fájl `meres(allapot, meresi_bazis)` függvénye egy bitet ad vissza.
Az állapot `(bázis, bit)` tuple, például `("Z", 1)`.

- Egyező bázisnál az eredeti bit az eredmény.
- Eltérő bázisnál a két lehetséges bit közül egyenlő eséllyel választ.
- A függvény nem módosítja az eredeti állapotot.

```python
from bb84 import meres

print(meres(("Z", 1), "Z"))  # Biztosan 1.
print(meres(("Z", 1), "X"))  # 0 vagy 1.
```

Ez ideális, zajmentes modell a négy BB84-állapotra. A függvény érvényes
bemeneteket feltételez: a bázis `"Z"` vagy `"X"`, a bit `0` vagy `1`.
A bemenetellenőrzés későbbi fejlesztési lépés. A típusjelölések dokumentálják
a várt típusokat, de önmagukban nem ellenőrzik az értékeket futás közben.
A `random` modul oktatási szimulációra szolgál, nem valódi titkos kulcsokhoz.

## Ellenőrzés

A projekt mappájából, Windows alatt:

```powershell
py -m unittest discover -s tests -v
```

Ha a Python más paranccsal érhető el, a `py` helyére annak elérési útja kerül.
A tesztek az összes egyező bázisú esetet, az eltérő bázisú mérés mindkét
lehetséges kimenetét és az eredeti állapot megőrzését vizsgálják.
A véletlen választást a tesztekben vezéreljük, ezért nem esetleges a teszteredmény.

## Következő lépés

A mérési függvény felhasználásával több pozícióból álló, Eve nélküli
futás elkészítése az elfogadott lista → szótár → tuple adatmodellel.
