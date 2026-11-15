import React from 'react';
import {Audio, Composition, Sequence, staticFile} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Briefing carregado para obter duração exata e palavras
const DURAÇÃO_S = 30.18;
const TOTAL_FRAMES = Math.ceil(DURAÇÃO_S * 30); // 906 frames

// Palavras para o Karaokê (apenas cenas 0 a 3, não exibido no cartão final / cena 4)
const PALAVRAS_KARAOKE = [
  {p: 'Cansado', ini: 0.318, fim: 0.835},
  {p: 'de', ini: 0.847, fim: 0.943},
  {p: 'CRM', ini: 0.955, fim: 1.592},
  {p: 'engessado', ini: 1.604, fim: 2.181},
  {p: 'que', ini: 2.193, fim: 2.289},
  {p: 'sua', ini: 2.301, fim: 2.494},
  {p: 'equipe', ini: 2.506, fim: 2.878},
  {p: 'não', ini: 2.89, fim: 3.07},
  {p: 'consegue', ini: 3.082, fim: 3.551},
  {p: 'usar?', ini: 3.563, fim: 3.912, quebraApos: true},
  {p: 'Sistemas', ini: 5.529, fim: 6.046},
  {p: 'prontos', ini: 6.058, fim: 6.479},
  {p: 'costumam', ini: 6.491, fim: 6.995},
  {p: 'complicar', ini: 7.007, fim: 7.488},
  {p: 'o', ini: 7.5, fim: 7.548},
  {p: 'trabalho', ini: 7.56, fim: 7.993},
  {p: 'diário', ini: 8.005, fim: 8.414},
  {p: 'com', ini: 8.426, fim: 8.618},
  {p: 'telas', ini: 8.63, fim: 8.955},
  {p: 'difíceis', ini: 8.967, fim: 9.507},
  {p: 'que', ini: 9.519, fim: 9.64},
  {p: 'ninguém', ini: 9.652, fim: 9.976},
  {p: 'na', ini: 9.988, fim: 10.06},
  {p: 'empresa', ini: 10.072, fim: 10.445},
  {p: 'preenche.', ini: 10.457, fim: 11.01, quebraApos: true},
  {p: 'Nós', ini: 12.437, fim: 12.629},
  {p: 'criamos', ini: 12.641, fim: 13.05},
  {p: 'uma', ini: 13.062, fim: 13.266},
  {p: 'solução', ini: 13.278, fim: 13.855},
  {p: 'sob', ini: 13.867, fim: 14.12},
  {p: 'medida', ini: 14.132, fim: 14.601},
  {p: 'com', ini: 14.613, fim: 14.757},
  {p: 'inteligência', ini: 14.769, fim: 15.37},
  {p: 'artificial,', ini: 15.382, fim: 16.019},
  {p: 'unindo', ini: 16.259, fim: 16.632},
  {p: 'helpdesk', ini: 16.644, fim: 17.137},
  {p: 'e', ini: 17.149, fim: 17.197},
  {p: 'atendimento', ini: 17.209, fim: 17.834},
  {p: 'na', ini: 17.846, fim: 17.954},
  {p: 'mesma', ini: 17.966, fim: 18.314},
  {p: 'tela.', ini: 18.326, fim: 18.711, quebraApos: true},
  {p: 'Sua', ini: 20.137, fim: 20.401},
  {p: 'rotina', ini: 20.413, fim: 20.846},
  {p: 'fica', ini: 20.858, fim: 21.087},
  {p: 'mais', ini: 21.099, fim: 21.351},
  {p: 'leve', ini: 21.363, fim: 21.724},
  {p: 'com', ini: 21.736, fim: 21.892},
  {p: 'processos', ini: 21.904, fim: 22.409},
  {p: 'adaptados', ini: 22.421, fim: 23.094},
  {p: 'exatamente', ini: 23.106, fim: 23.779},
  {p: 'ao', ini: 23.791, fim: 23.887},
  {p: 'jeito', ini: 23.899, fim: 24.248},
  {p: 'que', ini: 24.26, fim: 24.344},
  {p: 'você', ini: 24.356, fim: 24.632},
  {p: 'já', ini: 24.644, fim: 24.764},
  {p: 'trabalha.', ini: 24.776, fim: 25.293, quebraApos: true},
];

export const Main: React.FC = () => {
  return (
    <div style={{flex: 1, backgroundColor: '#111827'}}>
      {/* Trilha Sonora com volume ajustado e narração completa */}
      <Audio src={staticFile('trilha.mp3')} volume={0.12} />
      <Audio src={staticFile('narracao.mp3')} volume={1.0} />

      {/* Barra de Progresso no topo (y >= 150) */}
      <ProgressBar totalFrames={TOTAL_FRAMES} />

      {/* Cena 0: 0.00s a 5.39s (frames 0 a 162) */}
      <Sequence from={0} durationInFrames={162}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: 5.04s a 12.29s (frames 151 a 369) */}
      <Sequence from={151} durationInFrames={218}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: 11.94s a 19.99s (frames 358 a 600) */}
      <Sequence from={358} durationInFrames={242}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: 19.64s a 26.59s (frames 589 a 798) */}
      <Sequence from={589} durationInFrames={209}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: 26.24s a 30.18s (frames 787 a 906) */}
      <Sequence from={787} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Legenda Karaokê com componente da lib (não exibida no cartão final) */}
      <Sequence from={0} durationInFrames={787}>
        <Karaoke
          palavras={PALAVRAS_KARAOKE}
          fontFamily={fontFamily}
          destaque="#1F93FF"
          textoDestaque="#FFFFFF"
          tamanho={46}
          base={360}
        />
      </Sequence>
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={Main}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
