# Estrutura reconstruída para engenharia reversa

Este diretório foi gerado a partir do ROM `Duel, The - Test Drive II (USA).sfc` para disponibilizar uma base de trabalho legível.

## O que foi extraído
- `code/banks/*.bin`: ROM separado por bancos (LoROM), gerado localmente (não versionado).
- `code/rom_layout.asm`: layout ASM com `incbin` de cada banco.
- `code/vectors.txt`: vetores nativo/emulação do SNES.
- `assets/header.json`: metadados do cabeçalho.
- `assets/strings_ascii.txt`: strings ASCII localizadas no ROM.

## Próximos passos recomendados
1. Carregar os bancos em um disassembler 65c816 (Ghidra + plugin SNES, IDA, ou Mesen-S debugger).
2. Usar `vectors.txt` para iniciar no vetor `reset`.
3. Renomear rotinas e substituir gradualmente `incbin` por código ASM comentado.

## Nota sobre PR
Para manter compatibilidade com criação de PR, os binários `bank_*.bin` não são commitados.
Use o script para regenerar esses arquivos localmente quando precisar.

> Observação: sem símbolos originais do desenvolvedor, a reconstrução literal do código-fonte original não é possível. Esta estrutura reduz o esforço para recuperar lógica e assets de forma incremental.
