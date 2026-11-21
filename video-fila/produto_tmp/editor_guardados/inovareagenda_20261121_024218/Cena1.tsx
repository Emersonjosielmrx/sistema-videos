import React from 'react';
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Img,
  staticFile,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const totalFrames = 232;

  // Câmera dinâmica contínua: pan vertical e zoom suave
  const bgScale = interpolate(frame, [0, totalFrames], [1.06, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, totalFrames], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge superior no frame 6
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Título no frame 10
  const titleSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Entrada do Card 1 aos ~0.4s (frame 14)
  const card1Spring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 14, stiffness: 95},
  });

  // Destaque ativo e pop do Card 1 aos ~2.2s (frame 66, "o horário fica vazio")
  const card1Active = frame >= 66 && frame < 102;
  const card1Pop = spring({
    frame: frame - 66,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Entrada escalonada do Card 2 alinhada com a fala (frame 102, "E eu ainda perdia tempo...")
  const card2Spring = spring({
    frame: frame - 102,
    fps,
    config: {damping: 13, stiffness: 95},
  });

  // Destaque do Card 2 na locução específica
  const card2Active = frame >= 102;

  // Contador de mensagens acumuladas crescendo dinamicamente a partir do frame 106
  const msgCount = Math.min(
    18,
    Math.floor(
      interpolate(frame, [106, 185], [1, 18], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    )
  );

  // Pulso contínuo sutil
  const pulse = Math.sin(frame * 0.16) * 0.03 + 1.0;

  // Saída suave
  const exitOpacity = interpolate(frame, [totalFrames - 10, totalFrames], [1, 0], {
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
        backgroundColor: '#0B0D13',
        opacity: exitOpacity,
      }}
    >
      {/* Imagem de Fundo Clara e Vibrante (Regra 19) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_1.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Vinheta Suave Apenas para Contraste */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(11, 13, 19, 0.80) 0%, rgba(11, 13, 19, 0.30) 35%, rgba(11, 13, 19, 0.42) 65%, rgba(11, 13, 19, 0.84) 100%)',
        }}
      />

      {/* Conteúdo Seguro (y: 175 a 1380) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 175,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* Rótulo Oficial da Cena */}
        {badgeSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${badgeSpring})`,
              opacity: badgeSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 26px',
              borderRadius: 24,
              background: 'rgba(255, 107, 107, 0.22)',
              border: '2px solid #FF6B6B',
              boxShadow: '0 8px 24px rgba(255, 107, 107, 0.3)',
              marginBottom: 16,
            }}
          >
            <span style={{fontSize: 32}}>❌</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FF8787',
                textTransform: 'uppercase',
                letterSpacing: 1.2,
              }}
            >
              O Problema
            </span>
          </div>
        )}

        {/* Título Principal */}
        {titleSpring > 0.01 && (
          <div
            style={{
              transform: `translateY(${(1 - titleSpring) * 20}px)`,
              opacity: titleSpring,
              width: '100%',
              background: 'rgba(15, 23, 42, 0.88)',
              padding: '20px 24px',
              borderRadius: 24,
              border: '1.5px solid rgba(255, 255, 255, 0.12)',
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              textAlign: 'center',
              lineHeight: 1.2,
              textTransform: 'uppercase',
              textShadow: '0 3px 14px rgba(0, 0, 0, 0.9)',
              marginBottom: 26,
              backdropFilter: 'blur(12px)',
            }}
          >
            Quando o cliente não vai,{' '}
            <span style={{color: '#FF6B6B'}}>você perde duas vezes</span>
          </div>
        )}

        {/* Card 1: Cadeira Vazia = Prejuízo */}
        {card1Spring > 0.01 && (
          <div
            style={{
              transform: `translateY(${(1 - card1Spring) * 30}px) scale(${card1Active ? 1.02 + card1Pop * 0.02 : 1.0})`,
              opacity: card1Spring,
              width: 880,
              background: 'rgba(17, 24, 39, 0.96)',
              border: card1Active
                ? '2.5px solid #FF6B6B'
                : '2px solid rgba(255, 107, 107, 0.55)',
              borderRadius: 28,
              padding: '26px 32px',
              boxShadow: card1Active
                ? '0 18px 45px rgba(0, 0, 0, 0.85), 0 0 25px rgba(255, 107, 107, 0.35)'
                : '0 14px 35px rgba(0, 0, 0, 0.75)',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
              marginBottom: 22,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span style={{fontSize: 36}}>⏰</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FF6B6B',
                    textTransform: 'uppercase',
                  }}
                >
                  Cadeira Vazia = Prejuízo
                </span>
              </div>
              <span
                style={{
                  background: 'rgba(255, 107, 107, 0.22)',
                  color: '#FF8787',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  padding: '4px 16px',
                  borderRadius: 12,
                }}
              >
                VAGA PERDIDA
              </span>
            </div>

            <div
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 600,
                color: '#E2E8F0',
                lineHeight: 1.3,
              }}
            >
              Cadeira desocupada e receita perdida no horário agendado.
            </div>
          </div>
        )}

        {/* Card 2: Interrupção Constante */}
        {card2Spring > 0.01 && (
          <div
            style={{
              transform: `translateY(${(1 - card2Spring) * 35}px) scale(${card2Active ? pulse : 1.0})`,
              opacity: card2Spring,
              width: 880,
              background: 'rgba(17, 24, 39, 0.96)',
              border: card2Active
                ? '2.5px solid #F59E0B'
                : '2px solid rgba(245, 158, 11, 0.55)',
              borderRadius: 28,
              padding: '26px 32px',
              boxShadow: card2Active
                ? '0 18px 45px rgba(0, 0, 0, 0.85), 0 0 25px rgba(245, 158, 11, 0.3)'
                : '0 14px 35px rgba(0, 0, 0, 0.75)',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span style={{fontSize: 36}}>💬</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#F59E0B',
                    textTransform: 'uppercase',
                  }}
                >
                  Interrupção Constante
                </span>
              </div>
              <span
                style={{
                  background: 'rgba(245, 158, 11, 0.22)',
                  color: '#FBBF24',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  padding: '4px 16px',
                  borderRadius: 12,
                }}
              >
                MANUAL
              </span>
            </div>

            <div
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 600,
                color: '#E2E8F0',
                lineHeight: 1.3,
              }}
            >
              Parando atendimentos no meio para responder mensagens e remarcar.
            </div>

            {/* Painel de Mensagens Não Lidas Acumulando */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'rgba(0, 0, 0, 0.45)',
                padding: '12px 20px',
                borderRadius: 16,
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#CBD5E1',
                }}
              >
                Mensagens acumulando:
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#F59E0B',
                }}
              >
                +{msgCount} no WhatsApp
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
