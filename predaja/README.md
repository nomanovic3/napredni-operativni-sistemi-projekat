# SVEU16 sistemska virtualna mašina

**Prvo otvori POCNI_OVDJE.pdf:** nacrtani vodič na 6 stranica pokazuje šta pokrenuti, šta svaki fajl radi, ručne testove i tačne očekivane rezultate.

Rješenje projektnog zadatka iz Naprednih operativnih sistema: Windows aplikacija u C-u, direktno poravnato interpretiranje, 8 MHz, ROM boot loader, prekidi na 20 ms, 16-segmentni ekran 80 × 25, tastatura sa sken kodovima i disk sa sektorima od 256 bajtova. Prilagođeni eFORTH se učitava sa diska izvršavanjem gostujućeg boot loadera.

## Pokretanje bez kompajlera

1. Raspakovati **cijeli** paket u folder u koji je dozvoljeno pisanje.
2. Pokrenuti `POKRENI.bat` ili `sveu16.exe`.
3. Nakon pozdravne poruke pritisnuti Enter. Pojavljuje se `ok`.
4. Koristiti fizički US raspored tipki. Prvo unijeti `DECIMAL` ako se žele decimalni brojevi.

Uz program moraju ostati `boot.rom` i `disk.img`. Za automatizovane testove potreban je i `forth.map`. Aplikaciji nisu potrebni Python, IDE ili instaliran C kompajler. Izvršna datoteka je za 64-bitni Windows i koristi sistemski UCRT.

Primjer, svaku liniju potvrditi tipkom Enter:

```text
DECIMAL
2 3 + .
: KVADRAT DUP * ;
9 KVADRAT .
```

Rezultati su `5` i `81`. Tačka je Forth riječ za ispis broja. Velika i mala slova na segmentnom ekranu imaju isti oblik, ali gost prima stvarne ASCII znakove. Shift radi; Caps Lock i nacionalni rasporedi nisu implementirani u gostujućem drajveru. Ctrl+V nije način unosa u emuliranu tastaturu.

**F12** ponovo pokreće računar: briše RAM, zadržava disk i učitava OS iz početka. Zatvaranje prozora prekida program. Novodefinisane Forth riječi žive u RAM-u i resetom se gube, osim ako se njihov sadržaj zasebno ne sačuva na disk.

## Šta predati

- `src/` — kompletan C kod procesora, uređaja, Windows interfejsa i asemblera.
- `firmware/` — izvorni boot loader i prilagođeni eFORTH.
- `sveu16.exe`, `asm.exe`, `boot.rom`, `forth.bin`, `disk.img`, `disk.factory.img`, mape simbola.
- `docs/IZVJESTAJ.pdf` i `docs/OBJASNJENJE.md` — tehničko objašnjenje; `docs/ODBRANA.md` — priprema za demonstraciju.
- `POCNI_OVDJE.pdf` — nacrtani vodič za pokretanje, testiranje i ručnu evidenciju rezultata.
- `tests/`, `TESTIRAJ.bat`, `test.ps1`, `build.ps1` — ponovljive provjere i izgradnja.
- `IZVORI.md` i `SHA256SUMS.txt` — porijeklo i kontrolne sume.

Originalni nastavni ZIP/PDF nisu izmijenjeni i ostaju izvan ovog paketa u roditeljskom folderu. Izvorni autorski navodi eFORTH-a su zadržani.

## Testiranje

Zatvoriti otvoreni emulator i pokrenuti `TESTIRAJ.bat`. Provjerava stvarni emulator, boot, Forth komande, nove definicije, varijable i petlju; prekida se ako očekivani rezultati izostanu. Ne mijenja sadržaj diska. Ne zahtijeva PowerShell skripte; `test.ps1` je dodatna verzija za okruženja u kojima su one dozvoljene. Tekstualni prikaz video memorije na kraju je samo približno dekodiranje segmentnih maski; grafički prozor je stvarni prikaz.

Napredna provjera, uz Python 3, bez dodatnih paketa:

```powershell
python tests/integration.py
```

Ona poredi rezultate C i Python asemblera, provjerava disk kroz gostujuće Forth komande na privremenoj kopiji, trajnost zapisa, skrolovanje i Backspace, te pokreće nezavisni referentni model. Postojeći radni `disk.img` ostaje netaknut.

Rezultati izvršenih provjera su u `tests/unit-result.txt`, `tests/integration-result.json` i odgovarajućim tekstualnim zapisima. CPU test je prošao 74.901 tvrdnju, uključujući svako od 65.536 kodiranja instrukcija. Windows Application Control je blokirao naknadno pokretanje ponovo izgrađene zasebne testne izvršne datoteke istog izvornog koda; prethodni uspješan rezultat je sačuvan. Završni glavni emulator je nakon toga prošao integracijske provjere. Sigurnosne postavke nisu mijenjane.

## Ponovna izgradnja

Potreban je GCC/MinGW-w64 ili Clang/LLVM-MinGW za Windows, sa podrškom za GNU C `labels-as-values`. MSVC samostalno ne podržava ovu tehniku.

```powershell
.\build.ps1 -CC 'C:\putanja\do\mingw\bin\gcc.exe'
.\test.ps1
```

Opcija `-RunCpuTests` dodatno pokreće C CPU test. `build.ps1` uvijek izgrađuje i njegovu izvršnu datoteku. Windows može primijeniti svoja pravila za izvršavanje novih programa; takvu blokadu treba razlikovati od greške testa.

Izgradnja koristi `-std=gnu11 -O2 -Wall -Wextra -Werror`. Stvara novu `disk.factory.img`, ali ne prepisuje postojeći radni disk. Za prelazak na novoizgrađeni OS zatvoriti emulator, sačuvati željene podatke iz radnog diska i svjesno zamijeniti `disk.img` kopijom `disk.factory.img`.

Detalji odluka koje postavka nije precizirala, poznata ograničenja i objašnjenje razlike između početnog koda i PDF specifikacije nalaze se u izvještaju.
