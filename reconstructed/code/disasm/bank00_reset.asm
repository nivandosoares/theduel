; Disassembly linear inicial a partir do vetor RESET (auto-gerado).
; Instruções não reconhecidas aparecem como .byte para revisão manual.
; RESET = $802A (offset ROM 0x00002A)

.org $802A
reset_entry:
  clc             ; 18
  xce             ; FB
  rep  #$10       ; C2 10
  sep  #$20       ; E2 20
  ldx  #$01FF     ; A2 FF 01
  txs             ; 9A
  phk             ; 4B
  plb             ; AB
  ldx  #$0000     ; A2 00 00
  phx             ; DA
  pld             ; 2B
  stz  $4200      ; 9C 00 42
  lda  #$8F       ; A9 8F
  sta  $2100      ; 8D 00 21
  stz  $2101      ; 9C 01 21
  stz  $2102      ; 9C 02 21
  stz  $2103      ; 9C 03 21
  stz  $2104      ; 9C 04 21
  stz  $2104      ; 9C 04 21
  ldx  #$2105     ; A2 05 21
  stz  $00,X      ; 74 00
  inx             ; E8
  cpx  #$210D     ; E0 0D 21
  bne  $8055      ; D0 F8
  stz  $00,X      ; 74 00
  stz  $00,X      ; 74 00
  inx             ; E8
  cpx  #$2115     ; E0 15 21
  bne  $805D      ; D0 F6
  lda  #$80       ; A9 80
  sta  $2115      ; 8D 15 21
  inx             ; E8
  stz  $00,X      ; 74 00
  inx             ; E8
  cpx  #$211B     ; E0 1B 21
  bne  $806D      ; D0 F8
  ldy  #$0000     ; A0 00 00
  stz  $00,X      ; 74 00
  lda  $8000,Y    ; B9 00 80
  .byte $95       ; opcode não mapeado
  .byte $00       ; opcode não mapeado
  iny             ; C8
  inx             ; E8
  cpx  #$2121     ; E0 21 21
  bne  $8078      ; D0 F2
  stz  $00,X      ; 74 00
  inx             ; E8
  cpx  #$2130     ; E0 30 21
  bne  $8086      ; D0 F8
  lda  #$30       ; A9 30
  sta  $2130      ; 8D 30 21
  stz  $2131      ; 9C 31 21
  lda  #$E0       ; A9 E0
  sta  $2132      ; 8D 32 21
  stz  $2133      ; 9C 33 21
  rep  #$20       ; C2 20
  lda  #$0000     ; A9 00 00
  tax             ; AA
  tay             ; A8
  jsl  $00845B    ; 22 5B 84 00
  sep  #$20       ; E2 20
  stz  $4200      ; 9C 00 42
  lda  #$FF       ; A9 FF
  sta  $4201      ; 8D 01 42
  ldx  #$4202     ; A2 02 42
  stz  $00,X      ; 74 00
  inx             ; E8
  cpx  #$420D     ; E0 0D 42
  bne  $80B6      ; D0 F8
  rep  #$20       ; C2 20
  lda  #$AC1B     ; A9 1B AC
  .byte $85       ; opcode não mapeado
  .byte $0C       ; opcode não mapeado
  stz  $0E        ; 64 0E
  jsl  $009283    ; 22 83 92 00
  sep  #$20       ; E2 20
  ldx  #$1FFF     ; A2 FF 1F
  stz  $00,X      ; 74 00
  .byte $CA       ; opcode não mapeado
  bpl  $80D0      ; 10 FB
  ldx  #$0005     ; A2 05 00
  .byte $BD       ; opcode não mapeado
  .byte $23       ; opcode não mapeado
  bra  $8079      ; 80 9D
  .byte $00       ; opcode não mapeado
  .byte $01       ; opcode não mapeado
  .byte $CA       ; opcode não mapeado
  bpl  $80D8      ; 10 F7
  jsl  $018AF8    ; 22 F8 8A 01
  lda  #$8F       ; A9 8F
  sta  $0966      ; 8D 66 09
  ldx  #$001C     ; A2 1C 00
  .byte $BD       ; opcode não mapeado
  .byte $06       ; opcode não mapeado
  bra  $8086      ; 80 95
  sec             ; 38
  .byte $CA       ; opcode não mapeado
  bpl  $80ED      ; 10 F8
  stz  $0968      ; 9C 68 09
  stz  $096A      ; 9C 6A 09
  stz  $40        ; 64 40
  rep  #$20       ; C2 20
  stz  $096C      ; 9C 6C 09
  stz  $096F      ; 9C 6F 09
  stz  $0974      ; 9C 74 09
  stz  $0964      ; 9C 64 09
  stz  $0998      ; 9C 98 09
  lda  #$8029     ; A9 29 80
  .byte $85       ; opcode não mapeado
  .byte $3E       ; opcode não mapeado
  ldx  #$000E     ; A2 0E 00
  .byte $9E       ; opcode não mapeado
  .byte $32       ; opcode não mapeado
  .byte $0F       ; opcode não mapeado
  .byte $CA       ; opcode não mapeado
  .byte $CA       ; opcode não mapeado
  bpl  $8116      ; 10 F9
  lda  #$0000     ; A9 00 00
  tax             ; AA
  tay             ; A8
  jsl  $00954E    ; 22 4E 95 00
  sep  #$20       ; E2 20
  lda  #$81       ; A9 81
  sta  $4200      ; 8D 00 42
  jsl  $00A368    ; 22 68 A3 00
  jsl  $00850F    ; 22 0F 85 00
  jml  $018B26    ; 5C 26 8B 01
  rep  #$30       ; C2 30
  phb             ; 8B
  phk             ; 4B
  plb             ; AB
  pha             ; 48
  .byte $58       ; opcode não mapeado
  .byte $AD       ; opcode não mapeado
  bpl  $8185      ; 10 42
  .byte $A5       ; opcode não mapeado
  .byte $51       ; opcode não mapeado
  beq  $814A      ; F0 03
  pla             ; 68
  plb             ; AB
  rti             ; 40

; fim do bloco linear inicial
