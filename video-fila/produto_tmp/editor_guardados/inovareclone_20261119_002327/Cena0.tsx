import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES} from './constants';

interface Cena0Props {
  fontFamily: string;
}

export const Cena0: React.FC<Cena0Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera cinematográfico contínuo no fundo
  const bgScale = interpolate(frame, [0, 135], [1.02, 1.12], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 135], [0, -18], {
    extrapolateRight: 'clamp',
  });

  // Fade out de saída para a cena 1 (frames 122 a 133)
  const exitOpacity = interpolate(frame, [122, 133], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação dos elementos (Composição a - Texto Gigante sobre foto escurecida)
  // 1. Badge superior "PERGUNTA FREQUENTE" (entra frame 4)
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 2. Linha 1: "VOU ME LIVRAR DE TER QUE" (entra frame 10, ~0.33s)
  const l1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // 3. Linha 2: "MONTAR CENÁRIO" (entra frame 43, ~1.43s)
  const l2Spring = spring({
    frame: frame - 43,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 4. Linha 3: "TODA VEZ?" (entra frame 67, ~2.23s)
  const l3Spring = spring({
    frame: frame - 67,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // 5. Gancho de tela fixo "SEU AVATAR COM IA TODO DIA" (entra frame 82, ~2.7s)
  const ganchoSpring = spring({
    frame: frame - 82,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Micro-pulso no destaque de cenário
  const pulseDestaque = 1.0 + Math.sin(frame * 0.15) * 0.02;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: CORES.fundoEscuro,
        opacity: exitOpacity,
        fontFamily,
      }}
    >
      {/* Imagem de fundo com câmera contínua */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta escura no topo (y=0 a 650) garantindo contraste 100% legível,
            mantendo o apresentador e o laptop visíveis e nítidos abaixo */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(15, 23, 42, 0.90) 0%, rgba(15, 23, 42, 0.70) 35%, rgba(15, 23, 42, 0.45) 60%, rgba(15, 23, 42, 0.88) 100%)',
          }}
        />
      </div>

      {/* Conteúdo sobreposto — Topo y=175 a 580 (protegendo totalmente a pessoa no laptop) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Badge do Gancho */}
        <div
          style={{
            marginTop: 175,
            opacity: interpolate(badgeSpring, [0, 1], [0, 1]),
            transform: `scale(${badgeSpring})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 24px',
            borderRadius: 999,
            backgroundColor: 'rgba(31, 41, 55, 0.92)',
            border: `1.5px solid ${CORES.marcaClara}`,
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span style={{fontSize: 32}}>❓</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            Pergunta Frequente
          </span>
        </div>

        {/* Bloco de Texto Cinético GIGANTE */}
        <div
          style={{
            marginTop: 30,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 14,
            textAlign: 'center',
            width: '100%',
          }}
        >
          {/* Linha 1 */}
          <div
            style={{
              opacity: interpolate(l1Spring, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(l1Spring, [0, 1], [25, 0])}px)`,
              fontSize: 42,
              fontWeight: 800,
              color: '#E2E8F0',
              textTransform: 'uppercase',
              letterSpacing: '-0.5px',
              textShadow: '0 4px 12px rgba(0,0,0,0.9)',
            }}
          >
            Vou me livrar de ter que
          </div>

          {/* Linha 2 (Destaque Marca-Texto Gigante) */}
          <div
            style={{
              opacity: interpolate(l2Spring, [0, 1], [0, 1]),
              transform: `scale(${interpolate(l2Spring, [0, 1], [0.85, 1]) * pulseDestaque})`,
              display: 'inline-block',
              background: `linear-gradient(90deg, ${CORES.marcaEscura}, ${CORES.marca})`,
              padding: '12px 32px',
              borderRadius: 20,
              fontSize: 66,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: '-1px',
              boxShadow: '0 12px 35px rgba(109, 40, 217, 0.7)',
              border: '2px solid rgba(255, 255, 255, 0.25)',
            }}
          >
            Montar Cenário
          </div>

          {/* Linha 3 (Alerta / Pergunta) */}
          <div
            style={{
              opacity: interpolate(l3Spring, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(l3Spring, [0, 1], [20, 0])}px)`,
              fontSize: 54,
              fontWeight: 900,
              color: '#F87171',
              textTransform: 'uppercase',
              letterSpacing: '0px',
              textShadow: '0 4px 15px rgba(239, 68, 68, 0.6)',
            }}
          >
            Toda Vez?
          </div>
        </div>

        {/* Gancho de Tela Fixo (entra a 2.7s) */}
        {frame >= 80 && (
          <div
            style={{
              marginTop: 28,
              opacity: interpolate(ganchoSpring, [0, 1], [0, 1]),
              transform: `scale(${interpolate(ganchoSpring, [0, 1], [0.9, 1])})`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 30px',
              borderRadius: 999,
              backgroundColor: 'rgba(139, 92, 246, 0.35)',
              border: `2px solid ${CORES.marcaClara}`,
              boxShadow: '0 8px 25px rgba(139, 92, 246, 0.5)',
            }}
          >
            <span style={{fontSize: 34}}>✨</span>
            <span
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              Seu avatar com IA todo dia
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
