import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import briefing from '../../../trabalhos/followupia_ia_20261116_052420/public/briefing.json';

import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

const COR_MARCA = briefing.cores.marca; // #4ECDC4
const COR_FUNDO = briefing.cores.fundo_escuro; // #111827
const COR_TEXTO_MARCA = briefing.cores.texto_sobre_marca; // #121216

// Quebras forçadas de bloco para orações lógicas
const QUEBRAS_BLOCO: Record<number, boolean> = {
  6: true, // "no" -> "no mês passado e não comprou"
  12: true, // "Muitos" (Cena 1)
  15: true, // "esfriaram" -> "esfriaram semanas atrás"
  18: true, // "porque" -> "porque não tivemos braço para insistir."
  24: true, // "A" (Cena 2)
  30: true, // "para" -> "para trazer esse público de volta"
  36: true, // "e" -> "e nunca desiste."
  39: true, // "Eu" (Cena 3)
  45: true, // "direto" -> "direto no WhatsApp,"
  48: true, // "a" -> "a partir de cento e noventa e nove reais."
};

// Quebras de linha internas para balancear perfeitamente cada bloco em 2 linhas simétricas
// Eliminando 100% das palavras órfãs (ex: "PREÇO", "INSISTIR.", "WHATSAPP", "VOLTA", "ATRÁS")
const QUEBRAS_LINHA: Record<number, boolean> = {
  3: true, // "quem" -> "DÁ PARA RESGATAR / QUEM PEDIU PREÇO"
  9: true, // "e" -> "NO MÊS PASSADO / E NÃO COMPROU"
  21: true, // "braço" -> "PORQUE NÃO TIVEMOS / BRAÇO PARA INSISTIR."
  27: true, // "mensagens" -> "A IA ENVIA / MENSAGENS NO WHATSAPP"
  33: true, // "público" -> "PARA TRAZER ESSE / PÚBLICO DE VOLTA"
  42: true, // "de" -> "EU RECUPERO VENDAS / DE SEMANAS ATRÁS"
  52: true, // "e" -> "A PARTIR DE CENTO / E NOVENTA E NOVE REAIS."
};

// Apenas palavras das cenas 0 a 3 (o cartão final não exibe legenda)
const PALAVRAS_ATE_CENA_3: PalavraK[] = briefing.palavras
  .filter((w) => w.cena < 4)
  .map((w, idx, arr) => ({
    p: w.p,
    ini: w.ini,
    fim: w.fim,
    quebraAntes: Boolean(
      (idx > 0 && arr[idx - 1].cena !== w.cena) || QUEBRAS_BLOCO[idx]
    ),
    quebraLinha: Boolean(QUEBRAS_LINHA[idx]),
  }));

export const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  // Barra de progresso contínua no topo (Safe Zone y: 150)
  const progresso = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída na trilha sonora
  const volTrilha = interpolate(
    frame,
    [0, 15, durationInFrames - 30, durationInFrames],
    [0, 0.1, 0.1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: COR_FUNDO}}>
      {/* Áudio principal da narração e trilha de fundo */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volTrilha} />

      {/* Cena 0: Pergunta do cliente (0.00s - 5.12s) */}
      <Sequence from={0} durationInFrames={Math.ceil(5.12 * fps)}>
        <Cena0
          fontFamily={fontFamily}
          corMarca={COR_MARCA}
          corFundo={COR_FUNDO}
          corTextoMarca={COR_TEXTO_MARCA}
        />
      </Sequence>

      {/* Cena 1: O problema (4.77s - 12.08s) */}
      <Sequence
        from={Math.floor(4.77 * fps)}
        durationInFrames={Math.ceil((12.08 - 4.77) * fps)}
      >
        <Cena1
          fontFamily={fontFamily}
          corMarca={COR_MARCA}
          corFundo={COR_FUNDO}
          corTextoMarca={COR_TEXTO_MARCA}
        />
      </Sequence>

      {/* Cena 2: Como funciona (11.73s - 19.92s) */}
      <Sequence
        from={Math.floor(11.73 * fps)}
        durationInFrames={Math.ceil((19.92 - 11.73) * fps)}
      >
        <Cena2
          fontFamily={fontFamily}
          corMarca={COR_MARCA}
          corFundo={COR_FUNDO}
          corTextoMarca={COR_TEXTO_MARCA}
        />
      </Sequence>

      {/* Cena 3: O resultado (19.57s - 27.75s) */}
      <Sequence
        from={Math.floor(19.57 * fps)}
        durationInFrames={Math.ceil((27.75 - 19.57) * fps)}
      >
        <Cena3
          fontFamily={fontFamily}
          corMarca={COR_MARCA}
          corFundo={COR_FUNDO}
          corTextoMarca={COR_TEXTO_MARCA}
        />
      </Sequence>

      {/* Cena 4: Cartão Final com CTA e @ (27.40s - 31.34s) */}
      <Sequence
        from={Math.floor(27.4 * fps)}
        durationInFrames={Math.ceil((31.34 - 27.4) * fps)}
      >
        <Cena4
          fontFamily={fontFamily}
          corMarca={COR_MARCA}
          corFundo={COR_FUNDO}
          corTextoMarca={COR_TEXTO_MARCA}
        />
      </Sequence>

      {/* Barra de progresso na Safe Zone (y=150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 8,
          backgroundColor: 'rgba(255,255,255,0.18)',
          borderRadius: 4,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            backgroundColor: COR_MARCA,
            boxShadow: `0 0 8px ${COR_MARCA}`,
          }}
        />
      </div>

      {/* Karaokê ativo até o final da cena 3 (desativado no cartão final) */}
      {/* Base elevada para 450px para respeitar rigorosamente a Safe Zone do Reels */}
      <Sequence from={0} durationInFrames={Math.floor(27.4 * fps)}>
        <Karaoke
          palavras={PALAVRAS_ATE_CENA_3}
          fontFamily={fontFamily}
          destaque={COR_MARCA}
          textoDestaque={COR_TEXTO_MARCA}
          tamanho={40}
          base={450}
          maxLetras={55}
          pausaQuebra={1.2}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={VideoPrincipal}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
