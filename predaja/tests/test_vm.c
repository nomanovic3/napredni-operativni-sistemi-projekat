#include "../src/vm.h"
#include <stdlib.h>
#include <string.h>
static VM v;
static unsigned checks;
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#x);exit(1);}}while(0)
static uint32_t random_state=0x13579BDF;
static uint16_t rnd(void){random_state^=random_state<<13;random_state^=random_state>>17;random_state^=random_state<<5;return (uint16_t)random_state;}
static int signed16(unsigned x){return x<32768?(int)x:(int)x-65536;}
/* Spec oracle: result and next PC computed from input snapshots, independently
 * of the production computed-goto dispatcher and decoded cache. */
static void cpu_vectors(void){
    for(unsigned ir=0;ir<65536;ir++){
        uint16_t expected[16];unsigned op=ir>>12,d=(ir>>8)&15,s1=(ir>>4)&15,s2=ir&15;
        for(int j=0;j<16;j++)v.r[j]=rnd();
        v.r[15]=0x400;
        if((op==0||op==8)&&s2!=15)v.r[s2]=(uint16_t)(0x600+(rnd()%0x1000));
        memcpy(expected,v.r,sizeof expected);expected[15]=0x401;
        unsigned a=expected[s1],b=expected[s2],result=0;int writeback=1;
        v.mem[0x400]=(uint16_t)ir;v.decoded[0x400].handler=NULL;
        if(op==0||op==8)v.mem[b]=rnd();
        switch(op){
        case 0:result=v.mem[b];break;
        case 1:result=a+b;break;case 2:result=a-b;break;
        case 3:result=a&b;break;case 4:result=a|b;break;case 5:result=a^b;break;
        case 6:{unsigned n=b%16,k=(b/16)%4;
            if(k==0){int q=signed16(a);for(unsigned j=0;j<n;j++)q=q<0?(q-1)/2:q/2;result=(unsigned)q;}
            if(k==1)result=a/(1u<<n);
            if(k==2){result=a;for(unsigned j=0;j<n;j++)result=(result/2)|((result%2)*32768);}
            if(k==3)result=a*(1u<<n);break;}
        case 7:result=a*b;break;case 8:result=a;break;
        case 9:result=b;writeback=a!=0;break;
        case 10:result=a>b;break;case 11:result=signed16(a)>signed16(b);break;
        case 12:result=a<b;break;case 13:result=signed16(a)<signed16(b);break;
        case 14:result=a==b;break;case 15:result=a;break;
        }
        if(writeback)expected[d]=(uint16_t)result;
        if(op==15)expected[15]=(uint16_t)b;
        if((op==0||op==8)&&s2==15&&d!=15)expected[15]=0x402;
        v.until_irq=100;vm_run(&v,1);
        CHECK(!memcmp(expected,v.r,sizeof expected));
        if(op==8)CHECK(v.mem[b]==a);
    }
    puts("PASS: all 65536 instruction encodings (register aliasing and PC included)");
}
static void devices(void){
    memset(&v,0,sizeof v);v.until_irq=IRQ_PERIOD;
    v.mem[3]=123;vm_write(&v,3,456);CHECK(v.mem[3]==123);
    vm_write(&v,VIDEO_BASE,65535);CHECK(v.video_dirty&&v.mem[VIDEO_BASE]==65535);
    CHECK(vm_key(&v,0x1E));CHECK(vm_key(&v,0x9E));CHECK(vm_read(&v,65535)==0x1E);CHECK(vm_read(&v,65535)==0x9E);CHECK(!vm_read(&v,65535));
    for(unsigned i=0;i<1023;i++)CHECK(vm_key(&v,1));CHECK(!vm_key(&v,2));
    v.disk=tmpfile();CHECK(v.disk!=NULL);unsigned char zeros[256]={0};for(int i=0;i<4096;i++)CHECK(fwrite(zeros,1,256,v.disk)==256);
    vm_write(&v,65533,300);vm_write(&v,65534,2);
    for(unsigned i=0;i<128;i++)vm_write(&v,65532,(uint16_t)(0xA500+i));CHECK(!v.status);
    vm_write(&v,65534,1);for(unsigned i=0;i<128;i++)CHECK(vm_read(&v,65532)==0xA500+i);
    CHECK(vm_read(&v,65532)==0&&v.status==2);
    vm_write(&v,65534,0);CHECK(!v.status&&!v.sector&&!v.command);
    vm_write(&v,65533,4096);vm_write(&v,65534,1);CHECK(v.status==1);
    vm_write(&v,65534,99);CHECK(v.status==1);
    vm_write(&v,65533,301);vm_write(&v,65534,2);vm_write(&v,65532,999);vm_write(&v,65534,0);
    vm_write(&v,65533,301);vm_write(&v,65534,1);CHECK(vm_read(&v,65532)==0); /* aborted partial sector */
    vm_close(&v);
    puts("PASS: ROM, video, scan FIFO, disk round-trip, reset, bounds, partial transfer");
}
static void cache_irq(void){
    memset(&v,0,sizeof v);v.until_irq=IRQ_PERIOD;v.r[15]=0x400;v.r[1]=1;
    vm_write(&v,0x400,0x1221);vm_run(&v,1);CHECK(v.r[2]==1);
    v.r[15]=0x400;vm_write(&v,0x400,0x2221);vm_run(&v,1);CHECK(v.r[2]==0);
    v.r[15]=0x400;v.r[13]=0x500;vm_write(&v,0x500,0x2FE1);v.until_irq=0;
    vm_run(&v,1);CHECK(v.r[15]==0x500&&v.r[14]==0x401&&v.interrupts==1);
    vm_run(&v,1);CHECK(v.r[15]==0x400);
    vm_write(&v,0x400,0x4FFF); /* PC+1 flow is not a loop; use ORA PC,R2,R2. */
    v.r[2]=0x400;vm_write(&v,0x400,0x4F22);
    v.until_irq=IRQ_PERIOD;v.interrupts=0;vm_run(&v,IRQ_PERIOD);CHECK(v.interrupts==0);
    vm_run(&v,1);CHECK(v.interrupts==1);
    vm_run(&v,IRQ_PERIOD);CHECK(v.interrupts==2);
    puts("PASS: self-modifying code, interrupt injection/retry and exact 160000-cycle period");
}
int main(void){cpu_vectors();devices();cache_irq();printf("ALL PASS: %u assertions\n",checks);return 0;}
