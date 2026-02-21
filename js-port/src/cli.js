import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { loadRom, parseSnesHeader } from './rom.js';
import { disassembleResetWindow } from './disasm.js';
import { TheDuelBoot } from './gameBase.js';

const inputPath = process.argv[2];
const defaultCandidates = [
  resolve(process.cwd(), 'Duel, The - Test Drive II (USA).sfc'),
  resolve(process.cwd(), '../Duel, The - Test Drive II (USA).sfc')
];

let romPath;
if (inputPath) {
  romPath = resolve(process.cwd(), inputPath);
} else {
  romPath = defaultCandidates.find((p) => existsSync(p));
}

if (!romPath || !existsSync(romPath)) {
  console.error('Uso: node src/cli.js "Duel, The - Test Drive II (USA).sfc"');
  console.error('Dica: de dentro de js-port, rode `npm run analyze` ou passe o caminho do ROM.');
  process.exit(1);
}

const rom = loadRom(romPath);
const header = parseSnesHeader(rom);
const reset = header.vectors.emulation.reset;
const disasm = disassembleResetWindow(rom, reset);

const boot = new TheDuelBoot();
boot.bootSequence();

console.log('=== The Duel SNES -> JS base ===');
console.log(`ROM: ${romPath}`);
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
