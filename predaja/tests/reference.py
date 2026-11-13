"""Independent Python assembler and slow SVEU16 model for cross-checks.
Not used by the C application. Run from predaja: python tests/reference.py
"""
import re,struct,pathlib,json
OPS='LOD ADD SUB AND ORA XOR SHR MUL STO MIF GTU GTS LTU LTS EQU MAJ WRD ORG TXT CON'.split()
def assemble(path):
    rows=[];syms={};memory={};pc=0
    def num(s):
        if s in syms:return syms[s]
        return int(s[1:],16) if s.startswith('$') else int(s)
    for lineno,line in enumerate(pathlib.Path(path).read_text().splitlines(),1):
        quote=False
        for i,ch in enumerate(line):
            if ch=='"':quote=not quote
            if ch==';' and not quote:line=line[:i];break
        line=line.strip()
        if not line:continue
        parts=re.split(r'[\s,:]+',line,maxsplit=1);label=None
        if parts[0] not in OPS:
            label=parts[0];line=parts[1] if len(parts)>1 else ''
        if not line:
            if label in syms:raise ValueError((lineno,'duplicate',label))
            syms[label]=pc;continue
        parts=line.split(None,1);op=parts[0];args=parts[1].strip() if len(parts)>1 else ''
        if op not in OPS:raise ValueError((lineno,op))
        if label:
            if label in syms:raise ValueError((lineno,'duplicate',label))
            syms[label]=num(args)&65535 if op=='CON' else pc
        if op=='CON':continue
        if op=='ORG':pc=num(args);continue
        rows.append((pc,op,args,lineno))
        pc+=len(args)-2 if op=='TXT' else 1
    for pc,op,args,ln in rows:
        if op=='TXT':
            assert args[0]==args[-1]=='"',(ln,args)
            words=list(map(ord,args[1:-1]))
        elif op=='WRD':words=[num(args)&65535]
        else:
            rr=re.split(r'[\s,]+',args)
            assert len(rr)==3,(ln,args)
            regs=[int(r[1:]) for r in rr];assert all(0<=r<16 for r in regs)
            words=[OPS.index(op)*4096+regs[0]*256+regs[1]*16+regs[2]]
        for i,w in enumerate(words):
            assert pc+i not in memory,(ln,'overlap');memory[pc+i]=w
    lo=min(memory);hi=max(memory)+1
    return struct.pack('<'+'H'*(hi-lo),*(memory.get(a,0) for a in range(lo,hi))),syms,lo

class Reference:
    def __init__(self,rom,disk,syms):
        self.m=[0]*65536;self.m[:1024]=struct.unpack('<1024H',rom)
        self.r=[0]*16;self.disk=bytearray(disk);self.sector=0;self.command=0;self.pos=0
        self.keys=[];self.cycles=0;self.irqs=0;self.left=160000;self.out=[];self.syms=syms
    def read(self,a):
        if a==65535:return self.keys.pop(0) if self.keys else 0
        if a==65532:
            assert self.command==1 and self.pos<128
            i=self.sector*256+self.pos*2;self.pos+=1
            return self.disk[i]|self.disk[i+1]<<8
        return self.m[a]
    def write(self,a,x):
        if a==65533:self.sector=x
        elif a==65534:
            self.command=x;self.pos=0
            if not x:self.sector=0
        elif a==65532:
            assert self.command==2 and self.pos<128
            i=self.sector*256+self.pos*2;self.pos+=1;self.disk[i:i+2]=struct.pack('<H',x)
        elif a>=1024 and a<65532:self.m[a]=x
    def run(self,n):
        r=self.r;m=self.m
        for _ in range(n):
            if self.left==0:
                self.left=160000;self.irqs+=1;r[14]=(r[15]+1)&65535;r[15]=r[13]
            else:
                pc=r[15]
                if pc==self.syms['TXST1']:self.out.append(chr(m[r[2]]&127))
                ir=self.read(pc);op=ir>>12;d=(ir>>8)&15;s1=(ir>>4)&15;s2=ir&15
                r[15]=(pc+1)&65535;a=r[s1];b=r[s2]
                if op==0:
                    r[d]=self.read(b)
                    if s2==15 and d!=15:r[15]=(r[15]+1)&65535
                elif op==1:r[d]=(a+b)&65535
                elif op==2:r[d]=(a-b)&65535
                elif op==3:r[d]=a&b
                elif op==4:r[d]=a|b
                elif op==5:r[d]=a^b
                elif op==6:
                    n=b&15;kind=(b>>4)&3
                    if kind==0:r[d]=((a if a<32768 else a-65536)>>n)&65535
                    elif kind==1:r[d]=a>>n
                    elif kind==2:r[d]=((a>>n)|(a<<(16-n)))&65535
                    else:r[d]=(a<<n)&65535
                elif op==7:r[d]=a*b&65535
                elif op==8:
                    self.write(b,a);r[d]=a
                    if s2==15 and d!=15:r[15]=(r[15]+1)&65535
                elif op==9:
                    if a:r[d]=b
                elif op==10:r[d]=int(a>b)
                elif op==11:r[d]=int((a^32768)>(b^32768))
                elif op==12:r[d]=int(a<b)
                elif op==13:r[d]=int((a^32768)<(b^32768))
                elif op==14:r[d]=int(a==b)
                else:r[d]=a;r[15]=b
            self.cycles+=1;self.left-=1
    def command_text(self,text):
        table=self.syms['KEYTABLE']
        mapping=self.m[table:table+256]
        for ch in text:
            c=13 if ch=='\n' else ord(ch);k=mapping.index(c)
            self.keys+=([42] if k>=128 else [])+[k&127,(k&127)|128]+([170] if k>=128 else [])
            self.run(12000)
        self.run(150000)

def main():
    rom,rs,_=assemble('firmware/boot.asm');kernel,syms,base=assemble('firmware/forth.asm')
    assert len(rom)==2048 and base==0x3000 and len(kernel)<=32768
    disk=kernel+bytes(1048576-len(kernel)) # reference image in memory; never overwrite the working disk
    vm=Reference(rom,disk,syms);vm.run(500000)
    text='DECIMAL\n2 3 + .\n: KVADRAT DUP * ;\n9 KVADRAT .\n1 8 LSHIFT .\n256 4 RSHIFT .\n'
    vm.command_text(text)
    output=''.join(vm.out);print(output)
    assert '5 ' in output and '81 ' in output and '256 ' in output and '16 ' in output,output
    assert vm.irqs>0 and vm.m[:1024]==list(struct.unpack('<1024H',rom))
    result={'model':'independent Python reference, not the C executable','cycles':vm.cycles,'interrupts':vm.irqs,'kernel_bytes':len(kernel),'output':output}
    pathlib.Path('tests/reference-result.json').write_text(json.dumps(result,indent=2))
    print('REFERENCE PASS',result['cycles'],result['interrupts'])
if __name__=='__main__':main()
