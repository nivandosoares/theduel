# Bancos binários (gerados localmente)

Os arquivos `bank_XX.bin` são gerados pelo script `tools_reverse_engineer_rom.py`, mas **não são versionados** para evitar problemas de compatibilidade ao abrir PR (diff de binário e limites da plataforma).

Para gerar localmente:

```bash
python3 tools_reverse_engineer_rom.py "Duel, The - Test Drive II (USA).sfc" --out reconstructed
```

Após gerar, você terá os `bank_00.bin` ... `bank_1F.bin` nesta pasta para usar em disassembler/debugger.
