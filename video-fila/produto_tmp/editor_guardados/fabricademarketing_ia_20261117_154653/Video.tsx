import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {CORES, DURACOES} from './constants';
import {ProgressBar} from './ProgressBar';
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Dono} from './Cena1Dono';
import {Cena2Conversa} from './Cena2Conversa';
import {Cena3Dono} from './Cena3Dono';
import {Cena4Cartao} from './Cena4Cartao';

const {fontFamily} = loadFont();

// Palavras oficiais da locução divididas estritamente por sintagmas perfeitos (sem artigos ou palavras órfãs)
const PALAVRAS_KARAOKE: PalavraK[] = [
  // Cena 0: Pergunta
  {p: 'Como', ini: 0.318, fim: 0.558},
  {p: 'responder', ini: 0.57, fim: 1.087},
  {p: 'comentários', ini: 1.099, fim: 1.724, quebraLinha: true},
  {p: 'nos', ini: 1.736, fim: 1.905},
  {p: 'posts', ini: 1.917, fim: 2.301, quebraApos: true},
  {p: 'enquanto', ini: 2.313, fim: 2.758},
  {p: 'estou', ini: 2.77, fim: 2.998},
  {p: 'atendendo', ini: 3.01, fim: 3.503, quebraLinha: true},
  {p: 'clientes', ini: 3.515, fim: 4.164, quebraApos: true},

  // Cena 1: Dono (A rotina)
  {p: 'Quando', ini: 6.126, fim: 6.726},
  {p: 'estou', ini: 6.726, fim: 6.946},
  {p: 'atendendo', ini: 6.946, fim: 7.346, quebraApos: true},
  {p: 'um', ini: 7.346, fim: 7.546},
  {p: 'cliente', ini: 7.546, fim: 7.866},
  {p: 'na', ini: 7.866, fim: 8.006},
  {p: 'empresa,', ini: 8.006, fim: 8.486, quebraApos: true},
  {p: 'os', ini: 9.286, fim: 9.466},
  {p: 'comentários', ini: 9.466, fim: 10.026},
  {p: 'pedindo', ini: 10.026, fim: 10.546},
  {p: 'detalhes', ini: 10.546, fim: 11.186, quebraApos: true},
  {p: 'nas', ini: 11.186, fim: 11.346},
  {p: 'postagens', ini: 11.346, fim: 12.006, quebraLinha: true},
  {p: 'ficavam', ini: 12.006, fim: 12.526},
  {p: 'esperando.', ini: 12.526, fim: 13.026, quebraApos: true},

  // Cena 2: Conversa (O atendimento)
  {p: 'Na', ini: 13.602, fim: 13.746},
  {p: 'Fábrica', ini: 13.758, fim: 14.191},
  {p: 'de', ini: 14.203, fim: 14.287},
  {p: 'Conteúdo', ini: 14.299, fim: 14.948, quebraApos: true},
  {p: 'o', ini: 15.201, fim: 15.261},
  {p: 'agente', ini: 15.273, fim: 15.669},
  {p: 'de', ini: 15.681, fim: 15.754},
  {p: 'respostas', ini: 15.766, fim: 16.33, quebraLinha: true},
  {p: 'atende', ini: 16.342, fim: 16.775},
  {p: 'os', ini: 16.787, fim: 16.859},
  {p: 'comentários', ini: 16.871, fim: 17.448, quebraApos: true},
  {p: 'enquanto', ini: 17.46, fim: 17.893},
  {p: 'o', ini: 17.905, fim: 17.941},
  {p: 'blog', ini: 17.953, fim: 18.302},
  {p: 'com', ini: 18.314, fim: 18.47},
  {p: 'SEO', ini: 18.482, fim: 18.806, quebraLinha: true},
  {p: 'e', ini: 18.855, fim: 18.915},
  {p: 'o', ini: 18.927, fim: 18.987},
  {p: 'podcast', ini: 18.999, fim: 19.612},
  {p: 'rodam', ini: 19.624, fim: 20.068, quebraApos: true},

  // Cena 3: Dono (O resultado)
  {p: 'Hoje', ini: 21.561, fim: 22.341},
  {p: 'eu', ini: 22.541, fim: 22.681},
  {p: 'sigo', ini: 22.681, fim: 22.921},
  {p: 'focado', ini: 22.921, fim: 23.361, quebraLinha: true},
  {p: 'no', ini: 23.361, fim: 23.521},
  {p: 'meu', ini: 23.521, fim: 23.701},
  {p: 'trabalho', ini: 23.701, fim: 24.141, quebraApos: true},
  {p: 'e', ini: 24.141, fim: 24.821},
  {p: 'quem', ini: 24.821, fim: 25.081},
  {p: 'comenta', ini: 25.081, fim: 25.821, quebraLinha: true},
  {p: 'recebe', ini: 25.821, fim: 26.341},
  {p: 'atenção', ini: 26.341, fim: 26.901, quebraApos: true},
  {p: 'com', ini: 26.901, fim: 27.241},
  {p: 'tudo', ini: 27.241, fim: 27.441},
  {p: 'automatizado.', ini: 27.441, fim: 28.181, quebraApos: true},
];

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Volume da trilha: ~0.10 durante a fala, sobe para ~0.20 no cartão final
  const volumeTrilha = interpolate(
    frame,
    [0, 15, 860, 875, 960, 984],
    [0, 0.1, 0.1, 0.2, 0.2, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundoEscuro}}>
      {/* Narração Completa do Vídeo */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha Sonora Instrumental de Fundo */}
      <Audio src={staticFile('trilha.mp3')} volume={volumeTrilha} />

      {/* Barra de Progresso no Topo (y >= 150) */}
      <ProgressBar />

      {/* CENA 0: Pergunta (0.00s a 5.63s — frames 0 a 169) */}
      <Sequence from={0} durationInFrames={169} name="Cena 0 - Pergunta">
        <Cena0Pergunta fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 1: Dono - A Rotina (5.28s a 13.46s — frames 158 a 403) */}
      <Sequence from={158} durationInFrames={245} name="Cena 1 - Dono">
        <Cena1Dono fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 2: Conversa - O Atendimento (13.11s a 21.35s — frames 393 a 640) */}
      <Sequence from={393} durationInFrames={247} name="Cena 2 - Conversa">
        <Cena2Conversa fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 3: Dono - O Resultado (21.00s a 29.18s — frames 630 a 875) */}
      <Sequence from={630} durationInFrames={245} name="Cena 3 - Dono">
        <Cena3Dono fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 4: Cartão Final (28.83s a 32.78s — frames 865 a 984) */}
      <Sequence from={865} durationInFrames={119} name="Cena 4 - Cartão Final">
        <Cena4Cartao fontFamily={fontFamily} />
      </Sequence>

      {/* Karaokê Oficial Sincronizado (Ativo apenas nas cenas 0, 1, 2 e 3; oculto no cartão final) */}
      {frame < 865 && (
        <Karaoke
          palavras={PALAVRAS_KARAOKE}
          fontFamily={fontFamily}
          destaque={CORES.destaque}
          textoDestaque="#111827"
          tamanho={44}
          base={360}
          maxLetras={32}
          pausaQuebra={0.5}
        />
      )}
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainVideo}
      fps={DURACOES.fps}
      width={1080}
      height={1920}
      durationInFrames={DURACOES.totalFrames}
    />
  );
};
