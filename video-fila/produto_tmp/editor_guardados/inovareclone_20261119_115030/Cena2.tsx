import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES, fontFamily} from './constants';

export const Cena2: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no fundo
  const bgScale = interpolate(frame, [0, 205], [1.02, 1.14], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída
  const fadeIn = interpolate(frame, [0, 10], [0.8, 1], {
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(frame, [195, 205], [1, 0.85], {
    extrapolateRight: 'clamp',
  });

  // Animação 3D do Celular
  const phoneSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Mensagens do chat sincronizadas
  // Mensagem 1 (Cliente) - frame 10 (~0.33s)
  const msg1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Digitando... (frame 25 a 42)
  const isTyping = frame >= 25 && frame < 43;

  // Mensagem 2 (Empresa) - frame 43 (~1.4s, voz fala "O sistema gera o avatar...")
  const msg2Spring = spring({
    frame: frame - 43,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Chip Destaque 1: Fala em Português - frame 75 (~2.5s, voz fala "com fala em português")
  const chip1Spring = spring({
    frame: frame - 75,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Chip Destaque 2: Posturas Automáticas - frame 105 (~3.5s, voz fala "e posturas automáticas")
  const chip2Spring = spring({
    frame: frame - 105,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Mensagem 3 (Cliente) - frame 125 (~4.1s)
  const msg3Spring = spring({
    frame: frame - 125,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Mensagem 4 (Empresa) - frame 148 (~4.9s)
  const msg4Spring = spring({
    frame: frame - 148,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Flutuação 3D suave contínua
  const floatY = Math.sin(frame / 15) * 5;
  const rotateY = -8 + Math.sin(frame / 18) * 2;
  const rotateX = 4 + Math.cos(frame / 20) * 1.5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: CORES.fundoEscuro,
        overflow: 'hidden',
        fontFamily,
        opacity: fadeIn * fadeOut,
      }}
    >
      {/* Fundo com Img e push-in */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
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
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.15) 0%, rgba(11, 13, 20, 0.88) 60%, rgba(11, 13, 20, 0.98) 100%)',
          }}
        />
      </div>

      {/* TOPO: Safe Zone y: 150 a 480 */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 16,
          zIndex: 30,
        }}
      >
        {/* Rótulo COMO FUNCIONA */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 24px',
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            border: '1.5px solid rgba(139, 92, 246, 0.5)',
            borderRadius: 24,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: CORES.marca,
              boxShadow: `0 0 10px ${CORES.marca}`,
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>

        {/* Selo OBRIGATÓRIO: Simulação */}
        <div
          style={{
            padding: '8px 18px',
            backgroundColor: 'rgba(30, 41, 59, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: 16,
          }}
        >
          <span
            style={{
              fontSize: 32,
              fontWeight: 600,
              color: CORES.textoSecundario,
              letterSpacing: 0.8,
              textTransform: 'uppercase',
            }}
          >
            Simulação
          </span>
        </div>
      </div>

      {/* CHIPS DE RECURSOS EM DESTAQUE (surgem nas palavras da locução) */}
      <div
        style={{
          position: 'absolute',
          top: 248,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          gap: 14,
          zIndex: 35,
        }}
      >
        {frame >= 75 && (
          <div
            style={{
              opacity: Math.max(0, chip1Spring),
              transform: `scale(${Math.max(0.7, chip1Spring)}) translateY(${floatY * 0.5}px)`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 18px',
              backgroundColor: 'rgba(139, 92, 246, 0.95)',
              borderRadius: 18,
              boxShadow: '0 8px 24px rgba(139, 92, 246, 0.6)',
            }}
          >
            <span style={{fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
              🇧🇷 Fala em Português
            </span>
          </div>
        )}

        {frame >= 105 && (
          <div
            style={{
              opacity: Math.max(0, chip2Spring),
              transform: `scale(${Math.max(0.7, chip2Spring)}) translateY(${floatY * 0.5}px)`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 18px',
              backgroundColor: 'rgba(16, 185, 129, 0.95)',
              borderRadius: 18,
              boxShadow: '0 8px 24px rgba(16, 185, 129, 0.6)',
            }}
          >
            <span style={{fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
              ⚡ Posturas Automáticas
            </span>
          </div>
        )}
      </div>

      {/* MOCKUP DO CELULAR 3D — y: 360 a 1270 */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 70,
          right: 70,
          height: 910,
          perspective: 1200,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 25,
        }}
      >
        <div
          style={{
            width: 880,
            height: '100%',
            backgroundColor: '#0F172A',
            borderRadius: 44,
            border: '3px solid rgba(255, 255, 255, 0.18)',
            boxShadow:
              '0 30px 70px rgba(0, 0, 0, 0.9), 0 0 50px rgba(139, 92, 246, 0.25)',
            transform: `scale(${Math.max(0.85, phoneSpring)}) rotateY(${rotateY}deg) rotateX(${rotateX}deg) translateY(${floatY}px)`,
            transformStyle: 'preserve-3d',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header do WhatsApp Mockup */}
          <div
            style={{
              height: 96,
              backgroundColor: '#1E293B',
              borderBottom: '1.5px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              padding: '0 24px',
              gap: 16,
            }}
          >
            {/* Avatar do perfil */}
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                backgroundColor: CORES.marca,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: `0 0 12px ${CORES.marca}`,
              }}
            >
              <span style={{fontSize: 32, fontWeight: 900, color: '#FFFFFF'}}>
                IC
              </span>
            </div>

            {/* Informações de contato */}
            <div style={{display: 'flex', flexDirection: 'column'}}>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  letterSpacing: 0.5,
                }}
              >
                Inovare Clone
              </span>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#10B981',
                }}
              >
                ● Online
              </span>
            </div>
          </div>

          {/* Área de mensagens do WhatsApp */}
          <div
            style={{
              flex: 1,
              padding: '22px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: 18,
              backgroundColor: '#0B0F19',
              backgroundSize: 'cover',
            }}
          >
            {/* Mensagem 1: Cliente */}
            {frame >= 8 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  backgroundColor: '#1E293B',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '16px 22px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
                  opacity: Math.max(0, msg1Spring),
                  transform: `translateY(${(1 - msg1Spring) * 20}px)`,
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#94A3B8',
                    marginBottom: 4,
                  }}
                >
                  Cliente
                </div>
                <div
                  style={{
                    fontSize: 33,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Como funciona para criar os vídeos sem eu gravar?
                </div>
              </div>
            )}

            {/* Balão Digitando... */}
            {isTyping && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: '#2E1065',
                  borderRadius: '20px 20px 4px 20px',
                  padding: '14px 22px',
                  border: '1px solid rgba(139, 92, 246, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: CORES.marcaClara,
                  }}
                >
                  digitando...
                </span>
              </div>
            )}

            {/* Mensagem 2: Empresa (destaque da fala) */}
            {frame >= 43 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '84%',
                  backgroundColor: '#6D28D9',
                  borderRadius: '20px 20px 4px 20px',
                  padding: '16px 22px',
                  boxShadow: '0 6px 20px rgba(109, 40, 217, 0.5)',
                  opacity: Math.max(0, msg2Spring),
                  transform: `translateY(${(1 - msg2Spring) * 20}px)`,
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#DDD6FE',
                    marginBottom: 4,
                  }}
                >
                  Inovare Clone
                </div>
                <div
                  style={{
                    fontSize: 33,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Criamos seu avatar com IA, com posturas automáticas e fala em português.
                </div>
              </div>
            )}

            {/* Mensagem 3: Cliente */}
            {frame >= 125 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  backgroundColor: '#1E293B',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '16px 22px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
                  opacity: Math.max(0, msg3Spring),
                  transform: `translateY(${(1 - msg3Spring) * 20}px)`,
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#94A3B8',
                    marginBottom: 4,
                  }}
                >
                  Cliente
                </div>
                <div
                  style={{
                    fontSize: 33,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  E o material fica com a minha identidade?
                </div>
              </div>
            )}

            {/* Mensagem 4: Empresa */}
            {frame >= 148 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '84%',
                  backgroundColor: '#6D28D9',
                  borderRadius: '20px 20px 4px 20px',
                  padding: '16px 22px',
                  boxShadow: '0 6px 20px rgba(109, 40, 217, 0.5)',
                  opacity: Math.max(0, msg4Spring),
                  transform: `translateY(${(1 - msg4Spring) * 20}px)`,
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#DDD6FE',
                    marginBottom: 4,
                  }}
                >
                  Inovare Clone
                </div>
                <div
                  style={{
                    fontSize: 33,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Sim, é o seu próprio avatar, cem por cento seu.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
