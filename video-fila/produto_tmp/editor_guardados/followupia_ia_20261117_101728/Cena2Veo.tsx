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

export const Cena2Veo: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous push-in zoom on background b-roll video
  const videoScale = interpolate(frame, [0, 240], [1.02, 1.1], {
    extrapolateRight: 'clamp',
  });

  // Top Section Badge entrance ("A SOLUÇÃO INTELIGENTE") at frame 5
  const badgeSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Phone Mockup container entrance at frame 10 (0.33s)
  const phoneSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Speech timing in Scene 2 (ini: 12.22s):
  // 14.709s: "assume essa rotina no WhatsApp" -> relative frame = (14.709 - 12.22) * 30 = ~75
  // Typing indicator before balloon 1: relative frames 50 to 74
  const showTyping1 = frame >= 50 && frame < 75;

  // Balloon 1 (AI Follow-up) entrance at frame 75
  const balloon1Spring = spring({
    frame: frame - 75,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Speech timing:
  // 16.656s: "trazendo contatos parados" -> relative frame = (16.656 - 12.22) * 30 = ~133
  // Typing indicator before balloon 2: relative frames 115 to 134
  const showTyping2 = frame >= 115 && frame < 135;

  // Balloon 2 (Client Reply) entrance at frame 135
  const balloon2Spring = spring({
    frame: frame - 135,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Success banner ("Lead Reativado para Negociar!") at 18.0s: (18.0 - 12.22)*30 = ~174
  const statusSpring = spring({
    frame: frame - 174,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Micro floating motion
  const floatY = Math.sin(frame / 14) * 5;

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', overflow: 'hidden'}}>
      {/* Background B-roll video with subtle blur and dark overlay */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: 'center center',
          filter: 'blur(3px)',
        }}
      >
        <OffthreadVideo
          src={staticFile('video_2.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(17, 24, 39, 0.8)',
          }}
        />
      </div>

      {/* Top Section Badge: A SOLUÇÃO INTELIGENTE (y=175) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 26px',
            backgroundColor: 'rgba(78, 205, 196, 0.22)',
            border: '2px solid #4ECDC4',
            borderRadius: 24,
            backdropFilter: 'blur(10px)',
          }}
        >
          <span style={{fontSize: 26}}>⚡</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            A Solução Inteligente
          </span>
        </div>
      </div>

      {/* Modern Smartphone / WhatsApp Interface Mockup */}
      {/* Positioned between y=245 and y=1100 to strictly protect Karaoke zone (y=1320..1580) */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 80,
          right: 80,
          height: 850,
          transform: `translateY(${floatY}px) scale(${phoneSpring})`,
          opacity: phoneSpring,
          backgroundColor: '#1E293B',
          borderRadius: 40,
          border: '4px solid rgba(78, 205, 196, 0.55)',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.75)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* WhatsApp Top Header */}
        <div
          style={{
            backgroundColor: '#0F172A',
            padding: '18px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '2px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 54,
                height: 54,
                borderRadius: '50%',
                backgroundColor: '#4ECDC4',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
              }}
            >
              🤖
            </div>
            <div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span>Follow-up IA</span>
                <span style={{fontSize: 24, color: '#4ECDC4'}}>✓</span>
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#34D399',
                }}
              >
                Online no WhatsApp
              </div>
            </div>
          </div>

          {/* Mandatory "Simulação" Tag */}
          <div
            style={{
              padding: '6px 14px',
              backgroundColor: 'rgba(255, 255, 255, 0.12)',
              borderRadius: 12,
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#CBD5E1',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            Simulação
          </div>
        </div>

        {/* Chat Body */}
        <div
          style={{
            flex: 1,
            padding: '20px 22px',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            backgroundColor: '#111827',
            backgroundImage:
              'radial-gradient(rgba(255,255,255,0.03) 1px, transparent 1px)',
            backgroundSize: '20px 20px',
          }}
        >
          {/* Initial context message: Previous proposal that went cold */}
          <div
            style={{
              alignSelf: 'flex-end',
              maxWidth: '85%',
              backgroundColor: 'rgba(30, 58, 95, 0.7)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '20px 20px 4px 20px',
              padding: '14px 18px',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
                color: '#CBD5E1',
                lineHeight: 1.3,
              }}
            >
              Segue nossa proposta comercial com os valores!
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                marginTop: 6,
                fontFamily,
                fontSize: 32,
                color: '#94A3B8',
              }}
            >
              14:35 ✓✓
            </div>
          </div>

          {/* Stagnation note: lead went inactive */}
          <div style={{alignSelf: 'center'}}>
            <div
              style={{
                padding: '6px 18px',
                backgroundColor: 'rgba(239, 68, 68, 0.18)',
                border: '1px solid rgba(239, 68, 68, 0.5)',
                borderRadius: 14,
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#FCA5A5',
              }}
            >
              ⚠️ 5 dias sem resposta do cliente
            </div>
          </div>

          {/* Balloon 1: Automated Follow-up sent by AI */}
          {frame >= 50 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '92%',
                transform: `scale(${balloon1Spring}) translateY(${interpolate(
                  balloon1Spring,
                  [0, 1],
                  [15, 0]
                )}px)`,
                opacity: balloon1Spring,
              }}
            >
              {showTyping1 ? (
                <div
                  style={{
                    backgroundColor: '#1E293B',
                    padding: '14px 20px',
                    borderRadius: '20px 20px 20px 4px',
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#4ECDC4',
                  }}
                >
                  🤖 IA digitando follow-up inteligente...
                </div>
              ) : (
                <div
                  style={{
                    backgroundColor: '#0F3733',
                    border: '1.5px solid #14B8A6',
                    borderRadius: '20px 20px 20px 4px',
                    padding: '16px 20px',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#E6FFFA',
                      lineHeight: 1.35,
                    }}
                  >
                    Olá! Vi que você recebeu nossa proposta. Ficou alguma dúvida
                    para fecharmos?
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginTop: 8,
                    }}
                  >
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 700,
                        color: '#4ECDC4',
                      }}
                    >
                      Follow-up Automático
                    </span>
                    <span
                      style={{fontFamily, fontSize: 32, color: '#99F6E4'}}
                    >
                      10:02 ✓✓
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Balloon 2: Client replying and reactivating negotiation */}
          {frame >= 115 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '92%',
                transform: `scale(${balloon2Spring}) translateY(${interpolate(
                  balloon2Spring,
                  [0, 1],
                  [15, 0]
                )}px)`,
                opacity: balloon2Spring,
              }}
            >
              {showTyping2 ? (
                <div
                  style={{
                    backgroundColor: '#1E3A5F',
                    padding: '14px 20px',
                    borderRadius: '20px 20px 4px 20px',
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#93C5FD',
                  }}
                >
                  Cliente respondendo...
                </div>
              ) : (
                <div
                  style={{
                    backgroundColor: '#1E3A5F',
                    border: '1.5px solid #3B82F6',
                    borderRadius: '20px 20px 4px 20px',
                    padding: '16px 20px',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#EFF6FF',
                      lineHeight: 1.35,
                    }}
                  >
                    Oi! Estava bem corrido aqui, que bom que chamou. Vamos
                    alinhar o fechamento!
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'flex-end',
                      marginTop: 6,
                      fontFamily,
                      fontSize: 32,
                      color: '#BFDBFE',
                    }}
                  >
                    10:04
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Real-time status reactivation toast */}
          {frame >= 170 && (
            <div
              style={{
                marginTop: 'auto',
                alignSelf: 'center',
                width: '100%',
                transform: `scale(${statusSpring})`,
                opacity: statusSpring,
              }}
            >
              <div
                style={{
                  backgroundColor: 'rgba(16, 185, 129, 0.25)',
                  border: '2px solid #10B981',
                  borderRadius: 18,
                  padding: '12px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 12,
                }}
              >
                <span style={{fontSize: 30}}>🎯</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#6EE7B7',
                  }}
                >
                  Lead Reativado para Negociar!
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
