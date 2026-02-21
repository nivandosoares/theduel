#!/usr/bin/env python3
"""Gera uma estrutura legível para engenharia reversa de um ROM SNES."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path


ASCII_RE = re.compile(rb"[\x20-\x7E]{4,}")


@dataclass
class HeaderInfo:
    mapping: str
    header_offset: int
    title: str
    map_mode: int
    rom_type: int
    rom_size_byte: int
    sram_size_byte: int
    region: int
    developer_id: int
    version: int
    checksum_complement: int
    checksum: int
    native_vectors: dict[str, int]
    emulation_vectors: dict[str, int]


def score_header(data: bytes, base: int, expected_mode: int) -> int:
    if base + 0x40 > len(data):
        return -999
    score = 0
    reset = int.from_bytes(data[base + 0x3C : base + 0x3E], "little")
    checksum = int.from_bytes(data[base + 0x1E : base + 0x20], "little")
    complement = int.from_bytes(data[base + 0x1C : base + 0x1E], "little")
    map_mode = data[base + 0x15]
    title = data[base : base + 21]

    if 0x8000 <= reset <= 0xFFFF:
        score += 8
    if ((checksum ^ complement) & 0xFFFF) == 0xFFFF:
        score += 6
    if (map_mode & 0x0F) == expected_mode:
        score += 5
    if all(0x20 <= c <= 0x7E or c == 0 for c in title):
        score += 3

    return score


def parse_header(data: bytes) -> HeaderInfo:
    lorom_off = 0x7FC0
    hirom_off = 0xFFC0

    lorom_score = score_header(data, lorom_off, expected_mode=0)
    hirom_score = score_header(data, hirom_off, expected_mode=1)

    if hirom_score > lorom_score:
        mapping = "HiROM"
        off = hirom_off
    else:
        mapping = "LoROM"
        off = lorom_off

    title = data[off : off + 21].split(b"\x00", 1)[0].decode("ascii", errors="replace").strip()
    map_mode = data[off + 0x15]
    rom_type = data[off + 0x16]
    rom_size_byte = data[off + 0x17]
    sram_size_byte = data[off + 0x18]
    region = data[off + 0x19]
    developer_id = data[off + 0x1A]
    version = data[off + 0x1B]
    checksum_complement = int.from_bytes(data[off + 0x1C : off + 0x1E], "little")
    checksum = int.from_bytes(data[off + 0x1E : off + 0x20], "little")

    native_names = [
        "cop",
        "brk",
        "abort",
        "nmi",
        "reset",
        "irq",
    ]
    emu_names = ["cop", "brk", "abort", "nmi", "reset", "irq"]

    native_offsets = [0x24, 0x26, 0x28, 0x2A, 0x2C, 0x2E]
    emu_offsets = [0x34, 0x36, 0x38, 0x3A, 0x3C, 0x3E]

    native_vectors = {
        name: int.from_bytes(data[off + vec_off : off + vec_off + 2], "little")
        for name, vec_off in zip(native_names, native_offsets)
    }
    emulation_vectors = {
        name: int.from_bytes(data[off + vec_off : off + vec_off + 2], "little")
        for name, vec_off in zip(emu_names, emu_offsets)
    }

    return HeaderInfo(
        mapping=mapping,
        header_offset=off,
        title=title,
        map_mode=map_mode,
        rom_type=rom_type,
        rom_size_byte=rom_size_byte,
        sram_size_byte=sram_size_byte,
        region=region,
        developer_id=developer_id,
        version=version,
        checksum_complement=checksum_complement,
        checksum=checksum,
        native_vectors=native_vectors,
        emulation_vectors=emulation_vectors,
    )


def split_banks(data: bytes, mapping: str) -> list[bytes]:
    if mapping == "LoROM":
        bank_size = 0x8000
    else:
        bank_size = 0x10000
    return [data[i : i + bank_size] for i in range(0, len(data), bank_size)]


def extract_ascii_strings(data: bytes) -> list[str]:
    out = []
    for m in ASCII_RE.finditer(data):
        s = m.group().decode("ascii", errors="ignore")
        out.append(f"0x{m.start():06X}: {s}")
    return out


def write_project(rom_path: Path, out_dir: Path) -> None:
    data = rom_path.read_bytes()
    header = parse_header(data)
    banks = split_banks(data, header.mapping)
    strings = extract_ascii_strings(data)

    code_dir = out_dir / "code"
    assets_dir = out_dir / "assets"
    banks_dir = code_dir / "banks"
    banks_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    (assets_dir / "header.json").write_text(json.dumps(asdict(header), indent=2), encoding="utf-8")
    (assets_dir / "strings_ascii.txt").write_text("\n".join(strings) + "\n", encoding="utf-8")

    for idx, bank in enumerate(banks):
        (banks_dir / f"bank_{idx:02X}.bin").write_bytes(bank)

    disasm_stub = [
        "; Auto-gerado para facilitar engenharia reversa.",
        "; Os bancos foram extraídos para análise em ferramentas como bsnes-plus, Mesen-S, Ghidra e IDA.",
        ".cpu " + ("65816"),
        "",
        "; Mapeamento detectado: " + header.mapping,
        f"; Título: {header.title}",
        "",
    ]
    for idx, _ in enumerate(banks):
        if header.mapping == "LoROM":
            bank_addr = 0x8000
        else:
            bank_addr = 0x0000
        disasm_stub.append(f'.segment "BANK{idx:02X}"')
        disasm_stub.append(f'.org ${bank_addr:04X}')
        disasm_stub.append(f'.incbin "banks/bank_{idx:02X}.bin"')
        disasm_stub.append("")

    (code_dir / "rom_layout.asm").write_text("\n".join(disasm_stub), encoding="utf-8")

    vectors_lines = [
        "; Vetores extraídos do cabeçalho SNES",
        f"; Header @ 0x{header.header_offset:06X}",
        "",
        "[native]",
    ]
    for k, v in header.native_vectors.items():
        vectors_lines.append(f"{k} = ${v:04X}")
    vectors_lines.append("")
    vectors_lines.append("[emulation]")
    for k, v in header.emulation_vectors.items():
        vectors_lines.append(f"{k} = ${v:04X}")
    vectors_lines.append("")

    (code_dir / "vectors.txt").write_text("\n".join(vectors_lines), encoding="utf-8")

    readme = f"""# Estrutura reconstruída para engenharia reversa

Este diretório foi gerado a partir do ROM `{rom_path.name}` para disponibilizar uma base de trabalho legível.

## O que foi extraído
- `code/banks/*.bin`: ROM separado por bancos ({header.mapping}), gerado localmente (não versionado).
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
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconstrói estrutura base para reverse engineering de ROM SNES")
    parser.add_argument("rom", type=Path)
    parser.add_argument("--out", type=Path, default=Path("reconstructed"))
    args = parser.parse_args()

    write_project(args.rom, args.out)


if __name__ == "__main__":
    main()
