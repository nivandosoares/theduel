import { loadRom, parseSnesHeader } from './rom.js';
import { disassembleResetWindow } from './disasm.js';
import { TheDuelBoot } from './gameBase.js';

const romPath = process.argv[2];
if (!romPath) {
  console.error('Uso: node src/cli.js "Duel, The - Test Drive II (USA).sfc"');
  process.exit(1);
}

const rom = loadRom(romPath);
const header = parseSnesHeader(rom);
const reset = header.vectors.emulation.reset;
const disasm = disassembleResetWindow(rom, reset);

const boot = new TheDuelBoot();
boot.bootSequence();

console.log('=== The Duel SNES -> JS base ===');
console.log(`Título: ${header.title}`);
console.log(`Mapeamento: ${header.mapping}`);
console.log(`RESET: $${reset.toString(16).toUpperCase()}`);
console.log('\n--- Fluxo boot em JS ---');
console.log(boot.state, boot.entrypoints);

console.log('\n--- Primeiras instruções (janela RESET) ---');
for (const line of disasm.lines.slice(0, 20)) console.log(line);

console.log('\n--- Calls detectadas ---');
for (const c of disasm.calls) console.log(c);

console.log('\n--- Branches detectadas ---');
for (const b of disasm.branches) console.log(b);
