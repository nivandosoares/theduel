# The Duel — transcrição base para JavaScript

Este diretório entrega uma **transcrição prática da base do game em JS** para estudo e evolução.

## O que já existe
- `src/rom.js`: leitura do ROM e parse do header/vetores SNES.
- `src/disasm.js`: disassembly linear inicial a partir do vetor RESET com coleta de calls/branches.
- `src/gameBase.js`: versão JavaScript de alto nível do bootstrap do jogo (init CPU/PPU/memória/engine).
- `src/cli.js`: CLI para imprimir análise do ROM + fluxo do boot em JS.

## Como rodar
```bash
node js-port/src/cli.js "Duel, The - Test Drive II (USA).sfc"
```

## Como o código base funciona (resumo)
1. O SNES entra no vetor `RESET` (`$802A`) e executa setup de CPU/stack.
2. O código inicial desliga interrupções e prepara registradores PPU/APU.
3. Em seguida limpa estado de memória e chama rotinas principais via `JSL/JML`.
4. Depois do setup, habilita o loop principal e sincronização por frame (NMI/IRQ).

> Observação: este JS é uma transcrição guiada por engenharia reversa do bootstrap, não um emulador completo nem port pixel-perfect do jogo inteiro.
