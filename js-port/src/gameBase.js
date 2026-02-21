/**
 * "Transcrição" de alto nível do bootstrap do game em JavaScript.
 *
 * Não é um emulador completo de SNES nem um port 1:1 de toda a ROM.
 * É uma base legível do fluxo inicial observado no vetor RESET.
 */
export class TheDuelBoot {
  constructor() {
    this.reg = {
      inidisp: 0x8f,
      nmitimen: 0x00,
      cgwsel: 0x00,
      cgadsub: 0x00,
      coldata: 0x00
    };
    this.state = {
      interruptsEnabled: false,
      dmaEnabled: false,
      stackPointer: 0x01ff,
      initPhase: 'power_on'
    };
  }

  /**
   * Equivalente conceitual ao bloco inicial no reset:
   * - configura CPU mode
   * - inicializa PPU/APU I/O
   * - prepara variáveis globais
   */
  bootSequence() {
    this.state.initPhase = 'cpu_setup';
    this.state.stackPointer = 0x01ff;

    this.state.initPhase = 'ppu_setup';
    this.reg.inidisp = 0x8f; // tela apagada/brilho mínimo durante init
    this.reg.nmitimen = 0x00; // NMI/IRQ inicialmente desabilitados

    this.state.initPhase = 'memory_clear';
    this.clearCoreWorkRam();

    this.state.initPhase = 'engine_kickoff';
    this.callEngineEntrypoints();

    this.state.initPhase = 'ready';
    this.state.interruptsEnabled = true;
  }

  clearCoreWorkRam() {
    // placeholder de transcrição: no ROM original isso ocorre via loops + stores em registradores/WRAM.
    this.state.dmaEnabled = false;
  }

  callEngineEntrypoints() {
    // Pontos observados no disassembly linear (JSL/JML do bootstrap).
    this.entrypoints = [
      0x00845b,
      0x009283,
      0x018af8,
      0x018b26
    ];
  }
}
