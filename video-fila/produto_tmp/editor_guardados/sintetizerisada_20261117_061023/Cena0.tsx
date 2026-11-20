import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom contínuo no vídeo do apresentador (elimina tela preta estática)
  const bgScale = interpolate(frame, [0, 116], [1.02, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave na transição para a cena 1
  const sceneOpacity = interpolate(frame, [106, 116], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Transição de saída do overlay escuro (revela o apresentador naturalmente antes do corte)
  const overlayOpacity = interpolate(frame, [88, 112], [0.72, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Saída animada dos elementos da pergunta em slide-up antes do corte
  const hookExitTranslateY = interpolate(frame, [88, 112], [0, -60], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const hookExitOpacity = interpolate(frame, [88, 110], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Saída animada do card do WhatsApp
  const cardExitTranslateY = interpolate(frame, [88, 112], [0, 50], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cardExitOpacity = interpolate(frame, [88, 110], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Gancho inicial: Entrada rápida e completa (<0.25s) para prender a retenção imediata
  const hookSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Card de demonstração do WhatsApp na metade inferior (frame 38)
  const cardSpring = spring({
    frame: frame - 38,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Balão 2 de resposta automática da IA (frame 62)
  const iaReplySpring = spring({
    frame: frame - 62,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, overflow: 'hidden'}}>
      {/* Fundo com vídeo real do apresentador na barbearia (presença humana dinâmica desde o frame 0) */}
      <AbsoluteFill style={{transform: `scale(${bgScale})`}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Véu escuro equilibrado com fade-out antes da transição da cena 1 */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.88) 0%, rgba(15, 23, 42, 0.68) 45%, rgba(15, 23, 42, 0.90) 100%)',
          opacity: overlayOpacity,
        }}
      />

      {/* Topo informativo: Pergunta de Impacto Completa desde 0.0s (Safe Zone y=175 a 450, rosto 100% livre) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          gap: 16,
          transform: `translateY(${hookExitTranslateY}px)`,
          opacity: hookExitOpacity,
        }}
      >
        {/* Badge da marca */}
        <div
          style={{
            transform: `scale(${Math.max(0, hookSpring)})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 22px',
            borderRadius: 999,
            background: 'rgba(31, 41, 55, 0.92)',
            border: '1.5px solid rgba(255, 169, 77, 0.7)',
            boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#FFA94D',
              boxShadow: '0 0 10px #FFA94D',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Agenda IA
          </span>
        </div>

        {/* Linha 1 da dor: "MEDO DE SISTEMA" (Tipografia limpa e corporativa, sem emojis informais) */}
        <div
          style={{
            transform: `scale(${Math.max(0, hookSpring)})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 76,
              fontWeight: 900,
              color: '#FF6B6B',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
              textShadow: '0 10px 30px rgba(255, 107, 107, 0.45)',
            }}
          >
            MEDO
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 60,
              fontWeight: 800,
              color: '#F8FAFC',
              letterSpacing: 1,
              textTransform: 'uppercase',
              textShadow: '0 6px 18px rgba(0,0,0,0.8)',
            }}
          >
            DE SISTEMA
          </span>
        </div>

        {/* Linha 2 da dor: "DIFÍCIL DE MEXER?" (visível de imediato no gancho dos 2s) */}
        <div
          style={{
            transform: `scale(${Math.max(0, hookSpring)}) rotate(-1deg)`,
            background: '#FFA94D',
            padding: '10px 32px',
            borderRadius: 18,
            boxShadow: '0 12px 36px rgba(255, 169, 77, 0.45)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 64,
              fontWeight: 900,
              color: '#1F2937',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            DIFÍCIL DE MEXER?
          </span>
        </div>
      </div>

      {/* Card de Simulação do WhatsApp posicionado na metade inferior (y entre 1260 e 1520) */}
      {/* Aproveita a área sobre o peito e a bancada, deixando o rosto do apresentador (y=450 a 1150) totalmente livre */}
      {frame >= 38 && (
        <div
          style={{
            position: 'absolute',
            top: 1260,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            transform: `translateY(${cardExitTranslateY}px) scale(${Math.max(0, cardSpring)})`,
            opacity: cardSpring * cardExitOpacity,
            zIndex: 30,
          }}
        >
          <div
            style={{
              background: 'rgba(31, 41, 55, 0.95)',
              border: '2px solid rgba(34, 197, 94, 0.7)',
              borderRadius: 24,
              padding: '16px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
              width: '100%',
              maxWidth: 920,
              boxShadow: '0 16px 44px rgba(0,0,0,0.7)',
            }}
          >
            {/* Header da Simulação WhatsApp */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                paddingBottom: 10,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <svg
                  width="28"
                  height="28"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#22C55E"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#22C55E',
                  }}
                >
                  WhatsApp
                </span>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#94A3B8',
                  background: 'rgba(15, 23, 42, 0.7)',
                  padding: '4px 14px',
                  borderRadius: 10,
                }}
              >
                Simulação
              </span>
            </div>

            {/* Mensagem 1 do Cliente */}
            <div
              style={{
                display: 'flex',
                alignSelf: 'flex-start',
                background: 'rgba(15, 23, 42, 0.85)',
                padding: '12px 18px',
                borderRadius: '16px 16px 16px 4px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#F8FAFC',
                }}
              >
                "Quero agendar meu horário"
              </span>
            </div>

            {/* Mensagem 2 da IA respondendo automaticamente (expande para baixo sem tocar o rosto) */}
            {frame >= 62 && (
              <div
                style={{
                  transform: `scale(${Math.max(0, iaReplySpring)})`,
                  opacity: iaReplySpring,
                  display: 'flex',
                  alignSelf: 'flex-end',
                  alignItems: 'center',
                  gap: 10,
                  background: 'rgba(22, 101, 52, 0.90)',
                  border: '1.5px solid #22C55E',
                  padding: '12px 20px',
                  borderRadius: '16px 16px 4px 16px',
                  boxShadow: '0 6px 20px rgba(34, 197, 94, 0.35)',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  ✓ Confirmado! Agendado direto no WhatsApp
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
