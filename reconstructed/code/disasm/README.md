# Disassembly inicial

Arquivos desta pasta servem como ponto de partida para substituir `incbin` por ASM comentado.

- `bank00_reset.asm`: varredura linear a partir do vetor `reset`.
- `entrypoints.txt`: vetores + alvos de `jsr/jsl/jmp/branches` detectados no bloco inicial.

Fluxo recomendado:
1. Importar ROM no Ghidra/IDA e criar labels de `entrypoints.txt`.
2. Usar `vectors.txt` para validar ponto de entrada e interrupções.
3. Expandir o disassembly por blocos a partir de `jsr/jsl/jmp` encontrados.
4. Reclassificar dados/tabelas e substituir gradualmente bytes por instruções reais.
