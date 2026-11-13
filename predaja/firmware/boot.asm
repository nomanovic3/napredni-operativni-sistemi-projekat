; 1 Kword ROM. Disk sectors 0..127 -> RAM 0x3000..0x6FFF.
      ORG 0
      EQU R1,R1,R1
      SUB R0,R0,R0
      LOD R13,R13,R15
      WRD IRQHANDLER
      LOD R2,R2,R15
      WRD $FFFE
      STO R0,R0,R2
      LOD R3,R3,R15
      WRD $FFFD
      LOD R4,R4,R15
      WRD $FFFC
      LOD R5,R5,R15
      WRD $3000
      SUB R6,R6,R6
SECTOR STO R6,R6,R3
      STO R1,R1,R2
      LOD R7,R7,R15
      WRD 128
      LOD R8,R8,R15
      WRD COPYWORD
COPYWORD LOD R9,R9,R4
      STO R9,R9,R5
      ADD R5,R5,R1
      SUB R7,R7,R1
      MIF R15,R7,R8
      ADD R6,R6,R1
      LOD R7,R7,R15
      WRD 128
      LTU R7,R6,R7
      LOD R8,R8,R15
      WRD SECTOR
      MIF R15,R7,R8
      LOD R15,R15,R15
      WRD $3000
; Injected MAJ saves interrupted PC+1. Retry the replaced instruction.
IRQHANDLER SUB R15,R14,R1
      ORG 1023
      WRD 0
