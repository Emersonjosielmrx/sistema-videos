export type Palavra = {
  p: string;
  ini: number;
  fim: number;
  cena: number;
  quebraAntes?: boolean;
  quebraApos?: boolean;
  quebraLinha?: boolean;
};

export type MensagemConversa = {
  de: 'cliente' | 'empresa';
  texto: string;
};

export type CenaBriefing = {
  n: number;
  ini: number;
  fim: number;
  tipo: string;
  fala: string;
  rotulo: string | null;
  conversa: MensagemConversa[] | null;
  foto?: string;
  video?: string;
};

export const CORES = {
  marca: '#E11D48',
  apoio: '#FACC15',
  fundoEscuro: '#31060F',
  destaque: '#E11D48',
  textoSobreMarca: '#FFFFFF',
  whatsappVerde: '#25D366',
  whatsappEscuro: '#075E54',
  cardBg: 'rgba(26, 12, 18, 0.92)',
  cardBorda: 'rgba(244, 63, 94, 0.35)',
};
