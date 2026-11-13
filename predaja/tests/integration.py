"""Cross-check the C-built firmware and exercise the actual Windows executable.
Uses a temporary disk, so test writes never touch the user's working disk.
"""
from pathlib import Path
import subprocess,tempfile,shutil,json,time
from reference import assemble,Reference
ROOT=Path(__file__).resolve().parents[1]
def main():
    import os
    os.chdir(ROOT)
    for source,binary in [('boot.asm','boot.rom'),('forth.asm','forth.bin')]:
        blob,_,_=assemble(ROOT/'firmware'/source)
        assert blob==(ROOT/binary).read_bytes(),f'C/Python assembler disagreement: {source}'
    results=[]
    with tempfile.TemporaryDirectory(prefix='sveu16-test-') as folder:
        work=Path(folder)
        for name in ['boot.rom','forth.map']:shutil.copyfile(ROOT/name,work/name)
        shutil.copyfile(ROOT/'disk.factory.img',work/'disk.img')
        def run(name,text,expected):
            (work/'input.fth').write_text(text,encoding='ascii')
            start=time.perf_counter()
            p=subprocess.run([str(ROOT/'sveu16.exe'),'--batch','input.fth'],cwd=work,capture_output=True,text=True,timeout=60)
            out=p.stdout.split('--- VIDEO MEMORY')[0]
            assert p.returncode==0 and '?(-' not in out,(name,p.stderr,out)
            for item in expected:assert item in out,(name,item,out)
            results.append({'test':name,'passed':True,'seconds':round(time.perf_counter()-start,3)})
            (ROOT/'tests'/f'{name}-result.txt').write_text(p.stdout)
        run('smoke',(ROOT/'tests/smoke.fth').read_text(),['2 3 + . 5 ', '9 KVADRAT . 81 ', '1 8 LSHIFT . 256 ', '256 4 RSHIFT . 16 ', '/MOD . . 3 1 ', 'BROJ @ . 123 ', 'SUMA . 45 '])
        # Sector 3000 is outside the OS image. The guest performs all port I/O.
        disk='''DECIMAL
: FILL 128 BEGIN DUP WHILE 1 - DUP 65532 ! REPEAT DROP ;
: SUM 0 128 BEGIN DUP WHILE 1 - SWAP 65532 @ + SWAP REPEAT DROP ;
3000 65533 ! 2 65534 ! FILL
3000 65533 ! 1 65534 ! SUM .
65534 @ .
'''
        run('disk',disk,['SUM . 8128 ','65534 @ . 0 '])
        raw=(work/'disk.img').read_bytes()[3000*256:3001*256]
        import struct
        assert list(struct.unpack('<128H',raw))==list(range(127,-1,-1))
        run('disk-persist','DECIMAL\n: SUM 0 128 BEGIN DUP WHILE 1 - SWAP 65532 @ + SWAP REPEAT DROP ;\n3000 65533 ! 1 65534 ! SUM .\n',['SUM . 8128 '])
        run('scroll','DECIMAL\n'+''.join(f'{i} .\n' for i in range(60))+'12\b3 .\n',['59 . 59 ','3 . 13 '])
    rom=ROOT.joinpath('boot.rom').read_bytes();kernel,syms,_=assemble(ROOT/'firmware/forth.asm')
    model=Reference(rom,ROOT.joinpath('disk.factory.img').read_bytes(),syms)
    model.run(500000);model.command_text('DECIMAL\n2 3 + .\n: KVADRAT DUP * ;\n9 KVADRAT .\n')
    assert '9 KVADRAT . 81 ' in ''.join(model.out)
    assert model.m[:1024]==list(struct.unpack('<1024H',rom))
    assert model.irqs>0
    results.append({'test':'independent-reference-boot-and-forth','passed':True,'interrupts':model.irqs})
    (ROOT/'tests/integration-result.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
