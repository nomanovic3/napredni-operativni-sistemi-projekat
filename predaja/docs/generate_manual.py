"""Illustrated manual checks. Optional: Python, Pillow and ReportLab."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Preformatted,Image,Table,TableStyle,KeepTogether
from reportlab.graphics.shapes import Drawing,Rect,Line,Polygon,String
from PIL import Image as PILImage
from generate_report import body,h1,small,cell,code,NAVY,GREEN,GRAY,inline
ROOT=Path(__file__).resolve().parents[1]
story=[]
def p(t):story.append(Paragraph(inline(t),body))
def title(n,t):
    if story:story.append(PageBreak())
    story.append(Paragraph(f'{n:02d} / {t}',h1));story.append(Spacer(1,8))
def sub(t):story.append(Paragraph(inline(t),ParagraphStyle('sub',parent=body,fontName='Bold',fontSize=12,leading=16,spaceBefore=12,spaceAfter=6)))
def cmd(t):story.append(Preformatted(t,code,maxLineLength=88))
def ok(t):story.append(Paragraph('OČEKIVANO: '+inline(t),ParagraphStyle('ok',parent=body,textColor=GREEN,fontName='Bold')))
def table(rows,widths):
    a=Table([[Paragraph(inline(v),cell) for v in row] for row in rows],colWidths=widths,repeatRows=1)
    a.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DAEAE5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#D4DFE2'))]))
    story.extend([a,Spacer(1,8)])
def box(d,x,y,w,h,label,detail='',fill='#EDF3F4'):
    d.add(Rect(x,y,w,h,rx=6,ry=6,fillColor=colors.HexColor(fill),strokeColor=None))
    d.add(String(x+w/2,y+h-20,label,fontName='Bold',fontSize=11,textAnchor='middle',fillColor=NAVY))
    if detail:d.add(String(x+w/2,y+13,detail,fontName='Body',fontSize=9,textAnchor='middle',fillColor=GRAY))
def arrow(d,x1,y1,x2,y2):
    d.add(Line(x1,y1,x2,y2,strokeColor=GREEN,strokeWidth=1.6))
    if y2<y1:pts=[x2,y2,x2-4,y2+7,x2+4,y2+7]
    elif y2>y1:pts=[x2,y2,x2-4,y2-7,x2+4,y2-7]
    else:pts=[x2,y2,x2-7,y2-4,x2-7,y2+4]
    d.add(Polygon(pts,fillColor=GREEN,strokeColor=None))
def overview():
    d=Drawing(505,245)
    box(d,137,185,230,55,'Raspakuj cijeli ZIP','Otvori folder predaja')
    arrow(d,252,185,252,160)
    d.add(Line(80,160,425,160,strokeColor=GREEN,strokeWidth=1.6))
    for x in [80,252,425]:arrow(d,x,160,x,139)
    box(d,5,76,150,63,'POKRENI.bat','Otvara emulator')
    box(d,177,76,150,63,'TESTIRAJ.bat','Provjerava rezultate')
    box(d,350,76,150,63,'docs / IZVJESTAJ.pdf','Objašnjava implementaciju')
    for x in [80,252,425]:arrow(d,x,76,x,54)
    for x,t in [(80,'Enter → DECIMAL'),(252,'Na kraju mora pisati PASS'),(425,'Za razumijevanje i odbranu')]:
        d.add(String(x,34,t,fontName='Body',fontSize=9,textAnchor='middle',fillColor=NAVY))
    return d
def boot():
    d=Drawing(505,104)
    for x,label,detail in [(0,'sveu16.exe','računar u C-u'),(130,'boot.rom','PC kreće od 0'),(260,'disk.img','OS sektori 0–127'),(390,'eFORTH','RAM: 0x3000')]:
        box(d,x,28,110,60,label,detail)
        if x<390:arrow(d,x+110,58,x+129,58)
    return d
def leds():
    d=Drawing(505,132)
    coords=[(0,16,4,16),(4,16,8,16),(8,16,8,8),(8,8,8,0),(8,0,4,0),(4,0,0,0),(0,0,0,8),(0,8,0,16),(0,8,4,8),(4,8,8,8),(0,16,4,8),(4,16,4,8),(8,16,4,8),(0,0,4,8),(4,8,4,0),(4,8,8,0)]
    for pos,mask,label in [(45,1,'1'),(170,2,'2'),(295,65535,'FFFF'),(420,0,'0')]:
        for bit,(x1,y1,x2,y2) in enumerate(coords):d.add(Line(pos+x1*4,35+y1*4,pos+x2*4,35+y2*4,strokeColor=GREEN if mask&(1<<bit) else colors.HexColor('#E0E6E8'),strokeWidth=2.5))
        d.add(String(pos+16,12,label,fontName='Code',fontSize=11,textAnchor='middle',fillColor=NAVY))
    return d
def footer(c,doc):
    c.saveState();c.setFont('Bold',8);c.setFillColor(NAVY);c.drawString(44,815,'SVEU16 / VODIČ ZA RUČNU PROVJERU');c.setStrokeColor(GREEN);c.line(44,806,551,806)
    c.setFont('Body',8);c.setFillColor(GRAY);c.drawString(44,27,'Bez kompajlera za pokretanje • 13.11.2026.');c.drawRightString(551,27,str(doc.page));c.restoreState()

title(1,'Šta otvaram i kojim redom?')
p('Ovaj vodič je za ručnu provjeru gotovog programa. Ne moraš instalirati kompajler. Sve komande unose se u prozor emulatora, osim koraka koji izričito kažu da otvoriš datoteku.')
story.append(overview())
table([['Datoteka / folder','Čemu služi?'],['POKRENI.bat / sveu16.exe','Pokretanje virtualnog računara. Dovoljno je otvoriti jedno od njih.'],['boot.rom + disk.img','Obavezni firmware i radni disk. Moraju ostati uz izvršni program.'],['TESTIRAJ.bat','Automatski pokreće primjere i poredi rezultate. Prije toga zatvori emulator.'],['disk.factory.img','Tvornička kopija diska. Ne otvara se dvoklikom.'],['src/ + firmware/','C i asemblerski izvori za pregled i ponovnu izgradnju.'],['build.ps1','Ponovna kompilacija; nije potrebna za korištenje gotovog programa.'],['docs/ + tests/','Objašnjenje, priprema za odbranu, testovi i zapisi njihovih rezultata.']],[175,330])
sub('Šta se događa nakon pokretanja?')
story.append(boot())
p('ROM kod čita disk preko emuliranih portova i sam učitava OS. Pozdrav eFORTH-a znači da je taj lanac prošao do interaktivnog sistema.')

title(2,'Prvo pokretanje i izgled prozora')
p('1. Raspakuj ZIP i otvori predaja.  2. Dvaput klikni POKRENI.bat.  3. Klikni u prozor SVEU16.  4. Pritisni Enter, zatim upiši DECIMAL i ponovo Enter.')
with PILImage.open(ROOT/'docs/emulator.png') as im:iw,ih=im.size
story.append(Image(str(ROOT/'docs/emulator.png'),width=505,height=505*ih/iw))
story.append(Spacer(1,8))
table([['Dio prozora','Šta pratiš?'],['Gore: eFORTH i autorski tekst','OS je pokrenut. Ovo je stvarni snimak iz testiranja.'],['Znak ok i tekst koji unosiš','Tu se odvija rad u Forth-u. Na snimku su uneseni 2 i tačka, koja je ispisala 2.'],['Donja statusna linija','Broj ciklusa, broj prekida IRQ i status diska. Brojevi ciklusa i IRQ moraju rasti.'],['F12','Reset: prazni RAM i ponovo učitava OS. Sadržaj diska ostaje.']],[170,335])
ok('Vidiš pozdrav, nakon Entera dobiješ ok, a DECIMAL ne prijavljuje grešku.')
p('Forth početno koristi HEX. DECIMAL bira decimalne brojeve. Svaku narednu liniju potvrdi Enterom. Ostavi razmake između riječi: `2 3 + .` je ispravno, `2+3` nije ista naredba.')
p('Gost koristi US raspored fizičkih tipki. Shift radi; za ovaj projekt ne oslanjaj se na Caps Lock, AltGr, nacionalne znakove ili Ctrl+V. Izgled slova na segmentnom ekranu je stilizovan.')

title(3,'Ručno provjeri računanje i OS')
p('Kreni iz svježe pokrenutog programa. Unesi DECIMAL. Komande ispod su provjerene u završnoj izvršnoj datoteci.')
sub('A. Sabiranje i osnovno izvršavanje')
cmd('2 3 + .')
ok('5, zatim ok. Dva broja idu na stek; + ih sabira; tačka ispisuje rezultat.')
sub('B. Napravi novu riječ u RAM-u')
cmd(': KVADRAT DUP * ;\n9 KVADRAT .')
ok('81. Prva linija definiše riječ, druga je izvršava. DUP duplira broj, * množi.')
sub('C. Upis i čitanje varijable')
cmd('VARIABLE BROJ\n123 BROJ ! BROJ @ .')
ok('123. Znak ! upisuje, @ čita memoriju, a tačka ispisuje vrijednost.')
sub('D. Pomjeranja i dijeljenje')
cmd('1 8 LSHIFT .\n256 4 RSHIFT .\n10 3 /MOD . .')
ok('Redom 256, 16, pa 3 1. Posljednja linija prikazuje količnik i ostatak.')
sub('E. Petlja i proširenje rječnika')
cmd(': SUMA 0 10 BEGIN DUP WHILE 1 - SWAP OVER + SWAP REPEAT DROP ;\nSUMA .')
ok('45, odnosno 0 + 1 + ... + 9. Cijelu definiciju unesi u jednoj liniji.')
p('U ovom eFORTH-u koristi se `1 -` s razmakom i BEGIN/WHILE/REPEAT. DO/LOOP i `1-` nisu podržani u dostavljenom rječniku. Ako vidiš ?(-13), Forth nije prepoznao neku riječ; provjeri unos.')

title(4,'Provjeri ekran, tastaturu i ROM')
sub('A. Svaki bit pali segment prve ćelije')
p('Unesi HEX. Poslije svake naredbe pogledaj krajnju gornju lijevu ćeliju, iznad pozdravnog teksta. U naredbama je 2000 heksadecimalna adresa, odnosno decimalno 8192.')
story.append(leds())
cmd('HEX\n1 2000 !\n2 2000 !\nFFFF 2000 !\n0 2000 !\nDECIMAL')
ok('Redom: gornji lijevi dio, gornji desni dio, svih 16 segmenata, pa prazna ćelija.')
p('Za pojedinačne ostale bitove umjesto 1/2 koristi HEX maske 4, 8, 10, 20, 40, 80, 100, 200, 400, 800, 1000, 2000, 4000 i 8000. Adresa u drugoj poziciji uvijek ostaje 2000.')
sub('B. Tastatura i Backspace')
cmd('DECIMAL\nKEY .')
p('Nakon potvrde KEY . pritisni slovo a. Program čeka tipku; to nije zaglavljenje. Ponovi KEY . pa pritisni Shift+A.')
ok('Za a dobiješ 97; za Shift+A dobiješ 65.')
p('Zatim otkucaj 12, pritisni Backspace jednom, dopiši 3, razmak i tačku, pa Enter. Time je stvarna komanda `13 .`.')
ok('13. Uklonjena dvojka ne ulazi u broj.')
sub('C. ROM ostaje zaštićen')
cmd('HEX 0 @ . 0 0 ! 0 @ . DECIMAL')
ok('E111 E111. Pokušaj upisa nule na adresu 0 nije promijenio ROM.')

title(5,'Provjeri prekide i trajni disk')
sub('A. Prekidi bez dodatnih naredbi')
p('Posmatraj donji IRQ brojač nekoliko sekundi. Na neopterećenom računaru trebalo bi da raste približno 50 u sekundi. Odnos je tačan u simuliranom vremenu: 160.000 ciklusa po prekidu. Windows može kasniti; nije garantovan strogi zidni real-time.')
ok('Brojači cycles i IRQ rastu, a Forth ostaje upotrebljiv.')
sub('B. Napiši sektor iz samog gosta')
p('Ovaj test namjerno mijenja sektor 3000 radnog diska. OS koristi sektore 0–127. Koristi dostavljenu testnu sliku diska i ne mijenjaj broj sektora proizvoljno.')
cmd('DECIMAL\n: FILL 128 BEGIN DUP WHILE 1 - DUP 65532 ! REPEAT DROP ;\n: SUM 0 128 BEGIN DUP WHILE 1 - SWAP 65532 @ + SWAP REPEAT DROP ;\n3000 65533 ! 2 65534 ! FILL\n3000 65533 ! 1 65534 ! SUM .\n65534 @ .')
ok('SUM . daje 8128, a čitanje statusa daje 0.')
table([['Decimalna adresa','Značenje u testu'],['65533 = 0xFFFD','Izaberi sektor 3000.'],['65534 = 0xFFFE','2 započinje pisanje; 1 započinje čitanje.'],['65532 = 0xFFFC','128 puta prenesi riječ. Sektor ima 256 bajtova.']],[170,335])
p('FILL zapisuje 127, 126, ... , 0. SUM čita sektor i sabira sve riječi: 127 × 128 / 2 = 8128. Time su testirani upis, čitanje, redoslijed prenosa i gostujuće petlje.')
sub('C. Provjeri da je zapis preživio reset')
p('Pritisni F12, zatim Enter. RAM i nove riječi su nestali, pa ponovo unesi DECIMAL i definiciju SUM iznad. Nemoj ponovo pozivati FILL.')
cmd('3000 65533 ! 1 65534 ! SUM .')
ok('Ponovo 8128. Rezultat dolazi iz datoteke diska, ne iz starog RAM-a.')

title(6,'Automatski test, problemi i završna lista')
sub('Automatski test u tri koraka')
d=Drawing(505,85)
for x,a,b in [(0,'Zatvori emulator','dugme X'),(175,'TESTIRAJ.bat','dvostruki klik'),(350,'Pročitaj kraj','mora pisati PASS')]:
    box(d,x,10,155,65,a,b)
    if x<350:arrow(d,x+155,43,x+174,43)
story.append(d)
p('Prozor testa prikazuje komande i rezultate te čeka da pritisneš tipku. Cijeli posljednji zapis ostaje u tests/last-run.txt. Ako piše FAIL, pročitaj poruku iznad. Nije dovoljno da se samo otvorio prozor.')
sub('Ako nešto ne odgovara očekivanju')
table([['Šta vidiš?','Šta provjeriti?'],['Nedostaje sveu16.exe','Raspakuj cijeli paket. Ne pokreći .bat direktno iz pregleda ZIP-a.'],['Cannot load boot.rom / disk.img','Provjeri da su datoteke uz EXE. Zatvori drugu instancu programa. Folder mora dopuštati pisanje.'],['Nema odmah ok nakon pozdrava','Pritisni Enter. Početni pozdrav ne ispisuje prompt prije prvog unosa.'],['Brojevi su 51 umjesto 81','Uključen je HEX. Unesi DECIMAL pa ponovi primjer.'],['?(-13)','Nepoznata riječ ili tipfeler. Provjeri razmake i riječi koje ovaj eFORTH podržava.'],['Tipke ne daju očekivani simbol','Klikni u emulator; koristi US raspored. Ne koristi lijepljenje teksta ili Caps Lock.'],['Status diska nije 0','Pošalji novu ispravnu komandu; provjeri sektor i broj prenesenih riječi.'],['Windows blokira novi program','To je blokada okruženja, ne Forth rezultat. Ne isključuj zaštitu; koristi odobreno okruženje za izgradnju/pokretanje.']],[175,330])
sub('Lista za ručnu evidenciju')
for t in ['Pozdrav OS-a i ok su vidljivi.','Rezultati 5, 81, 123, 256, 16 i 45 su tačni.','Segmenti se pojedinačno pale, svi se pale i gase.','KEY daje 97/65, a Backspace ispravlja unos.','ROM provjera daje E111 E111.','IRQ raste i program nastavlja normalno raditi.','Disk daje 8128 prije i poslije reseta, status je 0.','TESTIRAJ.bat završava oznakom PASS.']:
    p('☐ '+t)
p('Za odbranu pročitaj docs/ODBRANA.md. Za detaljno objašnjenje šta je urađeno, kako i zašto pročitaj docs/IZVJESTAJ.pdf.')

doc=SimpleDocTemplate(str(ROOT/'POCNI_OVDJE.pdf'),pagesize=(595.276,841.89),leftMargin=44,rightMargin=44,topMargin=50,bottomMargin=45,title='SVEU16 - nacrtani vodič za pokretanje i ručnu provjeru',author='Projekt SVEU16')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(ROOT/'POCNI_OVDJE.pdf')
