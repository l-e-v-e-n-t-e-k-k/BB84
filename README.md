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

Aktív virtuális környezetben telepítsd a függőségeket a
`python -m pip install -r requirements.txt` paranccsal, majd futtasd a
`python launcher.py` parancsot. Az indító megnyitja a böngészőt a helyi címen.
Alapból a 8765-ös portot használja. Ha ez foglalt, szabad portra vált.
A pontos címet kiírja a konzolra. A **Program leállítása** gomb a böngészőben
megerősítést kér, majd bezárja a szervert. A böngészőlap külön bezárható.
Fejlesztéshez a `python app.py` paranccsal közvetlenül is indítható a szerver.
A terminálban mindkét indítási módnál a Ctrl+C állítja le.
A felület és a betűkészletek helyiek; a telepítés után internet nélkül is működik.
A fázisnapló korábbi nézetei nem számolnak újra. A szerver leállításakor a futások elvesznek.

## Windows-kiadás újraépítése

A kész mappás kiadást a teljes `dist/BB84` mappával vagy a
`dist/BB84-windows-x64.zip` kibontásával lehet átvinni másik gépre.
A kibontott `BB84/BB84.exe` indításához a Python és a csomagjai már a
kiadásban vannak. A jelenlegi kiadás 64 bites (x64) Windowshoz készült.

A `BB84/_internal` könyvtár `.pyd` fájljait is tovább kell adni és a Gitben
rögzíteni. Az `_socket.pyd` kihagyása `No module named '_socket'` hibát okoz.
A `.gitignore` a `dist` alatt engedélyezi ezeket a natív modulokat.

A kiadás újraépítéséhez 64 bites Windowson Python 3.12.10 (x64) környezetet használunk. A
`requirements-build.txt` rögzíti a PyInstaller 6.22.3 verzióját, valamint a
csomagoláshoz és a futtatáshoz szükséges közvetett függőségek verzióit.
A projekt mappájában hozd létre a virtuális környezetet, ha még nincs `.venv`,
majd telepítsd a rögzített csomagokat.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements-build.txt
.\.venv\Scripts\python.exe -m pip check
```

Először a mappás, konzolos változatot készítsd el. Az indító a
`dist\BB84\BB84.exe`. A futtatáshoz tartsd meg mellette a csomag többi fájlját.

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --onedir --console --noupx --name BB84 --add-data "templates:templates" --add-data "static:static" launcher.py
```

Ha a mappás változatban működik a felület, a léptetés és a leállítás, az
egyfájlos változatot az alábbi paranccsal készítheted el. A kimenet a `dist\BB84.exe`.

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --onefile --console --noupx --name BB84 --add-data "templates:templates" --add-data "static:static" launcher.py
```

Az egyfájlos build helyi futási próbáját a Microsoft Defender karanténja
szakította meg. A böngészőnyitást, a szimulációt és a leállítást a mappás
kiadáson sikerült végigellenőrizni.

## Tesztek

```powershell
py -m unittest discover -s tests -v
```

A tesztek az összes egyező bázisú esetet, az eltérő bázisú mérés mindkét
lehetséges kimenetét és az eredeti állapot megőrzését vizsgálják.
A véletlen választást a tesztekben vezéreljük, ezért nem esetleges a teszteredmény.
