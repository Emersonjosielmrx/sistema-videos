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

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Corte de câmera alternado (escala 1.05x -> 1.08x): dinamismo de corte entre Cena 1 (1.0x) e Cena 2 (1.15x)
  const videoScale = interpolate(frame, [0, 245], [1.05, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave na transição para o cartão final (últimos 10 frames)
  const sceneOpacity = interpolate(frame, [235, 245], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Header "03 · O RESULTADO"
  const headerSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Tópico 1: "Tudo direto no WhatsApp" (~frame 30)
  const whatsSpring = spring({
    frame: frame - 30,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Micro-elemento animado aos ~frame 105: dinamismo contínuo eliminando estagnação
  const syncSpring = spring({
    frame: frame - 105,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Card 1: "Sem Conflito de Horários" (~frame 170)
  const semConflitoSpring = spring({
    frame: frame - 170,
    fps,
    config: {damping: 10, stiffness: 150},
  });

  // Card 2: "Sem Duplo Agendamento" (~frame 198)
  const semDuploSpring = spring({
    frame: frame - 198,
    fps,
    config: {damping: 10, stiffness: 150},
  });

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, overflow: 'hidden'}}>
      {/* Vídeo do dono em tela cheia com movimento contínuo */}
      <AbsoluteFill style={{transform: `scale(${videoScale})`}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{width: '1080px', height: '1920px', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Gradiente superior sutil para máxima legibilidade */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 390,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.75) 0%, rgba(15, 23, 42, 0.35) 60%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo informativo (y=165 a 380) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
        }}
      >
        {/* Rótulo da etapa */}
        <div
          style={{
            transform: `scale(${Math.max(0, headerSpring)})`,
            opacity: headerSpring,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 20px',
            borderRadius: 999,
            background: 'rgba(31, 41, 55, 0.90)',
            border: '1.5px solid rgba(255, 169, 77, 0.5)',
            boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFA94D',
              textTransform: 'uppercase',
              letterSpacing: 1.2,
            }}
          >
            03 · O Resultado
          </span>
        </div>

        {/* Tópico 1: Notificação / Card Direto no WhatsApp (frame 30 a 105) */}
        {frame >= 30 && frame < 105 && (
          <div
            style={{
              transform: `scale(${Math.max(0, whatsSpring)})`,
              opacity: whatsSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 26px',
              borderRadius: 20,
              background: 'rgba(31, 41, 55, 0.92)',
              border: '2px solid rgba(34, 197, 94, 0.6)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            }}
          >
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
                fontSize: 34,
                fontWeight: 800,
                color: '#F8FAFC',
                textTransform: 'uppercase',
              }}
            >
              Direto no WhatsApp
            </span>
          </div>
        )}

        {/* Micro-elemento dinâmico (frame 105 a 170): sincronização ativa com rotação sutil eliminando o congelamento */}
        {frame >= 105 && frame < 170 && (
          <div
            style={{
              transform: `scale(${Math.max(0, syncSpring)})`,
              opacity: syncSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              padding: '12px 26px',
              borderRadius: 20,
              background: 'rgba(15, 23, 42, 0.94)',
              border: '2px solid rgba(255, 169, 77, 0.7)',
              boxShadow: '0 8px 26px rgba(255, 169, 77, 0.35)',
            }}
          >
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFA94D"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{
                transform: `rotate(${((frame - 105) * 3) % 360}deg)`,
              }}
            >
              <polyline points="23 4 23 10 17 10" />
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
            </svg>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFA94D',
                textTransform: 'uppercase',
                letterSpacing: 0.8,
              }}
            >
              Sincronização em Tempo Real
            </span>
          </div>
        )}

        {/* Pilha de Validações: Sem Conflito & Sem Duplo Agendamento (frame 170 em diante) */}
        {frame >= 170 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 10,
              width: '100%',
              maxWidth: 920,
            }}
          >
            {/* Card 1: SEM CONFLITO */}
            <div
              style={{
                transform: `scale(${Math.max(0, semConflitoSpring)})`,
                opacity: semConflitoSpring,
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '10px 24px',
                borderRadius: 18,
                background: 'rgba(15, 23, 42, 0.94)',
                border: '2px solid #22C55E',
                boxShadow: '0 6px 20px rgba(34, 197, 94, 0.3)',
              }}
            >
              <span
                style={{
                  color: '#22C55E',
                  fontSize: 36,
                  fontWeight: 900,
                }}
              >
                ✓
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: 0.8,
                }}
              >
                Sem Conflito de Horários
              </span>
            </div>

            {/* Card 2: SEM DUPLO AGENDAMENTO */}
            {frame >= 198 && (
              <div
                style={{
                  transform: `scale(${Math.max(0, semDuploSpring)})`,
                  opacity: semDuploSpring,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                  padding: '10px 24px',
                  borderRadius: 18,
                  background: 'rgba(15, 23, 42, 0.94)',
                  border: '2px solid #FFA94D',
                  boxShadow: '0 6px 20px rgba(255, 169, 77, 0.3)',
                }}
              >
                <span
                  style={{
                    color: '#FFA94D',
                    fontSize: 36,
                    fontWeight: 900,
                  }}
                >
                  ✓
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                    letterSpacing: 0.8,
                  }}
                >
                  Sem Duplo Agendamento
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
