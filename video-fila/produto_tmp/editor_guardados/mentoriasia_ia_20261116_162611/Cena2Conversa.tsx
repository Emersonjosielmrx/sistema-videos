import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig
} from 'remotion';
import {BRIEFING} from './data';

export const Cena2Conversa: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom contínuo
  const bgScale = interpolate(frame, [0, 260], [1.0, 1.08], {
    extrapolateRight: 'clamp'
  });

  // Perspectiva 3D visível (tilt sutil e elegante) + flutuação orgânica contínua
  const tiltY = Math.sin(frame / 18) * 4.5;
  const tiltX = Math.cos(frame / 22) * 3.0;
  const floatY = Math.sin(frame / 14) * 6;

  // Entrada do smartphone
  const phoneSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 105}
  });

  // Timings dinâmicos fracionados em 2 mensagens da mentoria para manter o chat ativo:
  // Msg 1 (Cliente): entra no frame 6
  const m1Spring = spring({frame: frame - 6, fps, config: {damping: 15, stiffness: 120}});

  // Resposta 1 (Empresa - Mapa Mental + Consultoria de Otimização):
  // Digitando: f=26..46
  // Msg 2A entra no frame 48 (~13.9s na fala)
  const isTyping1 = frame >= 26 && frame < 48;
  const m2aSpring = spring({frame: frame - 48, fps, config: {damping: 15, stiffness: 120}});

  // Resposta 2 (Empresa - Pack de Prompts Validados + Treinamento Vibe Coding):
  // Digitando: f=96..118 (evita chat estático entre 16s e 19s!)
  // Msg 2B entra no frame 120 (~16.3s na fala)
  const isTyping2 = frame >= 96 && frame < 120;
  const m2bSpring = spring({frame: frame - 120, fps, config: {damping: 15, stiffness: 120}});

  // Tags dos pilares acendem sincronizadas com a locução:
  // 12.8s abs (f=15): "Mapa Mental"
  // 13.8s abs (f=45): "Consultoria"
  // 15.5s abs (f=96): "Prompts Validados"
  // 17.0s abs (f=141): "Vibe Coding"
  const pilares = [
    {nome: 'Mapa Mental', delay: 15},
    {nome: 'Consultoria', delay: 45},
    {nome: 'Prompts Validados', delay: 96},
    {nome: 'Vibe Coding', delay: 141}
  ];

  return (
    <AbsoluteFill style={{backgroundColor: BRIEFING.cores.fundo_escuro, overflow: 'hidden'}}>
      {/* Background Image com Zoom */}
      <img
        src={staticFile('img_2.jpg')}
        alt="Fundo"
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${bgScale})`,
          filter: 'brightness(0.55) contrast(1.1)'
        }}
      />

      {/* Véu radial de iluminação */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 35%, rgba(37, 99, 235, 0.25) 0%, rgba(10, 15, 30, 0.88) 75%, rgba(5, 8, 16, 0.98) 100%)',
          pointerEvents: 'none'
        }}
      />

      {/* Safe Zone Container */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 165,
          bottom: 495,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
          perspective: 1100
        }}
      >
        {/* Topo Limpo: Pílulas citadas na voz */}
        <div
          style={{
            minHeight: 90,
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 10,
            width: '100%',
            maxWidth: 940
          }}
        >
          {pilares.map((pilar, pIdx) => {
            if (frame < pilar.delay) return null;
            const pSpring = spring({
              frame: frame - pilar.delay,
              fps,
              config: {damping: 13, stiffness: 130}
            });
            const isNewest =
              frame >= pilar.delay &&
              (pIdx === pilares.length - 1 || frame < pilares[pIdx + 1].delay);
            return (
              <div
                key={pIdx}
                style={{
                  padding: '6px 18px',
                  borderRadius: 16,
                  backgroundColor: isNewest ? '#2563EB' : 'rgba(30, 41, 59, 0.92)',
                  border: isNewest ? '2px solid #93C5FD' : '1.5px solid rgba(96, 165, 250, 0.45)',
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 800,
                  transform: `scale(${pSpring * (isNewest ? 1.05 : 1)})`,
                  opacity: pSpring,
                  boxShadow: isNewest ? '0 6px 20px rgba(37, 99, 235, 0.6)' : '0 4px 12px rgba(0,0,0,0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8
                }}
              >
                <span style={{color: '#60A5FA'}}>✓</span>
                <span>{pilar.nome}</span>
              </div>
            );
          })}
        </div>

        {/* Mockup do Smartphone: Descido em 90px para dar ampla margem de respiro das tags do topo */}
        <div
          style={{
            marginTop: 90,
            width: 950,
            height: 870,
            transform: `translateY(${floatY}px) scale(${phoneSpring}) rotateY(${tiltY}deg) rotateX(${tiltX}deg)`,
            opacity: phoneSpring,
            borderRadius: 40,
            border: '3px solid rgba(147, 197, 253, 0.35)',
            backgroundColor: '#0F172A',
            boxShadow: '0 28px 70px rgba(0, 0, 0, 0.85), 0 0 36px rgba(37, 99, 235, 0.28)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative'
          }}
        >
          {/* Dynamic Island */}
          <div
            style={{
              position: 'absolute',
              top: 10,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 150,
              height: 22,
              borderRadius: 12,
              backgroundColor: '#020617',
              zIndex: 30
            }}
          />

          {/* Header do WhatsApp */}
          <div
            style={{
              padding: '38px 28px 16px 28px',
              backgroundColor: '#1E293B',
              borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              zIndex: 20
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  backgroundColor: '#2563EB',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontWeight: 900,
                  fontSize: 32,
                  boxShadow: '0 4px 12px rgba(37, 99, 235, 0.5)'
                }}
              >
                IA
              </div>
              <div>
                <div style={{fontSize: 35, fontWeight: 900, color: '#FFFFFF', lineHeight: 1.15}}>
                  Mentorias IA
                </div>
                <div style={{fontSize: 32, color: '#34D399', fontWeight: 700}}>
                  ● Online
                </div>
              </div>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.12)',
                padding: '6px 16px',
                borderRadius: 14,
                fontSize: 32,
                fontWeight: 700,
                color: '#E2E8F0',
                border: '1px solid rgba(255, 255, 255, 0.2)'
              }}
            >
              Simulação
            </div>
          </div>

          {/* Área das Mensagens: 3 mensagens inteiras e nítidas sem corte ou rolagem agressiva */}
          <div
            style={{
              flex: 1,
              padding: '20px 24px',
              backgroundColor: '#0B132B',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'flex-start',
              overflow: 'hidden'
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 14
              }}
            >
              {/* Mensagem 1: Cliente (Dúvida inicial) */}
              {frame >= 6 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '88%',
                    backgroundColor: '#1E293B',
                    borderRadius: '24px 24px 24px 6px',
                    padding: '16px 22px',
                    border: '1.5px solid rgba(255, 255, 255, 0.16)',
                    boxShadow: '0 8px 20px rgba(0,0,0,0.45)',
                    transform: `scale(${m1Spring})`,
                    opacity: m1Spring
                  }}
                >
                  <div style={{fontSize: 35, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.25}}>
                    Tenho várias ideias, mas não sei o que automatizar primeiro.
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#CBD5E1',
                      textAlign: 'right',
                      marginTop: 4
                    }}
                  >
                    09:41
                  </div>
                </div>
              )}

              {/* Indicador Digitando 1 */}
              {isTyping1 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    backgroundColor: 'rgba(37, 99, 235, 0.35)',
                    padding: '12px 22px',
                    borderRadius: '20px 20px 6px 20px',
                    border: '1.5px solid #60A5FA',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12
                  }}
                >
                  <span style={{fontSize: 32, color: '#EFF6FF', fontWeight: 800}}>
                    Digitando...
                  </span>
                </div>
              )}

              {/* Mensagem 2A: Empresa (Parte 1 da fala: Mapa mental + consultoria de otimização) */}
              {frame >= 48 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '92%',
                    backgroundColor: '#1D4ED8',
                    borderRadius: '24px 24px 6px 24px',
                    padding: '16px 22px',
                    border: '1.5px solid rgba(147, 197, 253, 0.5)',
                    boxShadow: '0 8px 26px rgba(37, 99, 235, 0.45)',
                    transform: `scale(${m2aSpring})`,
                    opacity: m2aSpring
                  }}
                >
                  <div style={{fontSize: 35, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.25}}>
                    Com o mapa mental e consultoria de otimização estruturamos seus processos.
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#E0F2FE',
                      textAlign: 'right',
                      marginTop: 4
                    }}
                  >
                    09:41 <span style={{color: '#38BDF8'}}>✓✓</span>
                  </div>
                </div>
              )}

              {/* Indicador Digitando 2 (mantém ritmo ativo f=96..118) */}
              {isTyping2 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    backgroundColor: 'rgba(37, 99, 235, 0.35)',
                    padding: '12px 22px',
                    borderRadius: '20px 20px 6px 20px',
                    border: '1.5px solid #60A5FA',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12
                  }}
                >
                  <span style={{fontSize: 32, color: '#EFF6FF', fontWeight: 800}}>
                    Digitando...
                  </span>
                </div>
              )}

              {/* Mensagem 2B: Empresa (Parte 2 da fala: Pack de prompts + Vibe Coding) */}
              {frame >= 120 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '92%',
                    backgroundColor: '#1E40AF',
                    borderRadius: '24px 24px 6px 24px',
                    padding: '16px 22px',
                    border: '1.5px solid rgba(96, 165, 250, 0.6)',
                    boxShadow: '0 8px 28px rgba(30, 64, 175, 0.55)',
                    transform: `scale(${m2bSpring})`,
                    opacity: m2bSpring
                  }}
                >
                  <div style={{fontSize: 35, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.25}}>
                    E com o pack de prompts validados e treinamento Vibe Coding, você planeja tudo!
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#E0F2FE',
                      textAlign: 'right',
                      marginTop: 4
                    }}
                  >
                    09:42 <span style={{color: '#38BDF8'}}>✓✓</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Barra de Digitação Mobile (WhatsApp Nativo) */}
          <div
            style={{
              padding: '14px 20px',
              backgroundColor: '#1E293B',
              borderTop: '1.5px solid rgba(255, 255, 255, 0.12)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              zIndex: 20
            }}
          >
            <div
              style={{
                flex: 1,
                backgroundColor: '#0F172A',
                borderRadius: 24,
                padding: '10px 18px',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <span style={{fontSize: 32}}>😊</span>
                <span style={{fontSize: 32, color: '#94A3B8', fontWeight: 600}}>Mensagem</span>
              </div>
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <span style={{fontSize: 32}}>📎</span>
                <span style={{fontSize: 32}}>📷</span>
              </div>
            </div>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                backgroundColor: '#2563EB',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 30,
                color: '#FFFFFF'
              }}
            >
              🎙️
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
