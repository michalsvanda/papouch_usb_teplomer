# Vyčítání USB teploměru Papouch TMU

Jednoduchý skript v Pythonu, který vyčte aktuální teplotu z USB teploměru
[Papouch TMU](https://www.papouch.com/). Teploměr se v systému hlásí jako
virtuální sériový port (převodník FTDI, VID `0403`, PID `6001`), takže stačí
knihovna [pySerial](https://pyserial.readthedocs.io/).

Konkrétní teploměr se vybírá podle sériového čísla USB převodníku, takže
skript funguje i při více připojených teploměrech a nezávisí na tom, jaké
číslo portu (`COMx`, `/dev/ttyUSBx`) systém zařízení přidělí.

## Komunikační protokol

Zdroj: katalogový list TMU, kapitola *Komunikační protokol* (str. 20):
<https://cdn.papouch.com/data/user-content/old_eshop/files/TMU_C_1/tmu.pdf>

Níže je shrnutí protokolu; závazné znění je v odkazované dokumentaci.

Teploměr je jednosměrný – nepřijímá žádné příkazy a sám přibližně každých
10 sekund odešle změřenou teplotu. Formát zprávy je kompatibilní
s protokolem Spinel (formát 65, „B“).

Parametry sériové linky:

| Parametr      | Hodnota   |
|---------------|-----------|
| Rychlost      | 9600 Bd   |
| Datové bity   | 8         |
| Parita        | žádná     |
| Stop bity     | 1         |

Příklad zprávy (odesílá se bez mezer):

```
*B1E1+021.8<CR>
```

| Pole               | Délka  | Obsah                                                        |
|--------------------|--------|--------------------------------------------------------------|
| Prefix             | 1 B    | `*`                                                          |
| Formát             | 1 B    | `B`                                                          |
| Adresa             | 1 B    | `1`                                                          |
| Kód instrukce      | 2 B    | `E1`                                                         |
| Teplota            | 6 B    | ASCII se znaménkem, `-055.0` až `+125.0`; při poruše čidla `Err` |
| Zakončovací znak   | 1 B    | CR (`0x0D`)                                                  |

**Pozor:** zpráva končí znakem CR (`\r`), nikoliv LF (`\n`). Metoda
`readline()` z pySerialu proto není vhodná – čekala by na `\n`, skončila by
až timeoutem a vracela by náhodně rozříznuté zprávy. Skript místo toho používá
`read_until(b'\r')`, první (možná neúplnou) zprávu po otevření portu zahodí
a formát ověřuje regulárním výrazem.

## Instalace

```bash
git clone <URL tohoto repozitáře>
cd <adresář repozitáře>
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Na Linuxu musí mít uživatel přístup k sériovým portům, typicky členstvím
ve skupině `dialout`:

```bash
sudo usermod -aG dialout $USER   # poté se odhlásit a znovu přihlásit
```

Ovladače FTDI jsou v moderních Linuxech i Windows obvykle součástí systému.

## Zjištění sériového čísla teploměru

```bash
python -m serial.tools.list_ports -v
```

U teploměru TMU uvidíte řádek podobný tomuto:

```
/dev/ttyUSB0
    desc: TMU
    hwid: USB VID:PID=0403:6001 SER=PP69K2U2 LOCATION=1-1.2
```

Hodnotu za `SER=` nastavte v konstantě `SERIAL_NO` ve skriptu.

## Použití

Spuštění z příkazové řádky – vypíše teplotu ve °C:

```bash
$ python read_usb_papouch.py
21.8
```

Použití jako modul z jiného programu:

```python
from read_usb_papouch import read_tmu

try:
    t = read_tmu('PP69K2U2')
    print(f'Teplota: {t:.1f} °C')
except RuntimeError as e:
    print(f'Chyba čtení: {e}')
```

Funkce `read_tmu()` vyhodí `RuntimeError`, pokud:

- teploměr s daným sériovým číslem není připojen,
- teploměr hlásí `Err` (vadné čidlo nebo přívodní kabel),
- během několika pokusů nepřijde platná zpráva.

Protože teploměr vysílá jen jednou za ~10 s, trvá jedno čtení obvykle
až 10 s (výjimečně ~20 s). Pokud potřebujete teplotu často, je vhodnější
nechat port otevřený v dlouho běžícím procesu a průběžně ukládat poslední
hodnotu.

## Licence

Projekt je šířen pod licencí MIT – viz soubor [LICENSE](LICENSE).
