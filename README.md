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

py -c 'from bb84 import meres; print(meres(("Z", 1), "Z")); print(meres(("Z", 1), "X"))'

Ez ideális modell a négy BB84-állapotra. A függvény érvényes
bemeneteket feltételez: a bázis `"Z"` vagy `"X"`, a bit `0` vagy `1`.

## Többpozíciós futás

Az `elokeszites()` ellenőrzi a három bemeneti listát, és létrehozza a
pozíciókat. Üres listáknál, eltérő hosszúságnál vagy érvénytelen bit/bázis
esetén `ValueError` hibát jelez. Bob mérési eredménye kezdetben `None`.

A `bob_merese()` ugyanazokban a szótárakban tárolja el Bob eredményeit.
Nem ad vissza új listát; a már mért pozíciókat ismételt híváskor kihagyja.
Alice eredeti adatai és a szűréshez tartozó jelölések változatlanok maradnak.

Eve bekapcsolásához az `elokeszites()` negyedik paramétereként adjunk meg
egy bázislistát. Ekkor a sorrend: `eve_merese(poziciok)`, majd
`bob_merese(poziciok)`. A működés magyarázatai a függvényeknél találhatók.

## Böngészős indítás

Aktív virtuális környezetben: `python -m pip install -r requirements.txt`, majd
`python app.py`. Nyisd meg a `http://127.0.0.1:8765` címet. Leállítás: Ctrl+C.
A felület és a betűkészletek helyiek; a telepítés után internet nélkül is működik.
A fázisnapló korábbi nézetei nem számolnak újra. A szerver leállításakor a futások elvesznek.

## Tesztek

```powershell
py -m unittest discover -s tests -v
```

A tesztek az összes egyező bázisú esetet, az eltérő bázisú mérés mindkét
lehetséges kimenetét és az eredeti állapot megőrzését vizsgálják.
A véletlen választást a tesztekben vezéreljük, ezért nem esetleges a teszteredmény.
