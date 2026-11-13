#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdlib.h>
#include <string.h>
#include "vm.h"
#include "font.h"
#include "keymap.h"
static VM machine;
static LARGE_INTEGER frequency,last;
static double remainder;
static uint64_t last_paint;
static uint16_t symbol(const char *name){
    FILE *f=fopen("forth.map","r");char s[128];unsigned x;if(!f)return 0;
    while(fscanf(f,"%127s %x",s,&x)==2)if(!strcmp(s,name)){fclose(f);return (uint16_t)x;}
    fclose(f);return 0;
}
static void dump_screen(const VM *v){
    for(unsigned y=0;y<25;y++){
        for(unsigned x=0;x<80;x++){
            uint16_t mask=v->mem[VIDEO_BASE+y*80+x];char c='?';
            if(!mask)c=' ';else for(int k=32;k<96;k++)if(font16[k]==mask){c=(char)k;break;}
            putchar(c);
        }putchar('\n');
    }
}
/* Coordinates of all sixteen independent physical LED segments. */
static const int segments[16][4]={
 {1,0,5,0},{5,0,9,0},{9,0,9,8},{9,8,9,16},
 {9,16,5,16},{5,16,1,16},{1,16,1,8},{1,8,1,0},
 {1,8,5,8},{5,8,9,8},{1,0,5,8},{5,0,5,8},
 {9,0,5,8},{1,16,5,8},{5,8,5,16},{5,8,9,16}};
static void paint(HWND hwnd){
    PAINTSTRUCT ps;HDC dc=BeginPaint(hwnd,&ps);RECT rc;GetClientRect(hwnd,&rc);
    HDC back=CreateCompatibleDC(dc);HBITMAP bmp=CreateCompatibleBitmap(dc,rc.right>0?rc.right:1,rc.bottom>0?rc.bottom:1);
    HGDIOBJ oldbmp=SelectObject(back,bmp);HBRUSH bg=CreateSolidBrush(RGB(8,17,23));FillRect(back,&rc,bg);DeleteObject(bg);
    double cw=(rc.right-20)/80.0,ch=(rc.bottom-48)/25.0;if(cw<1)cw=1;if(ch<1)ch=1;
    HPEN on=CreatePen(PS_SOLID,2,RGB(87,239,183)),off=CreatePen(PS_SOLID,1,RGB(20,43,46));HGDIOBJ oldpen=SelectObject(back,on);
    for(unsigned cell=0;cell<2000;cell++){
        uint16_t mask=machine.mem[VIDEO_BASE+cell];if(!mask)continue;
        double x=10+(cell%80)*cw,y=10+(cell/80)*ch;
        for(unsigned bit=0;bit<16;bit++){
            SelectObject(back,(mask&(1u<<bit))?on:off);
            MoveToEx(back,(int)(x+segments[bit][0]*cw/12),(int)(y+segments[bit][1]*ch/19),NULL);
            LineTo(back,(int)(x+segments[bit][2]*cw/12),(int)(y+segments[bit][3]*ch/19));
        }
    }
    SelectObject(back,oldpen);DeleteObject(on);DeleteObject(off);
    SetBkMode(back,TRANSPARENT);SetTextColor(back,RGB(180,200,210));
    char status[220];snprintf(status,sizeof status,"SVEU16 | 8 MHz | IRQ 20 ms | cycles %llu | IRQ %llu | disk status %u | US keyboard | F12 reset",
        (unsigned long long)machine.cycles,(unsigned long long)machine.interrupts,machine.status);
    TextOutA(back,10,rc.bottom-25,status,(int)strlen(status));
    BitBlt(dc,0,0,rc.right,rc.bottom,back,0,0,SRCCOPY);
    SelectObject(back,oldbmp);DeleteObject(bmp);DeleteDC(back);EndPaint(hwnd,&ps);
}
static LRESULT CALLBACK window_proc(HWND hwnd,UINT msg,WPARAM wp,LPARAM lp){
    switch(msg){
    case WM_TIMER:{
        LARGE_INTEGER now;QueryPerformanceCounter(&now);
        double dt=(double)(now.QuadPart-last.QuadPart)/frequency.QuadPart;last=now;
        /* Pause catch-up after a debugger break/window drag; guest time stays exact. */
        if(dt>0.25)dt=0.25;
        remainder+=dt*VM_HZ;uint32_t steps=(uint32_t)remainder;remainder-=steps;
        vm_run(&machine,steps);
        uint64_t elapsed=machine.cycles-last_paint;
        if((machine.video_dirty&&elapsed>=VM_HZ/25)||elapsed>=VM_HZ/2){
            last_paint=machine.cycles;machine.video_dirty=0;InvalidateRect(hwnd,NULL,FALSE);
        }return 0;
    }
    case WM_KEYDOWN:case WM_SYSKEYDOWN:case WM_KEYUP:case WM_SYSKEYUP:{
        if(wp==VK_F12){if(msg==WM_KEYDOWN){vm_close(&machine);if(!vm_init(&machine,"boot.rom","disk.img")){MessageBoxA(hwnd,"Reset failed: cannot open boot.rom / disk.img","SVEU16",MB_ICONERROR);DestroyWindow(hwnd);}QueryPerformanceCounter(&last);remainder=0;last_paint=0;}return 0;}
        if(msg==WM_SYSKEYDOWN&&wp==VK_F4)return DefWindowProcA(hwnd,msg,wp,lp);
        unsigned scan=((unsigned long long)lp>>16)&255;
        /* Some injected/test key events omit lParam's scan field. Obtain the
         * hardware-style code from the virtual key, never from a character. */
        if(!scan)scan=MapVirtualKeyA((UINT)wp,MAPVK_VK_TO_VSC)&255;
        if(((unsigned long long)lp>>24)&1)scan|=0x100;
        if(msg==WM_KEYUP||msg==WM_SYSKEYUP)scan|=0x80;
        vm_key(&machine,(uint16_t)scan);return 0;
    }
    case WM_KILLFOCUS:vm_key(&machine,0xAA);vm_key(&machine,0xB6);return 0;
    case WM_PAINT:paint(hwnd);return 0;
    case WM_ERASEBKGND:return 1;
    case WM_DESTROY:KillTimer(hwnd,1);PostQuitMessage(0);return 0;
    default:return DefWindowProcA(hwnd,msg,wp,lp);
    }
}
int main(int argc,char **argv){
    int batch=argc>=2&&!strcmp(argv[1],"--batch");
    if(argc>1&&!batch){fprintf(stderr,"usage: sveu16.exe [--batch commands.txt]\n");return 2;}
    if(!batch){char path[MAX_PATH];GetModuleFileNameA(NULL,path,MAX_PATH);char *p=strrchr(path,'\\');if(p){*p=0;SetCurrentDirectoryA(path);}}
    if(!vm_init(&machine,"boot.rom","disk.img")){
        if(batch)fprintf(stderr,"Cannot load boot.rom (2048 bytes) or disk.img (1 MiB).\n");
        else MessageBoxA(NULL,"Cannot load boot.rom (2048 bytes) or disk.img (1 MiB).","SVEU16",MB_ICONERROR);
        return 1;
    }
    if(batch){
        if(argc!=3){vm_close(&machine);return 2;}
        FILE *f=fopen(argv[2],"rb");if(!f){perror(argv[2]);vm_close(&machine);return 1;}
        machine.trace_pc=symbol("TXST1");if(!machine.trace_pc){fprintf(stderr,"Missing forth.map\n");fclose(f);vm_close(&machine);return 1;}
        machine.trace=stdout;vm_run(&machine,2000000);
        int c;while((c=fgetc(f))!=EOF){
            if(c=='\r')continue;if(c=='\n')c=13;
            int k;for(k=0;k<256;k++)if(key_ascii[k]==c)break;
            if(k==256){fprintf(stderr,"Unsupported batch character %d\n",c);fclose(f);vm_close(&machine);return 1;}
            if(k>=128)vm_key(&machine,42);
            vm_key(&machine,(uint16_t)(k&127));vm_key(&machine,(uint16_t)((k&127)|128));
            if(k>=128)vm_key(&machine,170);
            vm_run(&machine,160000);
        }fclose(f);vm_run(&machine,2000000);machine.trace=NULL;
        printf("\n--- VIDEO MEMORY (approximate ASCII decoding) ---\n");dump_screen(&machine);
        printf("cycles=%llu irq=%llu pc=%04X disk_status=%u\n",(unsigned long long)machine.cycles,(unsigned long long)machine.interrupts,machine.r[15],machine.status);
        vm_close(&machine);return 0;
    }
    SetProcessDPIAware();HINSTANCE instance=GetModuleHandleA(NULL);
    WNDCLASSA wc={0};wc.lpfnWndProc=window_proc;wc.hInstance=instance;wc.lpszClassName="SVEU16Segments";wc.hCursor=LoadCursor(NULL,IDC_ARROW);
    if(!RegisterClassA(&wc)){vm_close(&machine);return 1;}
    HWND hwnd=CreateWindowA(wc.lpszClassName,"SVEU16 - eFORTH - 16 segmenta",WS_OVERLAPPEDWINDOW,CW_USEDEFAULT,CW_USEDEFAULT,1280,800,NULL,NULL,instance,NULL);
    if(!hwnd){vm_close(&machine);return 1;}
    QueryPerformanceFrequency(&frequency);QueryPerformanceCounter(&last);ShowWindow(hwnd,SW_SHOW);SetTimer(hwnd,1,10,NULL);
    MSG msg;while(GetMessageA(&msg,NULL,0,0)>0){TranslateMessage(&msg);DispatchMessageA(&msg);}
    vm_close(&machine);return 0;
}
