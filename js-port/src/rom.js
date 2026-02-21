import { readFileSync } from 'node:fs';

export function loadRom(filePath) {
  const buffer = readFileSync(filePath);
  return new Uint8Array(buffer.buffer, buffer.byteOffset, buffer.byteLength);
}

function scoreHeader(data, base, expectedMode) {
  if (base + 0x40 > data.length) return -999;

  const reset = data[base + 0x3c] | (data[base + 0x3d] << 8);
  const checksum = data[base + 0x1e] | (data[base + 0x1f] << 8);
  const complement = data[base + 0x1c] | (data[base + 0x1d] << 8);
  const mapMode = data[base + 0x15];

  let score = 0;
  if (reset >= 0x8000 && reset <= 0xffff) score += 8;
  if (((checksum ^ complement) & 0xffff) === 0xffff) score += 6;
  if ((mapMode & 0x0f) === expectedMode) score += 5;
  return score;
}

export function parseSnesHeader(data) {
  const loromOff = 0x7fc0;
  const hiromOff = 0xffc0;

  const loromScore = scoreHeader(data, loromOff, 0);
  const hiromScore = scoreHeader(data, hiromOff, 1);

  const headerOffset = hiromScore > loromScore ? hiromOff : loromOff;
  const mapping = hiromScore > loromScore ? 'HiROM' : 'LoROM';

  const titleBytes = data.slice(headerOffset, headerOffset + 21);
  const title = String.fromCharCode(...titleBytes).replace(/\u0000.*$/, '').trim();

  const read16 = (off) => data[headerOffset + off] | (data[headerOffset + off + 1] << 8);

  return {
    mapping,
    headerOffset,
    title,
    mapMode: data[headerOffset + 0x15],
    romType: data[headerOffset + 0x16],
    romSizeByte: data[headerOffset + 0x17],
    sramSizeByte: data[headerOffset + 0x18],
    region: data[headerOffset + 0x19],
    developerId: data[headerOffset + 0x1a],
    version: data[headerOffset + 0x1b],
    checksumComplement: read16(0x1c),
    checksum: read16(0x1e),
    vectors: {
      native: {
        nmi: read16(0x2a),
        reset: read16(0x2c),
        irq: read16(0x2e)
      },
      emulation: {
        nmi: read16(0x3a),
        reset: read16(0x3c),
        irq: read16(0x3e)
      }
    }
  };
}

export function loromOffset(bank, addr16) {
  return bank * 0x8000 + (addr16 & 0x7fff);
}
