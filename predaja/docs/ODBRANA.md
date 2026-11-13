# Kratka priprema za odbranu

## Objašnjenje u jednoj minuti

Program u C-u na Windowsu simulira računar SVEU16. Procesor ima 16 registara i 16 instrukcija, a memorija se adresira po 16-bitnim riječima. Na početku izvršava ROM boot loader na adresi nula. Boot preko disk portova prenosi eFORTH u RAM na 0x3000 i predaje mu izvršavanje. Tastatura daje sken kodove, koje OS prevodi u ASCII. OS zatim znakove pretvara u maske 16 segmenata i upisuje u video memoriju na 0x2000. CPU radi ciljno na 8 MHz, a prekid nastaje svakih 160.000 ciklusa.

## Demonstracija od pet minuta

1. Pokazati `src/vm.c`, `firmware/boot.asm` i `firmware/forth.asm` i objasniti ko izvršava koji kod.
2. Pokrenuti aplikaciju, Enter, `DECIMAL`, `2 3 + .` i pokazati rezultat 5.
3. Definisati `: KVADRAT DUP * ;`, pa `9 KVADRAT .`; rezultat 81 pokazuje rad Forth rječnika.
4. Unijeti `HEX FFFF 2000 !`, zatim `0 2000 !`, da se vidi direktno paljenje/gašenje segmenata.
5. Pokazati brojač IRQ-a i objasniti račun 8.000.000 × 0,020 = 160.000.
6. Pokazati rezultate testova i disk integracijski test. On zaista piše sektor iz gostujućeg Forth-a, pa ga čita u novom procesu.

## Pitanja koja treba znati objasniti

**Zašto 1 kiloriječ ROM-a znači 2048 bajtova?** Jedna riječ je 16 bita, odnosno dva bajta. Kiloriječ ovdje znači 1024 riječi.

**Zašto eFORTH počinje na 0x3000?** Niži prostor sadrži ROM i video memoriju. Time kernel i njegov rječnik ne prepisuju uređaje.

**Zašto sektor ima 128 prenosa?** Sektor ima 256 bajtova, a jedan pristup 16-bitnom portu prenosi dva bajta.

**Ko pretvara sken kod u ASCII?** Gostujuća Forth rutina `?RX`, ne Windows host. Host prenosi fizičke događaje tastature.

**Ko pretvara ASCII u segmente?** Gostujuća `DRAWCHAR` i tabela `FONT`. Windows samo crta bitove upisane u video memoriju.

**Šta je direktno poravnato interpretiranje ovdje?** Gostujućoj adresi A odgovara fiksni zapis `decoded[A]` sa adresom C labele i registrima. Interpreter skače direktno na tu labelu pomoću computed goto.

**Zašto se dekodirani zapis poništava pri upisu?** Forth može napraviti ili promijeniti izvršni kod. Stara dekodirana instrukcija ne smije ostati u kešu nakon upisa nove riječi.

**Kako se vraća iz prekida?** Hardver ubacuje MAJ R14,R15,R13, koji čuva PC+1. Rutina oduzima jedinicu i vraća se na prekinutu instrukciju, jer je IRQ zamijenio njen dohvat.

**Zašto izvorne vrijednosti registara moraju biti sačuvane prije upisa?** Da instrukcije sa istim izvornim i odredišnim registrom koriste stare izvore, kako rade paralelne veze stvarnog procesora.

**Zašto je ispravljena instrukcija SHR?** PDF i početni C primjer se razlikuju. Izabrana je specifikacija PDF-a i usklađene su OS konstante, što je pokriveno testovima.

**Da li Windows garantuje tačno 8 MHz?** Cilj se računa preciznim brojačem vremena, ali Windows nije real-time sistem. Simulirani odnos 160.000 ciklusa po IRQ-u ostaje tačan; stvarna brzina može pasti pod opterećenjem.

**Da li je ovo cijeli moderan operativni sistem?** Ovo je zadati prilagođeni eFORTH: interpreter, rječnik, memorija i osnovni I/O. Nema zaštićene procese, FAT ili multitasking.

**Šta testovi dokazuju?** Sva kodiranja instrukcija prošla su za izabrane vrijednosti registara, uređaji imaju granične provjere i stvarni OS izvršava primjere. To je jaka praktična provjera, a ne dokaz da nijedan mogući ulaz ne može izazvati grešku.

Pročitati glavni izvještaj i probati primjere prije predaje. U odbrani razlikovati preuzeti Forth interpreter od novog emulatora i prilagođenih drajvera; ne predstavljati izvorni eFORTH kao vlastiti rad.
