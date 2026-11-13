# Sistemska virtualna mašina SVEU16

## 1. Cilj i ostvareno ponašanje

Izrađen je emulator kompletnog malog računara, a ne samo aplikacija koja računa Forth izraze. Windows pokreće C program. C program simulira procesor SVEU16, njegovu memoriju, disk, tastaturu i ekran. Simulirani procesor izvršava stvarne SVEU16 instrukcije boot loadera i eFORTH-a.

Put pokretanja je: Windows → emulator → ROM na adresi 0 → disk kontroler → eFORTH u RAM-u → interaktivne komande. Domaćin učitava samo ROM. OS u RAM prenosi gostujući boot loader kroz iste portove koje kasnije može koristiti Forth.

Postavka je zahtijevala: C, Windows, direktno poravnato interpretiranje, 8 MHz, ROM od 1 kiloriječi na adresi 0, prekid svakih 20 ms, ekran od 80 × 25 znakova sa 16 segmenata na adresi 8192, tastaturu na 0xFFFF i disk s portovima 0xFFFE/0xFFFD/0xFFFC i sektorima od 256 bajtova. Sve ove komponente imaju odgovarajuću implementaciju u izvornom kodu.

## 2. Polazni materijali i izmjene

Polazni materijali su nastavni `SVEU16-CPU-final.pdf`, postavka sa slike i arhiva `sveu16.zip`. Arhiva sadrži početni emulator, asembler i eFORTH. Originali su sačuvani izvan predajnog paketa.

Početni emulator je koristio `switch` za izbor instrukcije, bitmap ekran 640 × 480 od adrese 0xB000, ASCII tastaturu na 0xFFF1, nominalnih 10 MHz i direktno učitavanje `forth.mem` u memoriju. To nije konfiguracija tražena zadatkom. Zato je napisana nova C implementacija računara, dok je postojeći eFORTH prilagođen njegovim novim uređajima i adresama.

Zadržani su Forth interpreteri, rječnik i većina operacija. Promijenjeni su mjesto učitavanja, drajver tastature, drajver ekrana i konstante pomjeranja ulijevo. Ispravljene su i duplirane oznake AR5/AR13 u dostavljenom izvoru, koje su pripadale riječima za registre R6/R12. Zadržani su izvorni autorski navodi.

Posebno neslaganje: PDF za `SHR` propisuje kod 10 za rotaciju udesno, a 11 za logičko pomjeranje ulijevo. Početni C emulator je koristio 10 za pomjeranje ulijevo, a 11 za rotaciju ulijevo. Novo jezgro slijedi opis PDF-a; Forth konstante za pomjeranje ulijevo prebačene su sa 0x20 na 0x30 i sa 0x28 na 0x38. Tako se ispravka procesora nije pretvorila u tihu grešku u OS-u.

## 3. Organizacija projekta

| Datoteka | Odgovornost |
| --- | --- |
| src/vm.h | Struktura stanja računara, konstante i javne funkcije |
| src/vm.c | CPU, direktno poravnata interpretacija, memorija, disk, FIFO tastature, IRQ |
| src/main.c | Windows prozor, segmentni prikaz, tajming, ulazni događaji i batch režim |
| src/asm.c | Dvoprolazni asembler s provjerom simbola i operanada |
| firmware/boot.asm | Kod koji iz ROM-a učitava eFORTH preko disk portova |
| firmware/forth.asm | Prilagođeni eFORTH sa gostujućim drajverima |
| tests/test_vm.c | Provjera CPU-a, uređaja, prekida i izmjene koda |
| tests/reference.py | Nezavisni Python asembler i spori referentni CPU model |
| tests/integration.py | Integracijske provjere stvarne C izvršne datoteke |

Glavni emulator i asembler napisani su u C-u. Python je dodatni alat za provjeru, a ne dio emulatora niti uslov za pokretanje predatog programa.

## 4. Memorija i adresiranje

SVEU16 adresira 16-bitne riječi. Ukupno 65.536 adresa zato predstavlja 131.072 bajta, odnosno 128 KiB. Adresa 8192 znači riječ broj 8192, a ne bajt na pomjeraju 8192.

| Adrese riječi | Namjena |
| --- | --- |
| 0x0000–0x03FF | ROM: 1024 riječi, odnosno 2048 bajtova |
| 0x0400–0x1FFF | Slobodni RAM |
| 0x2000–0x27CF | Video memorija: 2000 riječi za 80 × 25 znakova |
| 0x27D0–0x2FFF | Slobodni RAM između ekrana i OS-a |
| 0x3000–0x4569 | Početna slika prilagođenog eFORTH-a: 5482 riječi |
| 0x456A naviše | Prostor za proširenje Forth rječnika, do rezervisanih područja OS-a |
| 0xAE30–0xAEAF | Korisničke strukture i stekovi prema Forth konstantama |
| 0xAEB0–0xAEFF | Terminalni bafer i granica memorije koju koristi eFORTH |
| 0xAF00–0xFFFB | Preostali RAM koji standardni Forth alokator ne koristi |
| 0xFFFC–0xFFFF | Memorijski mapirani uređaji |

Granice pojedinih Forth struktura određuju njegovi simboli EUP, ERP, ESPP i ETIB; dijelovi početnog rasporeda se preklapaju po granicama, a stekovi rastu prema manjim adresama. Mape simbola su konačan izvor tačnih adresa oznaka.

ROM se ne može promijeniti instrukcijom `STO`. Upis i dalje postavlja odredišni registar, kao što propisuje semantika instrukcije, ali memorijska riječ u ROM-u ostaje ista. Video memorija je obična čitljiva i upisiva memorija sa dodatnom oznakom da je potrebno osvježiti ekran.

OS je premješten na 0x3000 zato što ne smije prepisati ROM niti zauzeti video područje. Sama promjena konstante u emulatoru ne bi bila dovoljna: asembler mora ponovo izračunati adrese svih oznaka u Forth kodu.

## 5. Procesor i instrukcije

Procesor ima 16 registara R0–R15, širine 16 bita. R15 je programski brojač. R0 nije hardverski vezan za nulu: Forth ga po konvenciji održava na nuli, a R1 na jedinici. R13 je adresa prekidne rutine, a R14 čuva povratnu adresu prekida.

Instrukcija ima četiri heksadecimalne cifre: OP, DEST, SRC1, SRC2. Primjer `ADD R2,R3,R4` kodira se kao 0x1234. Prva cifra bira operaciju, a preostale tri označavaju registre.

| Kod | Instrukcija | Efekat |
| --- | --- | --- |
| 0 | LOD | DEST = memorija[SRC2] |
| 1 | ADD | DEST = SRC1 + SRC2, modulo 65536 |
| 2 | SUB | DEST = SRC1 − SRC2, modulo 65536 |
| 3 | AND | Logičko I nad bitovima |
| 4 | ORA | Logičko ILI nad bitovima |
| 5 | XOR | Ekskluzivno ILI nad bitovima |
| 6 | SHR | Pomjeranje/rotacija prema upravljačkoj vrijednosti SRC2 |
| 7 | MUL | Donjih 16 bita proizvoda |
| 8 | STO | memorija[SRC2] = SRC1; DEST = SRC1 |
| 9 | MIF | Ako SRC1 nije nula, DEST = SRC2 |
| A | GTU | Neoznačeno poređenje veće od; rezultat 0 ili 1 |
| B | GTS | Označeno poređenje veće od; rezultat 0 ili 1 |
| C | LTU | Neoznačeno poređenje manje od; rezultat 0 ili 1 |
| D | LTS | Označeno poređenje manje od; rezultat 0 ili 1 |
| E | EQU | Poređenje jednakosti; rezultat 0 ili 1 |
| F | MAJ | DEST = SRC1; R15 = SRC2 |

Operandi R15 vide vrijednost PC+1. Oba izvora se snime prije upisa rezultata. To je važno kada se isti registar pojavljuje kao izvor i odredište; naročito `MAJ` mora skočiti na staru vrijednost SRC2, čak i kada je DEST isti registar.

Za `LOD` i `STO` sa SRC2=R15 i DEST različitim od R15 preskače se dodatna riječ: sljedeći PC je stari PC+2. Kada je odredište R15, primjenjuje se upis novog PC-a. Ovdje se prati detaljno objašnjenje PC multipleksera iz odjeljka II-F PDF-a.

Za `SHR`, četiri najniža bita SRC2 određuju broj pomjeranja 0–15; bitovi 5 i 4 određuju vrstu: 00 aritmetički udesno, 01 logički udesno, 10 rotacija udesno, 11 logički ulijevo. Rotacija za nulu čuva vrijednost i ne izvodi neispravno pomjeranje za punu širinu tipa. Množenje koristi širi neoznačeni međurezultat da ne nastane prekoračenje označenog C tipa.

## 6. Direktno poravnato interpretiranje

Osnovna tehnika je direktno threaded interpretiranje sa tabelom dekodiranih zapisa poravnatih prema gostujućim adresama. Za svaku od 65.536 riječi postoji jedan zapis `Decoded` u nizu `decoded`. Gostujuća adresa A uvijek odgovara zapisu `decoded[A]`, nezavisno od toga predstavlja li ta riječ trenutno kod ili podatak.

Zapis sadrži direktnu adresu C labele za instrukciju i indekse tri registra. Pri prvom izvršavanju određene adrese, instrukcija se dekodira i popunjava zapis. Kasnije se izvršavanje preusmjerava izrazom `goto *p->handler`, bez ponovljenog velikog `switch` izbora prema opcode-u.

Poravnanje ovdje znači stalnu vezu između adrese riječi i zapisa iste veličine u nizu; nije pretpostavka da gostujući kod mora biti poravnat na neku višebajtnu granicu. Ne generišu se nove x86 instrukcije i ovo nije JIT. Izvršava se već kompajlirani C kod odgovarajuće labele.

Forth stvara nove definicije tokom rada i može mijenjati memoriju koja se izvršava. Zato svaki uspješan upis u RAM poništava `decoded[adresa].handler`. Pri sljedećem izvršavanju te adrese dekodira se nova riječ. Bez toga bi emulator mogao nastaviti izvršavati staru instrukciju nakon promjene programa. Instrukcije dohvaćene iz područja portova uvijek se čitaju ponovo, jer njihov sadržaj nije stabilan.

Prednosti su jednostavno mapiranje skokova i izbjegavanje ponovnog dekodiranja stabilnog koda. Trošak je dodatna memorija domaćina. Na x64 platformi zapis zauzima 16 bajtova, pa tabela zauzima približno 1 MiB; gost i dalje vidi samo svojih 128 KiB adresnog prostora. GCC/Clang proširenje `labels-as-values` izabrano je upravo za ovakav direktan skok.

## 7. Frekvencija i prekidi

Prema specifikaciji sve instrukcije traju jedan ciklus. Ciljna frekvencija je 8.000.000 ciklusa u sekundi. Windows sloj koristi `QueryPerformanceCounter` da izmjeri proteklo vrijeme, množi ga sa 8.000.000 i izvrši odgovarajući broj ciklusa. Razlomljeni dio se prenosi u sljedeći interval, pa se ne gubi stalnim zaokruživanjem.

Za 20 ms vrijedi: 8.000.000 × 0,020 = 160.000 ciklusa. Brojač u CPU-u generiše IRQ nakon svakih 160.000 završenih ciklusa. Ne zavisi od broja osvježavanja ekrana niti od preciznosti Windows tajmera. Batch režim izvršava isti broj simuliranih ciklusa što brže, bez čekanja na stvarno vrijeme.

PDF definiše prekid kao zamjenu dohvaćene instrukcije konstantom 0xFEFD, odnosno `MAJ R14,R15,R13`. Emulator zato čuva PC+1 u R14, prelazi na R13 i troši jedan ciklus. Preskočena instrukcija ne smije biti izgubljena: ROM rutina na adresi 0x0022 izvršava `SUB R15,R14,R1`, čime se vraća na R14−1. Boot loader odmah postavlja R1=1 i R13=0x0022. Ova kratka rutina ne mijenja ostale registre; R13/R14 su rezervisani i nisu Forth radni registri.

IRQ se generiše i obrađuje, iako OS ne koristi tajmer za raspoređivanje procesa. Ovaj eFORTH je interaktivni sistem bez preemptivnog multitaskinga. Nisu izmišljeni dodatni registri za maskiranje prekida koje PDF ne propisuje.

Windows nije sistem stvarnog vremena. Ako se prozor dugo zadrži pri pomjeranju ili se proces pauzira, nadoknada se ograničava na 250 ms po koraku kako interfejs ne bi ostao blokiran. To može usporiti gostujuće vrijeme u odnosu na zidni sat, ali ne mijenja odnos ciklusa i prekida. Ne tvrdi se da se fizički IRQ dogodi tačno svakih 20 ms zidnog vremena pod svakim opterećenjem domaćina.

## 8. ROM i boot loader

`boot.rom` je tačno 2048 bajtova, sa 1024 little-endian riječi. Pri resetu PC je nula. Boot postavlja konstantne registre i prekidnu adresu, resetuje kontroler diska, a zatim učitava sektore 0–127 na adrese 0x3000–0x6FFF.

Za svaki sektor upisuje njegov broj u port 0xFFFD, šalje komandu 1 portu 0xFFFE i čita 128 riječi iz porta 0xFFFC. Svaku riječ upisuje instrukcijom `STO` u RAM. Po završetku skače na 0x3000, gdje počinje resetni ulaz eFORTH-a.

Učitava se fiksnih 128 sektora odnosno 32 KiB. Stvarni OS zauzima 10.964 bajta; ostatak početnog područja na disku popunjen je nulama. Fiksna veličina pojednostavljuje mali boot loader. Skripta za izgradnju odbija OS veći od tog područja. Ovo je izbor formata slike diska, jer postavka ne definiše zaglavlje ili datotečni sistem.

Host pri otvaranju provjerava veličinu ROM-a i diska. Ne provjerava se kriptografska autentičnost OS-a niti postoji sistem oporavka od oštećenih kernel sektora. Za vraćanje početnog sadržaja služi `disk.factory.img`.

## 9. Disk kontroler

Disk je datoteka `disk.img` veličine 1 MiB, odnosno 4096 sektora po 256 bajtova. Veličina diska je dokumentovani izbor implementacije. Zapis se otvara za čitanje i pisanje; po završetku sektorskog upisa poziva se `fflush` da promjene ostanu vidljive i narednom pokretanju programa.

| Port | Upis | Čitanje |
| --- | --- | --- |
| 0xFFFD | Izbor sektora 0–4095 | Trenutno izabrani sektor, dijagnostičko proširenje |
| 0xFFFE | Komanda: 0 reset, 1 read, 2 write | Status, dijagnostičko proširenje |
| 0xFFFC | Sljedeća riječ pri write operaciji | Sljedeća riječ pri read operaciji |

Jedan pristup podatkovnom portu prenosi 16 bita. Zato sektor zahtijeva 128 pristupa, a ne 256. Niži bajt riječi se čuva prvi. Postavka određuje veličinu sektora i port, ali ne govori da li je prenos bajtni ili riječ po riječ; izabran je prirodni 16-bitni prenos za ovaj procesor.

Komanda read učitava sektor u bafer i postavlja položaj na nulu. Komanda write priprema prazan bafer; tek 128. riječ izaziva upis cijelog sektora u datoteku. Reset usred nepotpunog upisa odbacuje bafer, bez djelimičnog mijenjanja diska. Nova komanda ponovo postavlja položaj prenosa. Izbor drugog sektora treba izvršiti prije slanja komande.

Status je 0 bez greške, 1 za nepoznatu komandu/neispravan sektor/nedostupan disk, 2 za pogrešan smjer ili prekoračenje prenosa i 3 za grešku datotečnog I/O-a. Status se poništava novom komandom. Čitanje statusa i izabranog sektora je dodatna dijagnostička mogućnost; propisani izlazni portovi i njihove komande ostaju očuvani.

Nije implementiran FAT ili drugi datotečni sistem: zadatak traži emulirani disk i učitavanje OS-a sa njega. Sektori poslije 127 dostupni su za korisničke podatke. Integracijski test koristi sektor 3000 na privremenoj kopiji diska.

## 10. Tastatura

Windows interfejs obrađuje događaje pritiska i otpuštanja tipke, uzima hardverski sken kod iz poruke i stavlja ga u FIFO. Ako testni/injektovani događaj nema sken kod, `MapVirtualKey` ga izvodi iz virtuelne tipke. Ne šalje se ASCII sa hosta direktno u gostujući port.

Čitanje 0xFFFF uklanja jedan kod iz FIFO-a; nula označava da nema događaja. Bafer ima kapacitet 1023 događaja; kada je pun, novi događaj se odbija. Sken kodovi koriste osnovni PC set-1 raspored. Bit 7 označava otpuštanje, a bit 8 proširenu tipku. Nepodržani prošireni događaji se ignorišu u gostujućem drajveru.

Forth rutina `?RX` čita kod sa porta, prati stanje lijevog i desnog Shift-a, ignoriše otpuštanja običnih tipki i koristi tabelu US rasporeda da dobije ASCII. Svaki Shift ima svoj bit, tako da otpuštanje jednog ne poništava drugi koji je još pritisnut. Tablice imaju po 128 elemenata za osnovni i Shift režim.

Podržani su osnovni znakovi, Enter, Backspace i Shift. Caps Lock, AltGr, nacionalni rasporedi i numerički blok nisu cjelovito mapirani. To ograničenje se odnosi na gostujući tekstualni drajver: emulator i dalje prosljeđuje njihove sken događaje. Gubitak fokusa šalje otpuštanja Shift-a kako se unos ne bi zadržao u pogrešnom režimu.

## 11. Ekran sa 16 segmenata

Video memorija počinje na decimalnoj adresi 8192 (0x2000). Adresa znaka u koloni x i redu y je 8192 + y × 80 + x, pri čemu su x=0–79 i y=0–24. Svaka riječ je maska 16 segmenata, a ne ASCII kod.

Bit vrijednosti 1 pali odgovarajući segment; 0 ga gasi. Program crta segmente Win32 GDI linijama, skaliranim prema veličini prozora. Svih 16 bitova upravlja nezavisnim segmentima. Numeracija nije zadana na slici, pa je usvojena i dosljedno dokumentovana sljedeća:

| Bit | Segment |
| --- | --- |
| 0, 1 | Gornji lijevi i gornji desni vodoravni dio |
| 2, 3 | Gornji desni i donji desni uspravni dio |
| 4, 5 | Donji desni i donji lijevi vodoravni dio |
| 6, 7 | Donji lijevi i gornji lijevi uspravni dio |
| 8, 9 | Srednji lijevi i srednji desni vodoravni dio |
| 10 | Dijagonala gornji lijevi ugao → centar |
| 11 | Središnja gornja uspravna linija |
| 12 | Dijagonala gornji desni ugao → centar |
| 13 | Dijagonala donji lijevi ugao → centar |
| 14 | Središnja donja uspravna linija |
| 15 | Dijagonala centar → donji desni ugao |

Forth rutina `DRAWCHAR` pretvara ASCII u masku preko tabele `FONT` u gostujućem RAM-u. Host ne radi ovu konverziju za stvarni prikaz. Drajver održava X/Y položaj, podržava CR, LF, Backspace, prelazak u sljedeći red i skrolovanje: kopira 1920 riječi iz redova 1–24 u redove 0–23, a posljednjih 80 riječi briše.

Velika i mala slova dijele izgled na ekranu. Neki oblici, poput O/0 i S/5, slični su ili jednaki zbog ograničenog skupa segmenata. Dijagnostički ASCII prikaz u batch izlazu ne može uvijek rekonstruisati originalni znak iz maske, pa nije mjerilo tačnosti Forth izlaza; ispred njega nalazi se tačan trag znakova koje je gost poslao svojoj rutini ispisa.

Grafičko osvježavanje je odvojeno od CPU frekvencije. Promjene se prikazuju do približno 25 puta u sekundi, a statistika se osvježava najmanje na pola sekunde simuliranog vremena. Prazne ćelije ne zahtijevaju crtanje svih ugašenih linija. Jedna Windows nit obrađuje i gostujuće cikluse i poruke, pa nema konkurentnih upisa u registre, video memoriju ili GDI objekte.

## 12. Asembler i izgradnja

Novi asembler radi u dva prolaza. U prvom računa adrese i prikuplja oznake; u drugom razrješava njihove vrijednosti i emituje instrukcije. Podržava 16 instrukcija i direktive `ORG`, `WRD`, `TXT`, `CON`. Provjerava duple/nepoznate oznake, neispravne registre, nedostajuće i višak operanada, preklapanje memorije i prekoračenje adresa.

Izlaz je niz little-endian riječi od najniže do najviše emitovane adrese, uz odvojenu mapu simbola. Boot koristi ORG 0 i završnu riječ na adresi 1023, pa ROM ima tačnu veličinu. Forth koristi ORG 0x3000, ali njegova binarna datoteka ne sadrži nepotrebnih 0x3000 početnih praznih riječi.

`build.ps1` kompajlira C izvore, asemblira firmware i pravi tvornički disk. Postojeći radni disk se ne prepisuje automatski, jer može sadržati korisničke sektore. Standardni GCC/MinGW ili LLVM-MinGW mogu izgraditi projekt pomoću GNU C11 opcije. Kompilacija uključuje `-Wall -Wextra -Werror`.

## 13. Izvršene provjere i njihova granica

CPU provjera prošla je svih 65.536 mogućih kodiranja instrukcije sa deterministički izabranim sadržajem registara. Za svaki slučaj nezavisno se računa očekivano stanje, uključujući preklapanje izvora/odredišta i R15. To ne iscrpljuje sve moguće kombinacije 16-bitnih vrijednosti registara, pa rezultat nije formalni dokaz odsustva svake greške.

Dodatno su provjereni zaštita ROM-a, upis video memorije, FIFO tastature i njegova granica, disk read/write, odbacivanje nepotpunog sektora, neispravan sektor/komanda, samomodifikujući kod, ubrizgavanje IRQ-a, ispravan povratak i interval od 160.000 ciklusa. Ukupno je prošla 74.901 tvrdnja. Izvještaj je `tests/unit-result.txt`.

Nezavisni Python asembler dao je identične ROM i OS bajtove kao C asembler. Referentni CPU model pokrenuo je isti ROM i eFORTH i izvršio sabiranje i novo definisanu riječ. Ovo smanjuje mogućnost da su generator i emulator međusobno sakrili istu grešku.

Integracijski testovi završne C aplikacije provjerili su: rezultate 5 i 81, LSHIFT/RSHIFT, dijeljenje s ostatkom, varijablu s vrijednošću 123, petlju sa rezultatom 45, upis svih 128 riječi sektora iz gosta, ponovno čitanje sa zbirom 8128, trajnost sadržaja pri novom pokretanju, 60 linija izlaza, skrolovanje i Backspace. Za disk se koristi privremena kopija, a sadržaj sektora dodatno se čita direktno iz datoteke i provjerava bajt po bajt.

U grafičkom prozoru provjereni su pozdrav OS-a, fizički unos tipke, Enter i Forth tačka za ispis vrijednosti. Snimak je `docs/emulator.png`. Izmjene u osvježavanju i dopuna za injektovane sken događaje provjerene su u završnoj aplikaciji i integracijskim testovima.

Na korištenom Windowsu Application Control je odbio najnoviji preuzeti Clang; službeni stabilni Clang 19.1.7 se pokrenuo i korišten je za izgradnju s MinGW bibliotekama. Nakon prvog uspješnog CPU testa, sigurnosna politika blokirala je naknadno pokretanje zasebnog ponovo izgrađenog testnog EXE-a istog izvornog koda. To je ograničenje okruženja, a ne zabilježeni neuspjeh CPU tvrdnje. Glavna završna izvršna datoteka uspješno je pokrenuta i prošla navedene integracijske testove. Zaštita Windowsa nije isključivana.

## 14. Demonstracija rada

Pokrenuti emulator, potvrditi Enterom, pa unijeti:

```text
DECIMAL
2 3 + .
: KVADRAT DUP * ;
9 KVADRAT .
VARIABLE BROJ
123 BROJ ! BROJ @ .
```

Očekuju se 5, 81 i 123. Nove riječi pokazuju da Forth zaista kompilira definicije u gostujuću memoriju i da emulator može izvršavati novoupisani sadržaj.

Za pokazivanje svih segmenata prve ćelije:

```text
HEX
FFFF 2000 !
0 2000 !
DECIMAL
```

Prva komanda pali svih 16 segmenata; druga ih gasi. To direktno demonstrira mapiranu video memoriju i razlikovanje maske segmenata od ASCII znaka.

Za petlju koristiti podržani skup riječi ovog eFORTH-a:

```text
: SUMA 0 10 BEGIN DUP WHILE 1 - SWAP OVER + SWAP REPEAT DROP ;
SUMA .
```

Rezultat je 45. Početni eFORTH nije puna implementacija svih ANS Forth riječi; primjer zato koristi BEGIN/WHILE/REPEAT i `1 -`, umjesto nepodržanih DO/LOOP ili `1-`.

## 15. Dokumentovane odluke i ograničenja

Postavka nije precizirala kapacitet diska, redoslijed bajtova, širinu jednog prenosa preko podatkovnog porta, tačnu numeraciju segmenata ni raspored tastature. Ovdje su izabrani 1 MiB, little-endian, 16-bitni prenos, prikazana tabela segmenata i US set-1 sken raspored. To su javne konvencije projekta, a ne tvrdnje da ih je profesor izričito zadao.

Direktno poravnato interpretiranje ostvareno je fiksnim zapisom za svaku gostujuću adresu i direktnim skokom na C labelu. Ako predmet koristi drugačiju formalnu definiciju tog termina, ovu implementaciju treba porediti s nastavnim slajdovima; takvi slajdovi nisu bili u dostavljenom folderu.

Disk nema datotečni sistem, firmware nema provjeru kontrolne sume, a proizvoljno oštećen gostujući program može upisati pogrešne adrese ili promijeniti rezervisane registre. Emulator ne pokušava dokazati ispravnost gosta. Nije implementirano potpuno međunarodno mapiranje tastature. GUI tajming zavisi od raspoloživog vremena Windows procesa. Ove granice su navedene kako bi demonstracija i odbrana odgovarale stvarnom ponašanju programa.
