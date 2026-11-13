/* Two-pass SVEU16 assembler. Output: explicit little-endian words, no headers. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdint.h>
typedef struct {char name[64];unsigned value;} Symbol;
static Symbol syms[8192];static unsigned ns,pc,lo=65536,hi;static uint16_t mem[65536];
static unsigned char used[65536];static int line,pass;
static const char *ops[]={"LOD","ADD","SUB","AND","ORA","XOR","SHR","MUL","STO","MIF","GTU","GTS","LTU","LTS","EQU","MAJ","WRD","ORG","TXT","CON"};
static void fail(const char *s){fprintf(stderr,"line %d: %s\n",line,s);exit(1);}
static int opnum(const char *s){for(int i=0;i<20;i++)if(!strcmp(s,ops[i]))return i;return -1;}
static unsigned value(const char *s){
    for(unsigned i=0;i<ns;i++)if(!strcmp(s,syms[i].name))return syms[i].value;
    char *end;long n=strtol(s[0]=='$'?s+1:s,&end,s[0]=='$'?16:10);
    if(!*s||*end||n< -32768||n>65535)fail("undefined symbol or invalid 16-bit value");
    return (unsigned)n&65535;
}
static unsigned reg(const char *s){char *end;long n=strtol(s+1,&end,10);if(*s!='R'||*end||n<0||n>15)fail("invalid register");return (unsigned)n;}
static void emit(unsigned x){
    if(pc>=65536)fail("address overflow");
    if(pass==2){if(used[pc])fail("overlapping output");used[pc]=1;mem[pc]=(uint16_t)x;}
    if(pc<lo)lo=pc;if(pc+1>hi)hi=pc+1;pc++;
}
int main(int argc,char **argv){
    if(argc!=4){fprintf(stderr,"usage: asm input.asm output.bin output.map\n");return 1;}
    for(pass=1;pass<=2;pass++){
        FILE *f=fopen(argv[1],"r");if(!f){perror(argv[1]);return 1;}
        char buf[4096];pc=0;line=0;
        while(fgets(buf,sizeof buf,f)){
            line++;int quote=0;for(char *p=buf;*p;p++){if(*p=='\"')quote=!quote;if(*p==';'&&!quote){*p=0;break;}}
            char *p=buf;while(isspace((unsigned char)*p))p++;if(!*p)continue;
            char *tok=strtok(p," ,:\t\r\n");int op=opnum(tok);char label[64]={0};
            if(op<0){if(strlen(tok)>=sizeof label)fail("label too long");strcpy(label,tok);tok=strtok(NULL," ,:\t\r\n");op=tok?opnum(tok):-1;if(tok&&op<0)fail("unknown opcode");}
            char *args[3]={NULL,NULL,NULL};char *txt=NULL;
            if(op==18){txt=strtok(NULL,"");if(!txt)fail("missing text");while(isspace((unsigned char)*txt))txt++;size_t len=strlen(txt);while(len&&isspace((unsigned char)txt[len-1]))txt[--len]=0;if(len<2||txt[0]!='\"'||txt[len-1]!='\"')fail("invalid TXT");txt[len-1]=0;txt++;}
            else if(op>=0){for(int i=0;i<(op<16?3:1);i++){args[i]=strtok(NULL," ,:\t\r\n");if(!args[i])fail("missing operand");}if(strtok(NULL," ,:\t\r\n"))fail("extra operand");}
            if(*label&&pass==1){for(unsigned i=0;i<ns;i++)if(!strcmp(label,syms[i].name))fail("duplicate label");if(ns==8192)fail("symbol table full");unsigned val=op==19?value(args[0]):pc;strcpy(syms[ns].name,label);syms[ns].value=val;ns++;}
            if(op<0||op==19)continue;
            if(op==17){pc=value(args[0]);continue;}
            if(op==18){while(*txt)emit((unsigned char)*txt++);continue;}
            if(op==16){emit(pass==2?value(args[0]):0);continue;}
            emit(((unsigned)op<<12)|(reg(args[0])<<8)|(reg(args[1])<<4)|reg(args[2]));
        }if(ferror(f))fail("input read failed");fclose(f);
    }
    FILE *f=fopen(argv[2],"wb");if(!f){perror(argv[2]);return 1;}
    for(unsigned i=lo;i<hi;i++){if(fputc(mem[i]&255,f)==EOF||fputc(mem[i]>>8,f)==EOF)fail("output write failed");}if(fclose(f))fail("output close failed");
    f=fopen(argv[3],"w");if(!f){perror(argv[3]);return 1;}for(unsigned i=0;i<ns;i++)fprintf(f,"%s %04X\n",syms[i].name,syms[i].value);fclose(f);
    printf("%s: base=%04X words=%u end=%04X\n",argv[1],lo,hi-lo,hi);return 0;
}
