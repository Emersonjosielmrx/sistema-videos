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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera dinâmico com push-in contínuo (> 8% variação)
  const scale = interpolate(frame, [0, 170], [1.10, 1.25], {
    extrapolateRight: 'clamp',
  });
  const panY = interpolate(frame, [0, 170], [0, 30], {
    extrapolateRight: 'clamp',
  });

  // Entrada do bloco principal imediata em 0.15s (frame 4) com leve bounce
  const cardSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Microinterações contínuas de pulso e flutuação
  const badgePulse = 1.0 + 0.035 * Math.sin((frame / 20) * Math.PI * 2);
  const cardFloat = Math.sin((frame / 18) * Math.PI * 2) * 5;

  // Entrada dinâmica de notificações nos primeiros 2 segundos para gancho visual e retenção
  const notifInstaSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, stiffness: 150},
  });
  const notifWhatsSpring = spring({
    frame: frame - 24,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Destaques conforme as palavras são ditas
  // Instagram: 2.289s -> frame ~68
  const isInsta = frame >= 68;
  // WhatsApp: 3.046s -> frame ~91
  const isWhats = frame >= 91;
  // juntos?: 3.611s -> frame ~108
  const isJuntos = frame >= 108;
  // Gancho aos 3.8s -> frame ~114
  const isGancho = frame >= 114;

  const juntosSpring = spring({
    frame: frame - 108,
    fps,
    config: {damping: 10, stiffness: 180},
  });

  const ganchoSpring = spring({
    frame: frame - 114,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Fade de saída sutil nos últimos 10 frames
  const sceneOpacity = interpolate(frame, [158, 169], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#0B0D13'}}>
      {/* Foto de fundo tratada como b-roll dinâmico de ambiente profissional */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${scale}) translateY(${panY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(12px) brightness(0.65)',
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
        {/* Iluminação volumétrica da marca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 35%, rgba(91,108,255,0.25) 0%, rgba(11,13,19,0.92) 85%)',
          }}
        />
      </div>

      {/* Conteúdo estritamente dentro da Safe Zone (y=150 a y=1580) */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 20,
        }}
      >
        {/* Badge superior com contraste >= 4.5:1 e tipografia >= 32px */}
        <div
          style={{
            alignSelf: 'flex-start',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 22px',
            borderRadius: 30,
            background: '#5B6CFF',
            boxShadow: '0 8px 24px rgba(91, 108, 255, 0.55)',
            transform: `scale(${badgePulse})`,
            transformOrigin: 'left center',
          }}
        >
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
            Dúvida Frequente
          </span>
        </div>

        {/* Card da pergunta com texto cinético sincrono e microflutuação */}
        <div
          style={{
            width: '100%',
            padding: '24px 28px',
            borderRadius: 24,
            background: 'rgba(17, 24, 39, 0.95)',
            border: '2px solid rgba(255, 255, 255, 0.16)',
            boxShadow: `0 20px 50px rgba(0, 0, 0, 0.85), 0 0 ${16 + 10 * Math.sin(frame / 12)}px rgba(91, 108, 255, 0.35)`,
            transform: `scale(${cardSpring}) translateY(${cardFloat}px)`,
            transformOrigin: 'top center',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              lineHeight: 1.25,
              color: '#FFFFFF',
              textWrap: 'balance',
            }}
          >
            Consigo atender quem vem de anúncios no{' '}
            <span
              style={{
                color: isInsta ? '#FF5483' : '#FFFFFF',
                background: isInsta ? 'rgba(255, 84, 131, 0.22)' : 'transparent',
                padding: isInsta ? '2px 6px' : '0 1px',
                borderRadius: 8,
                transition: 'all 0.15s ease',
              }}
            >
              Instagram
            </span>{' '}
            e no{' '}
            <span
              style={{
                color: isWhats ? '#25D366' : '#FFFFFF',
                background: isWhats ? 'rgba(37, 211, 102, 0.22)' : 'transparent',
                padding: isWhats ? '2px 6px' : '0 1px',
                borderRadius: 8,
                transition: 'all 0.15s ease',
              }}
            >
              WhatsApp
            </span>{' '}
            <span
              style={{
                display: 'inline-block',
                color: '#FFFFFF',
                background: isJuntos ? '#5B6CFF' : 'transparent',
                padding: isJuntos ? '2px 8px' : '0 1px',
                borderRadius: 8,
                transform: isJuntos
                  ? `scale(${interpolate(juntosSpring, [0, 1], [0.8, 1])})`
                  : 'scale(1)',
                boxShadow: isJuntos ? '0 4px 18px rgba(91,108,255,0.6)' : 'none',
              }}
            >
              juntos?
            </span>
          </div>

          {/* Gancho fixo que surge aos 3.8s */}
          {isGancho && (
            <div
              style={{
                marginTop: 18,
                padding: '10px 18px',
                borderRadius: 12,
                background: '#1F2937',
                border: '1.5px solid #5B6CFF',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                transform: `scale(${ganchoSpring})`,
                transformOrigin: 'left center',
              }}
            >
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  background: '#5B6CFF',
                  boxShadow: '0 0 12px #5B6CFF',
                }}
              />
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                }}
              >
                Solução: Atendimento unificado
              </span>
            </div>
          )}
        </div>

        {/* Notificações dinâmicas nos primeiros segundos (Gancho visual de tensão de mensagens) */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
            marginTop: 10,
          }}
        >
          {/* Notificação Instagram */}
          {frame >= 8 && (
            <div
              style={{
                width: '100%',
                padding: '16px 20px',
                borderRadius: 18,
                background: 'rgba(23, 27, 44, 0.94)',
                border: '1.5px solid rgba(255, 84, 131, 0.4)',
                boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5), 0 0 20px rgba(255, 84, 131, 0.25)',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                transform: `scale(${notifInstaSpring})`,
                transformOrigin: 'top center',
              }}
            >
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 14,
                  background: 'linear-gradient(135deg, #FF5483 0%, #D62976 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 26,
                  color: '#FFFFFF',
                  boxShadow: '0 4px 12px rgba(255, 84, 131, 0.5)',
                }}
              >
                📸
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FF5483',
                  }}
                >
                  Direct de Anúncio
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#FFFFFF',
                  }}
                >
                  Cliente solicitando atendimento no Instagram
                </span>
              </div>
            </div>
          )}

          {/* Notificação WhatsApp */}
          {frame >= 24 && (
            <div
              style={{
                width: '100%',
                padding: '16px 20px',
                borderRadius: 18,
                background: 'rgba(20, 32, 28, 0.94)',
                border: '1.5px solid rgba(37, 211, 102, 0.4)',
                boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5), 0 0 20px rgba(37, 211, 102, 0.25)',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                transform: `scale(${notifWhatsSpring})`,
                transformOrigin: 'top center',
              }}
            >
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 14,
                  background: 'linear-gradient(135deg, #25D366 0%, #128C7E 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 26,
                  color: '#FFFFFF',
                  boxShadow: '0 4px 12px rgba(37, 211, 102, 0.5)',
                }}
              >
                💬
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#25D366',
                  }}
                >
                  Mensagem no WhatsApp
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#FFFFFF',
                  }}
                >
                  Cliente aguardando resposta simultânea
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
