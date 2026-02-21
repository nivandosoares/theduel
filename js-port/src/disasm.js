import { loromOffset } from './rom.js';

const OPCODES = new Map([
  [0x18, ['clc', 'impl']],
  [0xfb, ['xce', 'impl']],
  [0xc2, ['rep', 'imm8']],
  [0xe2, ['sep', 'imm8']],
  [0xa9, ['lda', 'immM']],
  [0xa2, ['ldx', 'immX']],
  [0xa0, ['ldy', 'immX']],
  [0x9a, ['txs', 'impl']],
  [0x4b, ['phk', 'impl']],
  [0xab, ['plb', 'impl']],
  [0xda, ['phx', 'impl']],
  [0x2b, ['pld', 'impl']],
  [0x9c, ['stz', 'abs']],
  [0x8d, ['sta', 'abs']],
  [0x74, ['stz', 'dpX']],
  [0xe8, ['inx', 'impl']],
  [0xc8, ['iny', 'impl']],
  [0xe0, ['cpx', 'immX']],
  [0xd0, ['bne', 'rel8']],
  [0xb9, ['lda', 'absY']],
  [0x80, ['bra', 'rel8']],
  [0xaa, ['tax', 'impl']],
  [0xa8, ['tay', 'impl']],
  [0x22, ['jsl', 'long']],
  [0x10, ['bpl', 'rel8']],
  [0x4c, ['jmp', 'abs']],
  [0x5c, ['jml', 'long']],
  [0x20, ['jsr', 'abs']],
  [0x60, ['rts', 'impl']],
  [0x6b, ['rtl', 'impl']],
  [0x40, ['rti', 'impl']]
]);

function sizeFor(mode, flags) {
  if (mode === 'impl') return 1;
  if (mode === 'imm8') return 2;
  if (mode === 'immM') return flags.m8 ? 2 : 3;
  if (mode === 'immX') return flags.x8 ? 2 : 3;
  if (mode === 'abs' || mode === 'absY') return 3;
  if (mode === 'dpX') return 2;
  if (mode === 'long') return 4;
  if (mode === 'rel8') return 2;
  return 1;
}

function formatOperand(mode, operand, pc) {
  if (mode === 'impl') return '';
  if (mode === 'imm8') return `#$${operand[0].toString(16).padStart(2, '0').toUpperCase()}`;
  if (mode === 'immM' || mode === 'immX') {
    if (operand.length === 1) return `#$${operand[0].toString(16).padStart(2, '0').toUpperCase()}`;
    const v = operand[0] | (operand[1] << 8);
    return `#$${v.toString(16).padStart(4, '0').toUpperCase()}`;
  }
  if (mode === 'abs') {
    const v = operand[0] | (operand[1] << 8);
    return `$${v.toString(16).padStart(4, '0').toUpperCase()}`;
  }
  if (mode === 'absY') {
    const v = operand[0] | (operand[1] << 8);
    return `$${v.toString(16).padStart(4, '0').toUpperCase()},Y`;
  }
  if (mode === 'dpX') return `$${operand[0].toString(16).padStart(2, '0').toUpperCase()},X`;
  if (mode === 'long') {
    const v = operand[0] | (operand[1] << 8) | (operand[2] << 16);
    return `$${v.toString(16).padStart(6, '0').toUpperCase()}`;
  }
  if (mode === 'rel8') {
    const rel = operand[0] < 0x80 ? operand[0] : operand[0] - 0x100;
    const target = (pc + 2 + rel) & 0xffff;
    return `$${target.toString(16).padStart(4, '0').toUpperCase()}`;
  }
  return '';
}

export function disassembleResetWindow(data, resetAddr, maxBytes = 0x180) {
  const start = loromOffset(0x00, resetAddr);
  const end = Math.min(data.length, start + maxBytes);
  const flags = { m8: true, x8: true };

  const lines = [];
  const refs = { calls: new Set(), branches: new Set() };

  for (let i = start; i < end; ) {
    const pc = (resetAddr + (i - start)) & 0xffff;
    const op = data[i];
    const decoded = OPCODES.get(op);

    if (!decoded) {
      lines.push(`${pc.toString(16).padStart(4, '0').toUpperCase()}: .byte $${op.toString(16).padStart(2, '0').toUpperCase()}`);
      i += 1;
      continue;
    }

    const [mnem, mode] = decoded;
    const size = sizeFor(mode, flags);
    const chunk = data.slice(i, i + size);
    const operand = chunk.slice(1);
    const operandText = formatOperand(mode, operand, pc);

    lines.push(`${pc.toString(16).padStart(4, '0').toUpperCase()}: ${mnem} ${operandText}`.trim());

    if (mnem === 'jsl' || mnem === 'jsr' || mnem === 'jmp' || mnem === 'jml') {
      refs.calls.add(`${mnem.toUpperCase()} ${operandText}`);
    }
    if (mode === 'rel8') {
      refs.branches.add(`${mnem.toUpperCase()} ${operandText}`);
    }

    if (mnem === 'rep' && operand.length) {
      if (operand[0] & 0x20) flags.m8 = false;
      if (operand[0] & 0x10) flags.x8 = false;
    }
    if (mnem === 'sep' && operand.length) {
      if (operand[0] & 0x20) flags.m8 = true;
      if (operand[0] & 0x10) flags.x8 = true;
    }

    i += size;
    if (mnem === 'rts' || mnem === 'rtl' || mnem === 'rti') break;
  }

  return {
    lines,
    calls: [...refs.calls].sort(),
    branches: [...refs.branches].sort()
  };
}
