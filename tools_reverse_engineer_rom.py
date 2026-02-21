#!/usr/bin/env python3
"""Gera uma estrutura legível para engenharia reversa de um ROM SNES."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path


ASCII_RE = re.compile(rb"[\x20-\x7E]{4,}")


ADDR_MODE_SIZE = {
    "impl": 1,
    "imm8": 2,
    "imm_m": 0,
    "imm_x": 0,
    "imm16": 3,
    "dp": 2,
    "dp_x": 2,
    "dp_y": 2,
    "sr": 2,
    "sr_y": 2,
    "abs": 3,
    "abs_x": 3,
    "abs_y": 3,
    "ind": 3,
    "ind_x": 2,
    "ind_y": 2,
    "dp_ind": 2,
    "dp_ind_long": 2,
    "dp_ind_long_y": 2,
    "long": 4,
    "long_x": 4,
    "rel8": 2,
    "rel16": 3,
    "block": 3,
}


# Decodificador mínimo (fallback em .byte para opcodes não mapeados).
OPCODES = {
    0x78: ("sei", "impl"),
    0x18: ("clc", "impl"),
    0x38: ("sec", "impl"),
    0xFB: ("xce", "impl"),
    0xC2: ("rep", "imm8"),
    0xE2: ("sep", "imm8"),
    0xA9: ("lda", "imm_m"),
    0xA2: ("ldx", "imm_x"),
    0xA0: ("ldy", "imm_x"),
    0x8D: ("sta", "abs"),
    0x8F: ("sta", "long"),
    0x9C: ("stz", "abs"),
    0x64: ("stz", "dp"),
    0x20: ("jsr", "abs"),
    0x22: ("jsl", "long"),
    0x4C: ("jmp", "abs"),
    0x5C: ("jml", "long"),
    0x6C: ("jmp", "ind"),
    0x60: ("rts", "impl"),
    0x6B: ("rtl", "impl"),
    0x40: ("rti", "impl"),
    0xD0: ("bne", "rel8"),
    0xF0: ("beq", "rel8"),
    0x10: ("bpl", "rel8"),
    0x30: ("bmi", "rel8"),
    0x80: ("bra", "rel8"),
    0x82: ("brl", "rel16"),
    0x90: ("bcc", "rel8"),
    0xB0: ("bcs", "rel8"),
    0x50: ("bvc", "rel8"),
    0x70: ("bvs", "rel8"),
    0xC9: ("cmp", "imm_m"),
    0xE0: ("cpx", "imm_x"),
    0xC0: ("cpy", "imm_x"),
    0x8A: ("txa", "impl"),
    0x98: ("tya", "impl"),
    0x9A: ("txs", "impl"),
    0xBA: ("tsx", "impl"),
    0x48: ("pha", "impl"),
    0x68: ("pla", "impl"),
    0xDA: ("phx", "impl"),
    0xFA: ("plx", "impl"),
    0x5A: ("phy", "impl"),
    0x7A: ("ply", "impl"),
    0x8B: ("phb", "impl"),
    0xAB: ("plb", "impl"),
    0x4B: ("phk", "impl"),
    0x08: ("php", "impl"),
    0x28: ("plp", "impl"),
    0xEA: ("nop", "impl"),
    0x2B: ("pld", "impl"),
    0x74: ("stz", "dp_x"),
    0xE8: ("inx", "impl"),
    0xC8: ("iny", "impl"),
    0xB9: ("lda", "abs_y"),
    0xAA: ("tax", "impl"),
    0xA8: ("tay", "impl"),
    0x15: ("ora", "dp_x"),
    0xB8: ("clv", "impl"),
}


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


def lorom_file_offset(addr16: int, bank: int = 0x00) -> int:
    return bank * 0x8000 + (addr16 & 0x7FFF)


def format_operand(mode: str, operand: bytes, pc: int) -> str:
    if mode == "impl":
        return ""
    if mode in {"imm8", "dp", "dp_x", "dp_y", "sr", "sr_y", "ind_x", "ind_y", "dp_ind", "dp_ind_long", "dp_ind_long_y"}:
        if mode == "imm8":
            return f"#$%02X" % operand[0]
        if mode == "dp_x":
            return f"$%02X,X" % operand[0]
        if mode == "dp_y":
            return f"$%02X,Y" % operand[0]
        if mode == "ind_x":
            return f"($%02X,X)" % operand[0]
        if mode == "ind_y":
            return f"($%02X),Y" % operand[0]
        return f"$%02X" % operand[0]
    if mode in {"imm_m", "imm_x"}:
        return f"#$%02X" % operand[0] if len(operand) == 1 else f"#$%04X" % int.from_bytes(operand, "little")
    if mode in {"abs", "abs_x", "abs_y", "ind"}:
        v = int.from_bytes(operand, "little")
        if mode == "abs_x":
            return f"$%04X,X" % v
        if mode == "abs_y":
            return f"$%04X,Y" % v
        if mode == "ind":
            return f"($%04X)" % v
        return f"$%04X" % v
    if mode in {"long", "long_x"}:
        v = int.from_bytes(operand, "little")
        return f"$%06X" % v
    if mode == "rel8":
        rel = int.from_bytes(operand, "little", signed=True)
        return f"$%04X" % ((pc + 2 + rel) & 0xFFFF)
    if mode == "rel16":
        rel = int.from_bytes(operand, "little", signed=True)
        return f"$%04X" % ((pc + 3 + rel) & 0xFFFF)
    if mode in {"block", "imm16"}:
        v = int.from_bytes(operand, "little")
        return f"#$%04X" % v if mode == "imm16" else f"$%04X" % v
    return " ".join(f"${b:02X}" for b in operand)


def decode_reset_stub(data: bytes, reset_addr: int, max_bytes: int = 0x180) -> tuple[list[str], list[str]]:
    start = lorom_file_offset(reset_addr)
    end = min(start + max_bytes, len(data))
    lines = [
        '; Disassembly linear inicial a partir do vetor RESET (auto-gerado).',
        '; Instruções não reconhecidas aparecem como .byte para revisão manual.',
        f'; RESET = ${reset_addr:04X} (offset ROM 0x{start:06X})',
        '',
        f'.org ${reset_addr:04X}',
        'reset_entry:',
    ]

    i = start
    call_targets: list[str] = []
    branch_targets: list[str] = []
    # Estado inicial em modo emulação: M=1 e X=1 (acumulador/índice de 8 bits).
    m8 = True
    x8 = True
    while i < end:
        pc = reset_addr + (i - start)
        op = data[i]
        if op in OPCODES:
            mnem, mode = OPCODES[op]
            if mode == "imm_m":
                size = 2 if m8 else 3
            elif mode == "imm_x":
                size = 2 if x8 else 3
            else:
                size = ADDR_MODE_SIZE[mode]
            chunk = data[i : i + size]
            if len(chunk) < size:
                lines.append(f'  .byte ${op:02X} ; truncado')
                break
            operand = chunk[1:]
            operand_txt = format_operand(mode, operand, pc)
            byte_txt = ' '.join(f'{b:02X}' for b in chunk)
            lines.append(f'  {mnem:<4} {operand_txt:<10} ; {byte_txt}')
            i += size

            if mnem == "jsr" and mode == "abs":
                target = int.from_bytes(operand, "little")
                call_targets.append(f"JSR ${target:04X} (bank 00)")
            elif mnem == "jsl" and mode == "long":
                target = int.from_bytes(operand, "little")
                call_targets.append(f"JSL ${target:06X}")
            elif mnem in {"jmp", "jml"} and operand:
                target = int.from_bytes(operand, "little")
                width = 4 if mnem == "jmp" else 6
                call_targets.append(f"{mnem.upper()} ${target:0{width}X}")
            elif mode in {"rel8", "rel16"}:
                branch_targets.append(f"{mnem.upper()} {format_operand(mode, operand, pc)}")

            if mnem == "rep" and operand:
                m8 = m8 and not bool(operand[0] & 0x20)
                x8 = x8 and not bool(operand[0] & 0x10)
            elif mnem == "sep" and operand:
                if operand[0] & 0x20:
                    m8 = True
                if operand[0] & 0x10:
                    x8 = True
            if mnem in {"rts", "rtl", "rti"}:
                lines.append('')
                lines.append('; fim do bloco linear inicial')
                break
        else:
            lines.append(f'  .byte ${op:02X}       ; opcode não mapeado')
            i += 1

    refs = ["[calls]"] + sorted(set(call_targets)) + ["", "[branches]"] + sorted(set(branch_targets))
    return lines, refs


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

    disasm_dir = code_dir / "disasm"
    disasm_dir.mkdir(parents=True, exist_ok=True)
    reset_stub, reset_refs = decode_reset_stub(data, header.emulation_vectors["reset"])
    (disasm_dir / "bank00_reset.asm").write_text("\n".join(reset_stub) + "\n", encoding="utf-8")

    entrypoints = [
        "# Pontos de entrada e referências iniciais",
        "",
        "[vectors]",
        f"RESET = ${header.emulation_vectors['reset']:04X}",
        f"NMI = ${header.emulation_vectors['nmi']:04X}",
        f"IRQ = ${header.emulation_vectors['irq']:04X}",
        "",
    ] + reset_refs + ["", "Use estes endereços para criar labels iniciais no Ghidra/IDA."]
    (disasm_dir / "entrypoints.txt").write_text("\n".join(entrypoints) + "\n", encoding="utf-8")

    disasm_readme = """# Disassembly inicial

Arquivos desta pasta servem como ponto de partida para substituir `incbin` por ASM comentado.

- `bank00_reset.asm`: varredura linear a partir do vetor `reset`.
- `entrypoints.txt`: vetores + alvos de `jsr/jsl/jmp/branches` detectados no bloco inicial.

Fluxo recomendado:
1. Importar ROM no Ghidra/IDA e criar labels de `entrypoints.txt`.
2. Usar `vectors.txt` para validar ponto de entrada e interrupções.
3. Expandir o disassembly por blocos a partir de `jsr/jsl/jmp` encontrados.
4. Reclassificar dados/tabelas e substituir gradualmente bytes por instruções reais.
"""
    (disasm_dir / "README.md").write_text(disasm_readme, encoding="utf-8")

    readme = f"""# Estrutura reconstruída para engenharia reversa

Este diretório foi gerado a partir do ROM `{rom_path.name}` para disponibilizar uma base de trabalho legível.

## O que foi extraído
- `code/banks/*.bin`: ROM separado por bancos ({header.mapping}), gerado localmente (não versionado).
- `code/rom_layout.asm`: layout ASM com `incbin` de cada banco.
- `code/vectors.txt`: vetores nativo/emulação do SNES.
- `code/disasm/bank00_reset.asm`: disassembly linear inicial a partir do vetor reset.
- `code/disasm/entrypoints.txt`: vetores e alvos iniciais para rotulagem no disassembler.
- `assets/header.json`: metadados do cabeçalho.
- `assets/strings_ascii.txt`: strings ASCII localizadas no ROM.

## Próximos passos recomendados
1. Carregar os bancos em um disassembler 65c816 (Ghidra + plugin SNES, IDA, ou Mesen-S debugger).
2. Usar `vectors.txt` para iniciar no vetor `reset`.
3. Importar `code/disasm/entrypoints.txt` para criar labels iniciais no disassembler.
4. Renomear rotinas e substituir gradualmente `incbin` por código ASM comentado.

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
