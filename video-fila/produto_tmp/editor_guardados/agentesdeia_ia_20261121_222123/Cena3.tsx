import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Escala reduzida para igualar ao plano médio/busto da cena 1 (0.98 a 1.04)
  // Slow push-in digital contínuo ao longo da fala
  const videoScale = interpolate(frame, [0, 241], [0.98, 1.04], {
    extrapolateRight: 'clamp',
  });

  // Enquadramento elevado em 95px (-15px) para desobstruir o queixo do Karaokê e garantir headroom no topo
  const videoTranslateY = -15;

  // Entrada do Badge "O RESULTADO" aos 0.2s (frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título Fixo: "FOCO TOTAL NO SEU NEGÓCIO" (19.81s global = frame 9 local)
  const titleSpring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Elemento dinâmico de apoio 1: Selo de IA em Segundo Plano aos ~2.0s (frame 60)
  const broll1Spring = spring({
    frame: frame - 60,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Elemento dinâmico de apoio 2: Selo de Sucesso / Check aos ~3.8s (frame 115) quando fala "delegando qualquer coisa chata"
  const broll2Spring = spring({
    frame: frame - 115,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Transições de entrada e saída
  const enterOpacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(frame, [228, 241], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0B0F19',
        opacity: Math.min(enterOpacity, exitOpacity),
      }}
    >
      {/* Vídeo do dono em tela cheia com plano médio/busto igualado à Cena 1 e enquadramento elevado (+95px) */}
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: '50% 32%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta superior muito leve */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(180deg, rgba(11, 15, 25, 0.85) 0%, rgba(11, 15, 25, 0.4) 70%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </AbsoluteFill>

      {/* Faixa Superior restrita no topo (y=155): Rosto e olhos 100% livres com respiro */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 20,
        }}
      >
        {/* Badge do Rótulo "O RESULTADO" */}
        <div
          style={{
            opacity: badgeSpring,
            transform: `scale(${interpolate(badgeSpring, [0, 1], [0.85, 1], {extrapolateRight: 'clamp'})})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 24px',
            borderRadius: 24,
            background: 'rgba(16, 185, 129, 0.18)',
            border: '1.5px solid rgba(16, 185, 129, 0.6)',
            boxShadow: '0 4px 20px rgba(16, 185, 129, 0.3)',
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#10B981',
              boxShadow: '0 0 10px #10B981',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#34D399',
              textTransform: 'uppercase',
              letterSpacing: 2,
            }}
          >
            O Resultado
          </span>
        </div>

        {/* Card Superior Fixo mantido durante toda a cena 3 ('FOCO TOTAL NO SEU NEGÓCIO') */}
        <div
          style={{
            marginTop: 12,
            width: '100%',
            maxWidth: 960,
            borderRadius: 24,
            background: 'rgba(17, 24, 39, 0.94)',
            border: '1.5px solid rgba(16, 185, 129, 0.4)',
            boxShadow:
              '0 20px 45px rgba(0, 0, 0, 0.75), 0 0 30px rgba(16, 185, 129, 0.15)',
            padding: '20px 28px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            textAlign: 'center',
            gap: 8,
            opacity: titleSpring,
            transform: `scale(${interpolate(titleSpring, [0, 1], [0.92, 1], {extrapolateRight: 'clamp'})})`,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 42,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              lineHeight: 1.2,
            }}
          >
            Foco total no seu negócio
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 600,
              color: '#34D399',
            }}
          >
            Delegando qualquer coisa chata da rotina
          </div>
        </div>

        {/* Elemento dinâmico de apoio 1: Selo de IA em Segundo Plano aos ~2.0s (frame 60 a 114) */}
        {frame >= 60 && frame < 115 && (
          <div
            style={{
              marginTop: 12,
              opacity: broll1Spring,
              transform: `scale(${interpolate(broll1Spring, [0, 1], [0.85, 1])}) translateY(${interpolate(broll1Spring, [0, 1], [15, 0])}px)`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 24px',
              borderRadius: 20,
              background: 'rgba(16, 185, 129, 0.22)',
              border: '1.5px solid #10B981',
              boxShadow: '0 0 20px rgba(16, 185, 129, 0.4)',
            }}
          >
            <span style={{fontSize: 24}}>🤖</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#34D399',
                textTransform: 'uppercase',
                letterSpacing: 1.5,
              }}
            >
              Agente IA em 2º Plano
            </span>
          </div>
        )}

        {/* Elemento dinâmico de apoio 2: Selo de Sucesso / Check a partir de ~3.8s (frame 115) */}
        {frame >= 115 && (
          <div
            style={{
              marginTop: 12,
              opacity: broll2Spring,
              transform: `scale(${interpolate(broll2Spring, [0, 1], [0.85, 1])}) translateY(${interpolate(broll2Spring, [0, 1], [15, 0])}px)`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 24px',
              borderRadius: 20,
              background: 'rgba(16, 185, 129, 0.25)',
              border: '1.5px solid #10B981',
              boxShadow: '0 0 25px rgba(16, 185, 129, 0.5)',
            }}
          >
            <span style={{fontSize: 24}}>✓</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 1.5,
              }}
            >
              Rotina Liberada • Foco Total
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
