import React from 'react';
import {
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no vídeo: zoom contínuo + corte com aproximação (punch-in de 14%)
  // aos ~4.6s (frame 138) em "eu não conseguia responder e ele desistia" para quebrar a estática e marcar o gargalo
  const punchIn = interpolate(frame, [136, 142], [0, 0.14], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const videoScale =
    interpolate(frame, [0, 240], [1.0, 1.05], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }) + punchIn;

  // Badge do topo (y: 175)
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Estágio 1 da fala: "No pico do movimento" (frame 0 a 70)
  const fase1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Estágio 2 da fala: "mandava só um oi no WhatsApp" (inicia aos ~2.3s / frame 70)
  const fase2Prog = interpolate(frame, [68, 78], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Estágio 3 da fala: "eu não conseguia responder e ele desistia" (inicia aos ~4.7s / frame 140)
  const fase3Prog = interpolate(frame, [138, 148], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#000000',
        fontFamily,
      }}
    >
      {/* Vídeo do Dono da Empresa em tela cheia com leve zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: 'center 45%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Gradiente escuro protetor restrito ao topo (y: 0 a 480) - ROSTO 100% LIVRE */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(11,13,19,0.92) 0%, rgba(11,13,19,0.7) 65%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo estritamente na faixa superior (y: 170 a 430), preservando o rosto do dono */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
        }}
      >
        {/* Rótulo da Cena: O Problema */}
        {badgeSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${badgeSpring})`,
              opacity: badgeSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 24px',
              borderRadius: 50,
              backgroundColor: '#0B0D13F5',
              border: '2px solid #E11D48',
              boxShadow: '0 6px 20px rgba(0,0,0,0.8)',
            }}
          >
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#E11D48',
              }}
            />
            <span
              style={{
                color: '#FFFFFF',
                fontSize: 34,
                fontWeight: 800,
                letterSpacing: '1px',
                textTransform: 'uppercase',
              }}
            >
              O PROBLEMA REAL
            </span>
          </div>
        )}

        {/* Card Dinâmico no Alto (Sincronizado com a narrativa do dono) */}
        {fase1Spring > 0.01 && (
          <div
            style={{
              transform: `scale(${fase1Spring})`,
              opacity: fase1Spring,
              width: '100%',
              backgroundColor: '#0B0D13F5',
              padding: '20px 28px',
              borderRadius: 22,
              border: '2px solid rgba(255, 255, 255, 0.16)',
              boxShadow: '0 14px 35px rgba(0, 0, 0, 0.85)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            {fase3Prog > 0 ? (
              // Fase 3 (frame 140+): "eu não conseguia responder e ele desistia"
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 18,
                  width: '100%',
                  opacity: fase3Prog,
                }}
              >
                <div
                  style={{
                    width: 58,
                    height: 58,
                    borderRadius: 16,
                    backgroundColor: '#E11D48',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 34,
                    color: '#FFFFFF',
                    flexShrink: 0,
                  }}
                >
                  📉
                </div>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span
                    style={{
                      fontSize: 42,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      lineHeight: 1.15,
                    }}
                  >
                    SEM RESPOSTA ➔{' '}
                    <span style={{color: '#FACC15'}}>ELE DESISTIA</span>
                  </span>
                  <span
                    style={{
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#FFA4B4',
                      marginTop: 4,
                    }}
                  >
                    Vendas perdidas no delivery
                  </span>
                </div>
              </div>
            ) : fase2Prog > 0 ? (
              // Fase 2 (frame 70 a 140): "o cliente mandava só um oi no WhatsApp"
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 18,
                  width: '100%',
                  opacity: fase2Prog,
                }}
              >
                <div
                  style={{
                    width: 58,
                    height: 58,
                    borderRadius: 16,
                    backgroundColor: '#25D366',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 34,
                    color: '#FFFFFF',
                    flexShrink: 0,
                  }}
                >
                  💬
                </div>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span
                    style={{
                      fontSize: 42,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      lineHeight: 1.15,
                    }}
                  >
                    MANDAVA SÓ UM OI NO WHATSAPP
                  </span>
                  <span
                    style={{
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#CBD5E1',
                      marginTop: 4,
                    }}
                  >
                    Sem tempo para atendimento manual
                  </span>
                </div>
              </div>
            ) : (
              // Fase 1 (frame 0 a 70): "No pico do movimento"
              <div style={{display: 'flex', alignItems: 'center', gap: 18, width: '100%'}}>
                <div
                  style={{
                    width: 58,
                    height: 58,
                    borderRadius: 16,
                    backgroundColor: '#E11D48',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 34,
                    color: '#FFFFFF',
                    flexShrink: 0,
                  }}
                >
                  🔥
                </div>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span
                    style={{
                      fontSize: 42,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      lineHeight: 1.15,
                    }}
                  >
                    NO PICO DO MOVIMENTO
                  </span>
                  <span
                    style={{
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#CBD5E1',
                      marginTop: 4,
                    }}
                  >
                    Cozinha cheia e pedidos acumulando
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
