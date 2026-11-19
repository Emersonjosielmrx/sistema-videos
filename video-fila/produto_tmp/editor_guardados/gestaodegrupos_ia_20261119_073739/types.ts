export interface BriefingData {
  marca: string;
  produto: string;
  publico: string;
  fatos: string[];
  cliente_real: boolean;
  cores: {
    marca: string;
    apoio: string;
    fundo_escuro: string;
    destaque: string;
    texto_sobre_marca: string;
  };
  arroba: string;
  convite: string;
  convite_voz: string;
  titulo: string;
  gancho_tela: string;
  duracao_s: number;
  cenas: Array<{
    n: number;
    ini: number;
    fim: number;
    tipo: string;
    fala: string;
    rotulo: string | null;
    conversa: Array<{ de: string; texto: string }> | null;
    foto?: string;
    video?: string;
  }>;
  palavras: Array<{
    p: string;
    ini: number;
    fim: number;
    cena: number;
    quebraAntes?: boolean;
    quebraApos?: boolean;
    quebraLinha?: boolean;
  }>;
}
