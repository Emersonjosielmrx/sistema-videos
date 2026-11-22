import React from 'react';
import {
  AbsoluteFill,
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

export const CenaCartao: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com zoom contínuo mais dinâmico
  const bgScale = interpolate(frame, [0, 119], [1.08, 1.28], {
    extrapolateRight: 'clamp',
  });

  // Entrada imediata no frame 0 com pop-in ágil e 100% de opacidade
  const enterSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // Pulso cíclico suave no botão CTA (scale entre 1.0 e 1.04 a cada 45 frames = 1.5s)
  const pulseScale = 1.0 + 0.04 * (0.5 + 0.5 * Math.sin((frame * Math.PI * 2) / 45));

  // Shimmer luminoso varrendo horizontalmente a cada 45 frames (1.5s)
  const shimmerProgress = (frame % 45) / 45;
  const shimmerX = interpolate(shimmerProgress, [0, 1], [-250, 950]);

  // Brilho pulsante no botão
  const glowOpacity = 0.5 + 0.3 * (0.5 + 0.5 * Math.sin((frame * Math.PI * 2) / 45));

  // Microinteração contínua de flutuação para garantir dinamismo entre q13, q14 e q15
  const floatCard = Math.sin(frame / 16) * 6;
  const floatButton = Math.sin((frame + 12) / 16) * 5;
  const floatAt = Math.sin((frame + 24) / 16) * 4;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0B0F19',
        opacity: 1,
      }}
    >
      {/* Imagem de fundo com desfoque e zoom contínuo */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(20px)',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </AbsoluteFill>

      {/* Véu escuro da marca com gradiente esmeralda */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle at 50% 40%, rgba(16, 185, 129, 0.22) 0%, rgba(11, 15, 25, 0.92) 55%, #0B0F19 100%)',
        }}
      />

      {/* Conteúdo na Safe Zone (y: 150 a 1580, x: 60 a 1020) com distribuição vertical equilibrada preenchendo o terço inferior */}
      <AbsoluteFill style={{padding: '0 60px'}}>
        {/* Topo: Badge de Categoria */}
        <div
          style={{
            position: 'absolute',
            top: 195,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: 1,
            transform: `scale(${interpolate(enterSpring, [0, 1], [0.94, 1], {extrapolateRight: 'clamp'})})`,
          }}
        >
          <div
            style={{
              padding: '10px 28px',
              borderRadius: 30,
              background: 'rgba(16, 185, 129, 0.2)',
              border: '1.5px solid rgba(16, 185, 129, 0.7)',
              boxShadow: '0 0 25px rgba(16, 185, 129, 0.35)',
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#34D399',
              textTransform: 'uppercase',
              letterSpacing: 3,
            }}
          >
            Agente Pessoal IA
          </div>
        </div>

        {/* Nome da Marca Grande e Luminoso */}
        <div
          style={{
            position: 'absolute',
            top: 285,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            opacity: 1,
            transform: `scale(${interpolate(enterSpring, [0, 1], [0.94, 1], {extrapolateRight: 'clamp'})})`,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 72,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -1,
              textShadow:
                '0 10px 30px rgba(0, 0, 0, 0.9), 0 0 45px rgba(16, 185, 129, 0.5)',
            }}
          >
            Agentes de IA
          </div>
        </div>

        {/* Card: Proposta de valor com texto complementar em verde luminoso (#00FF88) e fonte ampliada em +24% (42px) */}
        <div
          style={{
            position: 'absolute',
            top: 425,
            left: 70,
            right: 70,
            opacity: 1,
            transform: `scale(${interpolate(enterSpring, [0, 1], [0.94, 1], {extrapolateRight: 'clamp'})}) translateY(${floatCard}px)`,
            borderRadius: 32,
            background: 'rgba(17, 24, 39, 0.96)',
            border: '1.5px solid rgba(16, 185, 129, 0.45)',
            boxShadow:
              '0 25px 60px rgba(0, 0, 0, 0.8), 0 0 35px rgba(16, 185, 129, 0.2)',
            padding: '36px 32px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 16,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 46,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.25,
            }}
          >
            Delegue tarefas reais a um agente IA.
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 42,
              fontWeight: 700,
              color: '#00FF88',
              lineHeight: 1.35,
              textShadow: '0 0 20px rgba(0, 255, 136, 0.35)',
            }}
          >
            Pesquisa, agendamento, follow-up, qualquer coisa da sua rotina.
          </div>
        </div>

        {/* Botão de CTA: Pulso suave cíclico (1.0 a 1.04) e varredura de shimmer contínua a cada 1.5s */}
        <div
          style={{
            position: 'absolute',
            top: 770,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: 1,
            transform: `scale(${interpolate(enterSpring, [0, 1], [0.92, 1], {extrapolateRight: 'clamp'}) * pulseScale}) translateY(${floatButton}px)`,
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: 860,
              height: 135,
              borderRadius: 68,
              background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
              border: '2px solid rgba(255, 255, 255, 0.5)',
              boxShadow: `0 15px 45px rgba(16, 185, 129, ${glowOpacity}), 0 0 35px #00FF88`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 20,
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer sweep animado percorrendo o botão horizontalmente a cada 1.5s */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 220,
                background:
                  'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.75) 50%, transparent 100%)',
                transform: `translateX(${shimmerX}px) skewX(-25deg)`,
                pointerEvents: 'none',
              }}
            />

            {/* Ícone de Direct Message */}
            <svg
              width="46"
              height="46"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>

            {/* Texto do CTA em alto contraste */}
            <span
              style={{
                fontFamily,
                fontSize: 50,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 2,
                textShadow: '0 2px 10px rgba(0, 0, 0, 0.5)',
              }}
            >
              Chame no Direct
            </span>
          </div>
        </div>

        {/* Perfil Oficial @agentesdeia.ia: Exibido IMEDIATAMENTE no frame 1 da cena */}
        <div
          style={{
            position: 'absolute',
            top: 970,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: 1,
            transform: `scale(${interpolate(enterSpring, [0, 1], [0.94, 1], {extrapolateRight: 'clamp'})}) translateY(${floatAt}px)`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 16,
              padding: '18px 42px',
              borderRadius: 40,
              background: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid rgba(16, 185, 129, 0.65)',
              boxShadow:
                '0 12px 35px rgba(0, 0, 0, 0.65), 0 0 30px rgba(16, 185, 129, 0.3)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 1.5,
              }}
            >
              @agentesdeia.ia
            </span>
            {/* Selo Verificado */}
            <svg
              width="36"
              height="36"
              viewBox="0 0 24 24"
              fill="#10B981"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
            </svg>
          </div>
        </div>

        {/* Distribuição no terço inferior (y > 1150) preenchendo o vazio com credibilidade */}
        <div
          style={{
            position: 'absolute',
            top: 1140,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: 1,
            transform: `scale(${interpolate(enterSpring, [0, 1], [0.94, 1], {extrapolateRight: 'clamp'})})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 28px',
              borderRadius: 24,
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.4)',
            }}
          >
            <span style={{fontSize: 26}}>⚡</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#E2E8F0',
              }}
            >
              Comece sua automação agora
            </span>
          </div>
        </div>

        <div
          style={{
            position: 'absolute',
            top: 1250,
            left: 70,
            right: 70,
            display: 'flex',
            justifyContent: 'center',
            textAlign: 'center',
            opacity: 1,
            transform: `scale(${interpolate(enterSpring, [0, 1], [0.94, 1], {extrapolateRight: 'clamp'})})`,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 600,
              color: '#94A3B8',
              letterSpacing: 0.5,
            }}
          >
            Envie uma mensagem e fale direto com a nossa equipe
          </span>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
