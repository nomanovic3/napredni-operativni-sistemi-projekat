/* SVEU16: direct threaded, address-aligned decoded instruction cache.
 * GNU C labels-as-values are supported by GCC and Clang. No native JIT code.
 */
#include "vm.h"
#include <string.h>

int vm_init(VM *v,const char *rom,const char *disk) {
    memset(v,0,sizeof(*v)); v->until_irq=IRQ_PERIOD;
    FILE *f=fopen(rom,"rb"); if(!f) return 0;
    for(unsigned i=0;i<1024;i++) {
        int lo=fgetc(f),hi=fgetc(f);
        if(lo==EOF||hi==EOF){fclose(f);return 0;}
        v->mem[i]=(uint16_t)(lo|(hi<<8));
    }
    int extra=fgetc(f); fclose(f); if(extra!=EOF) return 0;
    v->disk=fopen(disk,"r+b"); if(!v->disk) return 0;
    if(fseek(v->disk,0,SEEK_END)||ftell(v->disk)!=1048576L){vm_close(v);return 0;}
    v->video_dirty=1; return 1;
}
void vm_close(VM *v){if(v->disk){fclose(v->disk);v->disk=NULL;}}
int vm_key(VM *v,uint16_t scan){
    unsigned next=(v->key_tail+1)%1024;
    if(next==v->key_head) return 0;
    v->keys[v->key_tail]=scan;v->key_tail=next;return 1;
}
uint16_t vm_read(VM *v,uint16_t addr){
    if(addr==0xFFFF){
        if(v->key_head==v->key_tail)return 0;
        uint16_t k=v->keys[v->key_head];v->key_head=(v->key_head+1)%1024;return k;
    }
    if(addr==0xFFFE)return v->status; /* documented status extension */
    if(addr==0xFFFD)return v->sector;
    if(addr==0xFFFC){
        if(v->command!=1||v->disk_pos>=128||v->status){v->status=2;return 0;}
        unsigned n=2*v->disk_pos++;
        return (uint16_t)(v->buffer[n]|((uint16_t)v->buffer[n+1]<<8));
    }
    return v->mem[addr];
}
void vm_write(VM *v,uint16_t addr,uint16_t value){
    if(addr==0xFFFF)return;
    if(addr==0xFFFD){v->sector=value;return;}
    if(addr==0xFFFE){
        v->command=value;v->disk_pos=0;v->status=0;
        if(!value){v->sector=0;memset(v->buffer,0,256);return;}
        if(value>2||v->sector>=4096||!v->disk){v->status=1;return;}
        if(fseek(v->disk,(long)v->sector*256,SEEK_SET)){v->status=3;return;}
        if(value==1&&fread(v->buffer,1,256,v->disk)!=256)v->status=3;
        if(value==2)memset(v->buffer,0,256);
        return;
    }
    if(addr==0xFFFC){
        if(v->command!=2||v->disk_pos>=128||v->status){v->status=2;return;}
        unsigned n=2*v->disk_pos++;v->buffer[n]=(uint8_t)value;v->buffer[n+1]=(uint8_t)(value>>8);
        if(v->disk_pos==128){
            if(fseek(v->disk,(long)v->sector*256,SEEK_SET)||fwrite(v->buffer,1,256,v->disk)!=256||fflush(v->disk))v->status=3;
        }return;
    }
    if(addr<1024)return; /* ROM protection */
    v->mem[addr]=value;v->decoded[addr].handler=NULL; /* self modifying code */
    if(addr>=VIDEO_BASE&&addr<VIDEO_BASE+VIDEO_WORDS)v->video_dirty=1;
}

void vm_run(VM *v,uint32_t budget){
    static void *const ops[]={&&LOD,&&ADD,&&SUB,&&AND,&&ORA,&&XOR,&&SHR,&&MUL,
        &&STO,&&MIF,&&GTU,&&GTS,&&LTU,&&LTS,&&EQU,&&MAJ};
    Decoded *p;uint16_t a,b,ir;unsigned d,src2,n,kind;
    if(!budget)return;
NEXT:
    /* An IRQ replaces the fetched instruction with FEFD, exactly as the PDF.
     * Handler returns to R14-1 so that the displaced instruction is retried. */
    if(!v->until_irq){
        v->until_irq=IRQ_PERIOD;v->interrupts++;
        v->r[14]=(uint16_t)(v->r[15]+1);v->r[15]=v->r[13];
        goto DONE;
    }
    if(v->trace&&v->r[15]==v->trace_pc)fputc(v->mem[v->r[2]]&127,v->trace);
    p=&v->decoded[v->r[15]];
    if(!p->handler||v->r[15]>=0xFFFC){
        ir=vm_read(v,v->r[15]);p->d=(ir>>8)&15;p->a=(ir>>4)&15;p->b=ir&15;p->handler=ops[ir>>12];
    }
    d=p->d;src2=p->b;
    v->r[15]++;a=v->r[p->a];b=v->r[src2]; /* capture both before writeback */
    goto *p->handler;
LOD: v->r[d]=vm_read(v,b);if(src2==15&&d!=15)v->r[15]++;goto DONE;
ADD: v->r[d]=(uint16_t)(a+b);goto DONE;
SUB: v->r[d]=(uint16_t)(a-b);goto DONE;
AND: v->r[d]=a&b;goto DONE;
ORA: v->r[d]=a|b;goto DONE;
XOR: v->r[d]=a^b;goto DONE;
SHR:
    n=b&15;kind=(b>>4)&3;
    if(kind==0)v->r[d]=(uint16_t)((a>>n)|((a&0x8000)&&n?(0xFFFFu<<(16-n)):0));
    if(kind==1)v->r[d]=(uint16_t)(a>>n);
    if(kind==2)v->r[d]=n?(uint16_t)((a>>n)|((uint32_t)a<<(16-n))):a;
    if(kind==3)v->r[d]=(uint16_t)((uint32_t)a<<n);
    goto DONE;
MUL: v->r[d]=(uint16_t)((uint32_t)a*b);goto DONE;
STO: vm_write(v,b,a);v->r[d]=a;if(src2==15&&d!=15)v->r[15]++;goto DONE;
MIF: if(a)v->r[d]=b;goto DONE;
GTU: v->r[d]=a>b;goto DONE;
GTS: v->r[d]=(int16_t)a>(int16_t)b;goto DONE;
LTU: v->r[d]=a<b;goto DONE;
LTS: v->r[d]=(int16_t)a<(int16_t)b;goto DONE;
EQU: v->r[d]=a==b;goto DONE;
MAJ: v->r[d]=a;v->r[15]=b;goto DONE;
DONE:
    v->cycles++;v->until_irq--;
    if(--budget)goto NEXT;
}
