"""Optional documentation build: Python + reportlab. Does not build the emulator."""
from pathlib import Path
from xml.sax.saxutils import escape
import re
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,Table,TableStyle,Image,Preformatted,KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.graphics.shapes import Drawing,Line,String
HERE=Path(__file__).resolve().parent
for name,file in [('Body','arial.ttf'),('Bold','arialbd.ttf'),('Code','consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
NAVY=colors.HexColor('#102C3A');GREEN=colors.HexColor('#147A62');GRAY=colors.HexColor('#536570')
body=ParagraphStyle('body',fontName='Body',fontSize=10,leading=14.5,spaceAfter=8,textColor=NAVY)
h1=ParagraphStyle('h1',parent=body,fontName='Bold',fontSize=17,leading=21,spaceBefore=16,spaceAfter=10,keepWithNext=True)
small=ParagraphStyle('small',parent=body,fontSize=8.5,leading=12,textColor=GRAY)
cell=ParagraphStyle('cell',parent=body,fontSize=8.5,leading=11,spaceAfter=0)
code=ParagraphStyle('code',fontName='Code',fontSize=8,leading=11,spaceBefore=4,spaceAfter=10,backColor=colors.HexColor('#EDF3F4'),borderPadding=8)
def inline(text):
    text=escape(text)
    text=re.sub(r'`([^`]+)`',r'<font name="Code">\1</font>',text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',text)
    return text
def header(c,doc):
    c.saveState();w,h=A4
    if doc.page>1:
        c.setStrokeColor(GREEN);c.setLineWidth(.7);c.line(44,h-38,w-44,h-38)
        c.setFont('Bold',8);c.setFillColor(NAVY);c.drawString(44,h-29,'SVEU16 / SISTEMSKA VIRTUALNA MAŠINA')
    c.setFont('Body',8);c.setFillColor(GRAY);c.drawString(44,27,'Tehnički izvještaj • 12.11.2026.');c.drawRightString(w-44,27,str(doc.page));c.restoreState()
class Doc(BaseDocTemplate):
    def afterFlowable(self,f):
        if isinstance(f,Paragraph) and f.style.name=='h1':
            title=f.getPlainText();key='h-'+str(self.seq.nextf('heading'))
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(title,key,0)
            self.notify('TOCEntry',(0,title,self.page,key))
    def beforeDocument(self):self.seq.reset('heading')

def segments_diagram():
    d=Drawing(440,210)
    points=[(0,16,4,16),(4,16,8,16),(8,16,8,8),(8,8,8,0),(8,0,4,0),(4,0,0,0),(0,0,0,8),(0,8,0,16),(0,8,4,8),(4,8,8,8),(0,16,4,8),(4,16,4,8),(8,16,4,8),(0,0,4,8),(4,8,4,0),(4,8,8,0)]
    offsets={0:(0,10),1:(0,10),2:(14,0),3:(14,0),4:(0,-13),5:(0,-13),6:(-14,0),7:(-14,0),8:(0,9),9:(0,9),10:(-8,0),11:(11,0),12:(8,0),13:(-8,0),14:(11,0),15:(8,0)}
    for i,(x1,y1,x2,y2) in enumerate(points):
        x1=95+x1*10;x2=95+x2*10;y1=22+y1*10;y2=22+y2*10
        d.add(Line(x1,y1,x2,y2,strokeColor=GREEN,strokeWidth=3))
        dx,dy=offsets[i];d.add(String((x1+x2)/2+dx,(y1+y2)/2+dy,str(i),fontName='Bold',fontSize=9,textAnchor='middle',fillColor=NAVY))
    d.add(String(230,130,'Jedna riječ = 16 nezavisnih bitova',fontName='Bold',fontSize=10,fillColor=NAVY))
    d.add(String(230,110,'1: segment svijetli',fontName='Body',fontSize=10,fillColor=NAVY))
    d.add(String(230,92,'0: segment je ugašen',fontName='Body',fontSize=10,fillColor=NAVY))
    return d

def main():
    story=[Spacer(1,20),Paragraph('NAPREDNI OPERATIVNI SISTEMI',ParagraphStyle('eyebrow',parent=small,textColor=GREEN,fontName='Bold',fontSize=11)),Spacer(1,18),Paragraph('Sistemska virtualna<br/>mašina SVEU16',ParagraphStyle('title',parent=h1,fontSize=30,leading=35)),Spacer(1,10),Paragraph('Implementacija u C-u za Windows<br/>ROM boot loader • eFORTH sa diska • 16-segmentni ekran',body),Spacer(1,18)]
    from PIL import Image as PILImage
    with PILImage.open(HERE/'emulator.png') as screen: iw,ih=screen.size
    story.append(Image(str(HERE/'emulator.png'),width=505,height=505*ih/iw))
    story += [Spacer(1,14),Paragraph('Izvršavanje stvarnih gostujućih instrukcija, dokumentovan raspored uređaja i ponovljive provjere CPU-a i operativnog sistema.',body),Paragraph('Prilozi: C izvori, asemblerski firmware, Windows izvršne datoteke, disk slike, testovi i priprema za odbranu.',small),PageBreak()]
    story.append(Paragraph('Sadržaj',ParagraphStyle('toc-title',parent=h1)))
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc',fontName='Body',fontSize=10,leading=15,spaceBefore=7,leftIndent=0,firstLineIndent=0)]
    story.extend([toc,Spacer(1,20),Paragraph('Izvještaj opisuje implementirano i provjereno ponašanje. Konvencije koje nisu bile precizirane postavkom odvojeno su navedene, kao i ograničenja okruženja i testiranja.',small),PageBreak()])
    lines=(HERE/'OBJASNJENJE.md').read_text(encoding='utf-8').splitlines();i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip() or line.startswith('# '):i+=1;continue
        if line.startswith('## '):
            if line.startswith('## 14.'):story.append(PageBreak())
            story.append(Paragraph(inline(line[3:]),h1));i+=1
            if line.startswith('## 11.'):story.append(segments_diagram())
            continue
        if line.startswith('```'):
            i+=1;block=[]
            while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
            story.append(Preformatted('\n'.join(block),code,maxLineLength=92));i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                parts=[p.strip() for p in lines[i].strip('|').split('|')]
                if not all(re.fullmatch(r'[- :]+',p) for p in parts):rows.append([Paragraph(inline(p),cell) for p in parts])
                i+=1
            count=len(rows[0]);widths=[105,400] if count==2 else [60,115,330]
            table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DAEAE5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.7,GREEN),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#D4DFE2'))]))
            story.extend([KeepTogether([table]),Spacer(1,10)]);continue
        para=[]
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','```')):para.append(lines[i]);i+=1
        story.append(Paragraph(inline(' '.join(para)),body))
    story.append(Paragraph('Izvori',h1))
    for p in ['Dostavljena postavka: nosslika.png; nastavni paket sveu16.zip.','S. Ribić, K. Hodžić: Educational Processor with Single-cycle Instructions SVEU16, dostavljeni PDF.','Originalni eFORTH iz nastavne arhive; autorski navod Bill Muench 1989–1999 sačuvan je u izvoru.','GNU GCC dokumentacija: Labels as Values, gcc.gnu.org/onlinedocs/gcc/Labels-as-Values.html.','Alati: službeni LLVM 19.1.7 i LLVM-MinGW Windows biblioteke. Detaljno porijeklo: IZVORI.md.']:
        story.append(Paragraph(inline(p),small))
    output=HERE/'IZVJESTAJ.pdf'
    doc=Doc(str(output),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=52,bottomMargin=45,title='Sistemska virtualna mašina SVEU16 - tehnički izvještaj',author='Projekt SVEU16')
    doc.addPageTemplates(PageTemplate(id='main',frames=[Frame(44,45,507,745,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=header))
    doc.multiBuild(story)
    print(output)
if __name__=='__main__':main()
