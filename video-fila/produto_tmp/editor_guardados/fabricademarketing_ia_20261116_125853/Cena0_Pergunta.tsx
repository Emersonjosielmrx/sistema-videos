import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0_Pergunta: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (1.00 -> 1.07)
  const bgScale = interpolate(frame, [0, 177], [1.0, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Entrada ágil do card logo aos 0.1s (frame 3) para retenção imediata
  const cardSpring = spring({
    frame: Math.max(0, frame - 3),
    fps,
    config: {damping: 13, stiffness: 140},
  });
  const cardScale = interpolate(cardSpring, [0, 1], [0.86, 1.0]);
  const cardOpacity = interpolate(cardSpring, [0, 1], [0, 1]);

  // Movimento dinâmico contínuo do card ao longo da cena
  const cardDrift = interpolate(frame, [0, 177], [1.0, 1.03], {
    extrapolateRight: 'clamp',
  });

  // Destaque cinético para "vários canais ativos" (~1.12s -> frame 34)
  const highlight1Spring = spring({
    frame: Math.max(0, frame - 34),
    fps,
    config: {damping: 14, stiffness: 150},
  });

  // Destaque cinético para "único responsável" (~2.68s -> frame 80)
  const highlight2Spring = spring({
    frame: Math.max(0, frame - 80),
    fps,
    config: {damping: 14, stiffness: 150},
  });

  // Saída suave nos últimos 12 frames
  const exitOpacity = interpolate(frame, [165, 177], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
        opacity: exitOpacity,
      }}
    >
      {/* Imagem de Fundo com Zoom Dinâmico Contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
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
        {/* Glow dinâmico vivo em movimento para quebrar efeito de slide inerte */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(circle at ${50 + Math.sin(frame * 0.04) * 8}% ${40 + Math.cos(frame * 0.04) * 6}%, rgba(244, 114, 182, 0.25) 0%, rgba(17, 24, 39, 0.8) 60%, rgba(17, 24, 39, 0.96) 100%)`,
          }}
        />
      </div>

      {/* Topo: Pill fixo e estável desde o frame 0 (sem troca brusca) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 40,
        }}
      >
        <div
          style={{
            padding: '12px 28px',
            borderRadius: 24,
            backgroundColor: '#F472B6',
            color: '#111827',
            fontSize: 34,
            fontWeight: 900,
            letterSpacing: 0.5,
            textTransform: 'uppercase',
            boxShadow: '0 8px 25px rgba(244, 114, 182, 0.45)',
          }}
        >
          🔥 Vários canais sozinho?
        </div>
      </div>

      {/* Card Central de Pergunta Autêntico (y=440 a 1080) */}
      <div
        style={{
          position: 'absolute',
          top: 450,
          left: 60,
          right: 60,
          opacity: cardOpacity,
          transform: `scale(${cardScale * cardDrift})`,
          backgroundColor: 'rgba(17, 24, 39, 0.90)',
          borderRadius: 36,
          border: '1.5px solid rgba(244, 114, 182, 0.45)',
          padding: '48px 42px',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.65), 0 0 30px rgba(244, 114, 182, 0.15)',
          backdropFilter: 'blur(20px)',
          zIndex: 30,
        }}
      >
        {/* Cabeçalho do Card (Sem @ ilegal e com português correto) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 36,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: 32,
                backgroundColor: '#F472B6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#111827',
                fontSize: 34,
                fontWeight: 900,
                boxShadow: '0 0 18px rgba(244, 114, 182, 0.5)',
              }}
            >
              👤
            </div>
            <div>
              <div style={{fontSize: 36, fontWeight: 800, color: '#FFFFFF'}}>
                Empreendedor Solo
              </div>
              <div style={{fontSize: 32, color: '#9CA3AF', fontWeight: 600}}>
                Dúvida do Gestor
              </div>
            </div>
          </div>
          <div
            style={{
              padding: '10px 22px',
              borderRadius: 18,
              backgroundColor: 'rgba(244, 114, 182, 0.2)',
              border: '1.5px solid #F472B6',
              color: '#F472B6',
              fontSize: 32,
              fontWeight: 800,
            }}
          >
            Pergunta
          </div>
        </div>

        {/* Texto Cinético da Pergunta — Focado e Puro, sem poluição de tags */}
        <div
          style={{
            fontSize: 50,
            fontWeight: 800,
            lineHeight: 1.32,
            color: '#FFFFFF',
            textWrap: 'balance',
          }}
        >
          <span>Consigo manter </span>
          <span
            style={{
              backgroundColor: highlight1Spring > 0.05 ? '#F472B6' : 'transparent',
              color: highlight1Spring > 0.05 ? '#111827' : '#FFFFFF',
              padding: '3px 10px',
              borderRadius: 10,
              boxShadow: highlight1Spring > 0.05 ? '0 4px 18px rgba(244, 114, 182, 0.5)' : 'none',
              transition: 'background-color 0.15s',
            }}
          >
            vários canais ativos
          </span>
          <span> sendo o </span>
          <span
            style={{
              backgroundColor: highlight2Spring > 0.05 ? '#F472B6' : 'transparent',
              color: highlight2Spring > 0.05 ? '#111827' : '#FFFFFF',
              padding: '3px 10px',
              borderRadius: 10,
              boxShadow: highlight2Spring > 0.05 ? '0 4px 18px rgba(244, 114, 182, 0.5)' : 'none',
              transition: 'background-color 0.15s',
            }}
          >
            único responsável
          </span>
          <span> pela empresa?</span>
        </div>
      </div>
    </div>
  );
};
