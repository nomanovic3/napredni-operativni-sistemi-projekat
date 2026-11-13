#ifndef SVEU_VM_H
#define SVEU_VM_H
#include <stdint.h>
#include <stdio.h>
#define VM_HZ 8000000u
#define IRQ_PERIOD 160000u
#define VIDEO_BASE 8192u
#define VIDEO_WORDS 2000u
typedef struct { void *handler; uint8_t d,a,b; } Decoded;
typedef struct {
    uint16_t mem[65536], r[16];
    Decoded decoded[65536];
    uint64_t cycles, interrupts;
    uint32_t until_irq;
    uint16_t keys[1024]; unsigned key_head,key_tail;
    FILE *disk; uint16_t sector, command, status;
    unsigned disk_pos; uint8_t buffer[256];
    int ready, video_dirty;
    uint16_t trace_pc; FILE *trace;
} VM;
int vm_init(VM *v,const char *rom,const char *disk);
void vm_close(VM *v);
uint16_t vm_read(VM *v,uint16_t addr);
void vm_write(VM *v,uint16_t addr,uint16_t value);
int vm_key(VM *v,uint16_t scan);
void vm_run(VM *v,uint32_t cycles);
#endif
