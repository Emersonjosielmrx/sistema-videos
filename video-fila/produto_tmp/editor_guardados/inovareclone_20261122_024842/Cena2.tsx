import React from 'react';
import {useCurrentFrame, useVideoConfig, spring, interpolate, Img, staticFile} from 'remotion';
import {BRIEFING} from './constants';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração da cena: 12.03s a 21.69s (~290 frames)
  // Zoom contínuo do fundo
  const bgScale = interpolate(frame, [0, 290], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  const cenaOpacity = interpolate(frame, [0, 8, 280, 290], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Movimento 3D contínuo do celular (garante dinamismo sem congelamento)
  const phoneHoverY = Math.sin(frame / 15) * 8;
  const phoneRotateY = 12 + Math.cos(frame / 20) * 2;
  const phoneRotateX = 3 + Math.sin(frame / 20) * 1.5;

  // Entrada do celular aos 0.1s (frame 3)
  const phoneSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Rótulo da etapa aos 0.15s (frame 4)
  const rotuloSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Balão 1 (Cliente): entra no frame 6 (~12.2s)
  const msg1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Indicador de digitação: ativo entre frame 25 e 48 (~12.8s a 13.6s)
  const isTyping1 = frame >= 25 && frame < 48;
  const typingDots = (frame % 18 < 6) ? '.' : (frame % 18 < 12) ? '..' : '...';

  // Balão 2 (Empresa): entra no frame 48 (~13.63s, fala: "avatar IA")
  const msg2Spring = spring({
    frame: frame - 48,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Balão 3 (Cliente): entra no frame 125 (~16.2s)
  const msg3Spring = spring({
    frame: frame - 125,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Indicador de digitação 2: ativo entre frame 138 e 160 (~16.6s a 17.3s)
  const isTyping2 = frame >= 138 && frame < 160;

  // Balão 4 (Empresa): entra no frame 160 (~17.36s, fala: "automáticas")
  const msg4Spring = spring({
    frame: frame - 160,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Chips de Destaques Técnicos sincronizados com a fala
  // Chip 1: "Posturas automáticas" aos 17.0s (frame 150)
  const chip1Spring = spring({
    frame: frame - 150,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Chip 2: "Fala em português" aos 18.4s (frame 191)
  const chip2Spring = spring({
    frame: frame - 191,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Chip 3: "100% seu" aos 19.4s (frame 221)
  const chip3Spring = spring({
    frame: frame - 221,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity: cenaOpacity,
        overflow: 'hidden',
        backgroundColor: '#0B0D13',
      }}
    >
      {/* Fundo com zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: -40,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Camada de Contraste */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 50%, rgba(15, 23, 42, 0.75) 0%, rgba(11, 13, 19, 0.95) 85%)',
        }}
      />

      {/* Rótulo Superior (y=165 a 220) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 50,
          transform: `scale(${rotuloSpring})`,
          opacity: rotuloSpring,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: 'rgba(15, 23, 42, 0.95)',
            border: `1.5px solid ${BRIEFING.cores.marca}`,
            padding: '8px 24px',
            borderRadius: 24,
            boxShadow: '0 8px 24px rgba(139, 92, 246, 0.35)',
          }}
        >
          <div
            style={{
              padding: '2px 8px',
              borderRadius: 8,
              backgroundColor: BRIEFING.cores.marca,
              color: '#FFFFFF',
              fontFamily,
              fontSize: 24,
              fontWeight: 900,
            }}
          >
            02
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            A SOLUÇÃO: AVATAR IA
          </span>
        </div>
      </div>

      {/* Container 3D do Celular */}
      <div
        style={{
          position: 'absolute',
          top: 235,
          left: 60,
          right: 60,
          height: 1040,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          perspective: 1200,
          zIndex: 30,
        }}
      >
        {/* Mockup do Smartphone */}
        <div
          style={{
            width: 840,
            height: 980,
            backgroundColor: '#0F172A',
            borderRadius: 48,
            border: '4px solid #334155',
            boxShadow:
              '0 30px 60px rgba(0, 0, 0, 0.9), 0 0 40px rgba(139, 92, 246, 0.25)',
            transform: `scale(${phoneSpring}) translateY(${phoneHoverY}px) rotateY(${phoneRotateY}deg) rotateX(${phoneRotateX}deg)`,
            transformOrigin: 'center center',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Dynamic Island / Notch */}
          <div
            style={{
              height: 36,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              paddingTop: 10,
              backgroundColor: '#0F172A',
            }}
          >
            <div
              style={{
                width: 140,
                height: 24,
                backgroundColor: '#000000',
                borderRadius: 16,
              }}
            />
          </div>

          {/* Cabeçalho do Chat */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 28px',
              backgroundColor: '#1E293B',
              borderBottom: '1.5px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              {/* Avatar do Bot */}
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: '50%',
                  background: `linear-gradient(135deg, ${BRIEFING.cores.marca}, #6D28D9)`,
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  boxShadow: '0 4px 12px rgba(139, 92, 246, 0.5)',
                }}
              >
                <span style={{fontSize: 28}}>🤖</span>
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Inovare Clone • IA
                </span>
              </div>
            </div>

            {/* Selo Simulação */}
            <div
              style={{
                padding: '4px 14px',
                borderRadius: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#94A3B8',
                  textTransform: 'uppercase',
                }}
              >
                Simulação
              </span>
            </div>
          </div>

          {/* Área de Mensagens */}
          <div
            style={{
              flex: 1,
              padding: '24px 28px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              justifyContent: 'flex-start',
              overflow: 'hidden',
            }}
          >
            {/* Mensagem 1 (Cliente) */}
            {frame >= 6 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  backgroundColor: '#1E293B',
                  border: '1.5px solid #334155',
                  borderRadius: '22px 22px 22px 4px',
                  padding: '14px 20px',
                  boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                  transform: `scale(${msg1Spring}) translateY(${(1 - msg1Spring) * 15}px)`,
                  opacity: msg1Spring,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    lineHeight: 1.25,
                    color: '#F8FAFC',
                  }}
                >
                  Como vocês conseguem postar explicando cada serviço todo dia?
                </span>
              </div>
            )}

            {/* Digitando 1 */}
            {isTyping1 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: 'rgba(139, 92, 246, 0.25)',
                  border: `1.5px solid ${BRIEFING.cores.marca}`,
                  borderRadius: '22px 22px 4px 22px',
                  padding: '8px 18px',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: BRIEFING.cores.destaque_claro,
                  }}
                >
                  digitando{typingDots}
                </span>
              </div>
            )}

            {/* Mensagem 2 (Empresa) */}
            {frame >= 48 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '84%',
                  background: `linear-gradient(135deg, ${BRIEFING.cores.marca}, #7C3AED)`,
                  borderRadius: '22px 22px 4px 22px',
                  padding: '14px 22px',
                  boxShadow: '0 8px 24px rgba(139, 92, 246, 0.45)',
                  transform: `scale(${msg2Spring}) translateY(${(1 - msg2Spring) * 15}px)`,
                  opacity: msg2Spring,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    lineHeight: 1.25,
                    color: '#FFFFFF',
                  }}
                >
                  Usamos nosso próprio avatar IA falando em português. ✨
                </span>
              </div>
            )}

            {/* Mensagem 3 (Cliente) */}
            {frame >= 125 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  backgroundColor: '#1E293B',
                  border: '1.5px solid #334155',
                  borderRadius: '22px 22px 22px 4px',
                  padding: '14px 20px',
                  boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                  transform: `scale(${msg3Spring}) translateY(${(1 - msg3Spring) * 15}px)`,
                  opacity: msg3Spring,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    lineHeight: 1.25,
                    color: '#F8FAFC',
                  }}
                >
                  E as posturas ficam naturais no vídeo?
                </span>
              </div>
            )}

            {/* Digitando 2 */}
            {isTyping2 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: 'rgba(139, 92, 246, 0.25)',
                  border: `1.5px solid ${BRIEFING.cores.marca}`,
                  borderRadius: '22px 22px 4px 22px',
                  padding: '8px 18px',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: BRIEFING.cores.destaque_claro,
                  }}
                >
                  digitando{typingDots}
                </span>
              </div>
            )}

            {/* Mensagem 4 (Empresa) */}
            {frame >= 160 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '84%',
                  background: `linear-gradient(135deg, ${BRIEFING.cores.marca}, #7C3AED)`,
                  borderRadius: '22px 22px 4px 22px',
                  padding: '14px 22px',
                  boxShadow: '0 8px 24px rgba(139, 92, 246, 0.45)',
                  transform: `scale(${msg4Spring}) translateY(${(1 - msg4Spring) * 15}px)`,
                  opacity: msg4Spring,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    lineHeight: 1.25,
                    color: '#FFFFFF',
                  }}
                >
                  Sim, as posturas automáticas mantêm a apresentação perfeita.
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chips Flutuantes de Diferenciais Reais (y=1270 a 1360) */}
      <div
        style={{
          position: 'absolute',
          top: 1260,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 12,
          flexWrap: 'wrap',
          zIndex: 40,
        }}
      >
        {frame >= 150 && (
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.95)',
              border: `2px solid ${BRIEFING.cores.marca}`,
              padding: '8px 18px',
              borderRadius: 20,
              boxShadow: '0 8px 20px rgba(0,0,0,0.7)',
              transform: `scale(${chip1Spring})`,
              opacity: chip1Spring,
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
              ✓ Posturas automáticas
            </span>
          </div>
        )}

        {frame >= 191 && (
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.95)',
              border: `2px solid ${BRIEFING.cores.marca}`,
              padding: '8px 18px',
              borderRadius: 20,
              boxShadow: '0 8px 20px rgba(0,0,0,0.7)',
              transform: `scale(${chip2Spring})`,
              opacity: chip2Spring,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: BRIEFING.cores.destaque_claro,
              }}
            >
              ✓ Fala em português
            </span>
          </div>
        )}

        {frame >= 221 && (
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.95)',
              border: `2px solid #22C55E`,
              padding: '8px 18px',
              borderRadius: 20,
              boxShadow: '0 8px 20px rgba(34, 197, 94, 0.35)',
              transform: `scale(${chip3Spring})`,
              opacity: chip3Spring,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
              }}
            >
              ✓ 100% seu
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
