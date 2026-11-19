export const CORES = {
  marca: '#8B5CF6', // Roxo vibrante da marca
  marcaClara: '#A78BFA',
  marcaEscura: '#6D28D9',
  apoio: '#1F2937',
  fundoEscuro: '#0F172A',
  destaque: '#8B5CF6',
  texto: '#FFFFFF',
  textoSecundario: '#E2E8F0',
  sucesso: '#10B981',
  alerta: '#F59E0B',
  perigo: '#EF4444',
};

export const CENAS_TIMING = {
  cena0: { ini: 0.0, fim: 4.43 },
  cena1: { ini: 4.08, fim: 12.26 },
  cena2: { ini: 11.91, fim: 20.30 },
  cena3: { ini: 19.95, fim: 28.13 },
  cena4: { ini: 27.78, fim: 31.72 },
};

export const TOTAL_DURACAO_S = 31.72;
export const TOTAL_FRAMES = Math.ceil(TOTAL_DURACAO_S * 30); // 952 frames
