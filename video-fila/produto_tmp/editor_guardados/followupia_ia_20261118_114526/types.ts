export interface BriefingPalavra {
  p: string;
  ini: number;
  fim: number;
  cena: number;
}

export interface BriefingCena {
  n: number;
  ini: number;
  fim: number;
  tipo: 'pergunta' | 'dono' | 'conversa' | 'imagem' | 'real' | 'veo' | 'cartao';
  fala: string;
  rotulo: string | null;
  conversa: Array<{ de: 'cliente' | 'empresa'; texto: string }> | null;
  foto?: string;
  video?: string;
}

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
  cenas: BriefingCena[];
  palavras: BriefingPalavra[];
}
