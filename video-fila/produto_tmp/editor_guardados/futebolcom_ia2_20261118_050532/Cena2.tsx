import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
  OffthreadVideo,
} from 'remotion';
import {CORES} from './types';

export const Cena2: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com movimento contínuo (zoom suave 1.05 -> 1.18)
  const bgScale = interpolate(frame, [0, 226], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Movimento de câmera 3D suave com push-in contínuo (1.00 -> 1.08)
  const phoneScale = interpolate(frame, [0, 226], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });
  const phoneRotateY = interpolate(frame, [0, 226], [6, -2], {
    extrapolateRight: 'clamp',
  });
  const phoneFloatY = Math.sin(frame * 0.08) * 6;

  // Entrada do celular com spring
  const phoneSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do topo
  const headerSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Timings acelerados e orgânicos das mensagens sincronizados com a fala
  const msg1Spring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 150},
  });
  const msg2Spring = spring({
    frame: frame - 34,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Destaque visual heroico do cardápio com foto em alta definição
  const heroPopSpring = spring({
    frame: frame - 44,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const heroOut = interpolate(frame, [96, 104], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const heroProgress = Math.max(0, heroPopSpring) * heroOut;

  const msg3Spring = spring({
    frame: frame - 104,
    fps,
    config: {damping: 12, stiffness: 150},
  });
  const msg4Spring = spring({
    frame: frame - 146,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Fundo com Vídeo do Restaurante em Desfoque Cinematográfico Suave para Manter Imersão */}
      <div
        style={{
          position: 'absolute',
          inset: -20,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(14px) brightness(0.55)',
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

      {/* Overlay com gradiente profundo da marca */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 35%, rgba(225,29,72,0.25) 0%, rgba(35,6,12,0.8) 65%, #110206 100%)',
        }}
      />

      {/* Topo Informativo (y: 170 a 270) — Respiro garantido >= 30px acima do smartphone */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
          zIndex: 25,
          transform: `scale(${Math.max(0, headerSpring)})`,
          opacity: Math.min(1, headerSpring),
        }}
      >
        <div
          style={{
            background: 'rgba(250, 204, 21, 0.18)',
            border: `2px solid ${CORES.apoio}`,
            borderRadius: 999,
            padding: '4px 20px',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            boxShadow: '0 4px 18px rgba(0,0,0,0.5)',
          }}
        >
          <span style={{fontSize: 32}}>✨</span>
          <span
            style={{
              color: CORES.apoio,
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            COMO FUNCIONA
          </span>
        </div>

        <div
          style={{
            fontSize: 36,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            textTransform: 'uppercase',
            lineHeight: 1.15,
            textShadow: '0 4px 18px rgba(0,0,0,0.85)',
          }}
        >
          CARDÁPIO COM FOTOS{' '}
          <span
            style={{
              background: CORES.marca,
              padding: '2px 14px',
              borderRadius: 10,
              color: '#FFFFFF',
              whiteSpace: 'nowrap',
            }}
          >
            & IA NO WHATSAPP
          </span>
        </div>
      </div>

      {/* Mockup de Celular 3D (Largura 840px >= 820px, y: 300 a 1280) — Sem colisão com topo ou karaokê */}
      <div
        style={{
          position: 'absolute',
          top: 300,
          left: 120,
          width: 840,
          height: 980,
          transform: `perspective(1200px) rotateY(${phoneRotateY}deg) translateY(${phoneFloatY}px) scale(${
            phoneScale * Math.max(0, phoneSpring)
          })`,
          opacity: Math.min(1, phoneSpring),
          zIndex: 20,
        }}
      >
        {/* Carcaça do Celular com Borda Metálica e Vidro Escuro */}
        <div
          style={{
            width: '100%',
            height: '100%',
            borderRadius: 44,
            background: '#0B141A',
            border: '6px solid #2A3942',
            boxShadow:
              '0 25px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(225, 29, 72, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* Barra Superior do WhatsApp */}
          <div
            style={{
              height: 100,
              background: '#1F2C34',
              borderBottom: '2px solid #2A3942',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 24px',
              zIndex: 10,
              flexShrink: 0,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 999,
                  background:
                    'linear-gradient(135deg, #E11D48 0%, #BE123C 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  boxShadow: '0 0 14px rgba(225,29,72,0.6)',
                }}
              >
                🍔
              </div>
              <div>
                <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 800}}>
                  Cardápio Digital
                </div>
                <div
                  style={{
                    color: '#25D366',
                    fontSize: 32,
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: 999,
                      background: '#25D366',
                    }}
                  />
                  Online com IA
                </div>
              </div>
            </div>

            {/* Selo OBRIGATÓRIO: "Simulação" (font-size >= 32px) */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.12)',
                border: '1.5px solid rgba(255, 255, 255, 0.35)',
                borderRadius: 8,
                padding: '4px 14px',
                color: '#E2E8F0',
                fontSize: 32,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: 0.8,
              }}
            >
              Simulação
            </div>
          </div>

          {/* Área de Conversa / Chat Integrada */}
          <div
            style={{
              flex: 1,
              padding: '18px 20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'flex-start',
              gap: 14,
              background:
                'radial-gradient(circle at 50% 30%, #111B21 0%, #0B141A 100%)',
              position: 'relative',
            }}
          >
            {/* Mensagem 1: Cliente pergunta onde ver os pratos */}
            {frame >= 4 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '85%',
                  background: '#202C33',
                  border: '1.5px solid #2A3942',
                  borderRadius: '18px 18px 18px 4px',
                  padding: '12px 18px',
                  transform: `scale(${Math.max(0, msg1Spring)})`,
                  opacity: Math.min(1, msg1Spring),
                  boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                }}
              >
                <div style={{color: '#E9EDEF', fontSize: 34, fontWeight: 500}}>
                  Boa noite, onde vejo os pratos?
                </div>
                <div
                  style={{
                    color: '#8696A0',
                    fontSize: 32,
                    textAlign: 'right',
                    marginTop: 2,
                  }}
                >
                  20:14
                </div>
              </div>
            )}

            {/* Indicador "IA Digitando..." antes da resposta 1 */}
            {frame >= 16 && frame < 34 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  background: '#005C4B',
                  borderRadius: '18px 18px 4px 18px',
                  padding: '10px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span
                  style={{
                    color: '#D1F4CC',
                    fontSize: 32,
                    fontStyle: 'italic',
                    fontWeight: 600,
                  }}
                >
                  IA digitando...
                </span>
                <span style={{fontSize: 30}}>⚡</span>
              </div>
            )}

            {/* Mensagem 2: Empresa envia Cardápio com fotos */}
            {frame >= 34 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '92%',
                  background: '#005C4B',
                  border: '1.5px solid rgba(37, 211, 102, 0.4)',
                  borderRadius: '18px 18px 4px 18px',
                  padding: '12px 18px',
                  transform: `scale(${Math.max(0, msg2Spring)})`,
                  opacity: Math.min(1, msg2Spring),
                  boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
                }}
              >
                <div
                  style={{
                    color: '#FFFFFF',
                    fontSize: 34,
                    fontWeight: 500,
                    marginBottom: 8,
                  }}
                >
                  Olá! Aqui está o cardápio digital com fotos para você
                  escolher:
                </div>

                {/* Card de Catálogo do Produto */}
                <div
                  style={{
                    background: 'rgba(11, 20, 26, 0.92)',
                    borderRadius: 16,
                    padding: '10px 16px',
                    border: '1.5px solid rgba(255,255,255,0.22)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 16,
                    boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
                  }}
                >
                  <Img
                    src={staticFile('burger.jpg')}
                    style={{
                      width: 90,
                      height: 90,
                      borderRadius: 14,
                      objectFit: 'cover',
                      flexShrink: 0,
                      border: '2px solid rgba(250, 204, 21, 0.6)',
                    }}
                  />
                  <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                    <div
                      style={{
                        color: '#FFFFFF',
                        fontSize: 34,
                        fontWeight: 800,
                      }}
                    >
                      Burger Artesanal
                    </div>
                    <div
                      style={{
                        color: CORES.apoio,
                        fontSize: 32,
                        fontWeight: 700,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                      }}
                    >
                      <span>📸</span> Fotos no Celular
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    color: '#D1F4CC',
                    fontSize: 32,
                    textAlign: 'right',
                    marginTop: 4,
                  }}
                >
                  20:14 ✓✓
                </div>
              </div>
            )}

            {/* Destaque Visual Heroico: Modal com Foto em Alta Resolução do Prato */}
            {heroProgress > 0.02 && (
              <div
                style={{
                  position: 'absolute',
                  top: 230,
                  left: 20,
                  right: 20,
                  transform: `scale(${heroProgress})`,
                  opacity: Math.min(1, heroProgress * 1.5),
                  background: 'rgba(15, 23, 42, 0.97)',
                  border: '3px solid #FACC15',
                  borderRadius: 24,
                  padding: '16px',
                  boxShadow:
                    '0 20px 50px rgba(0,0,0,0.9), 0 0 35px rgba(250, 204, 21, 0.45)',
                  zIndex: 40,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
              >
                {/* Cabeçalho do Destaque Heroico */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    borderBottom: '1.5px solid rgba(255,255,255,0.15)',
                    paddingBottom: 8,
                  }}
                >
                  <div
                    style={{
                      color: CORES.apoio,
                      fontSize: 32,
                      fontWeight: 800,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      textTransform: 'uppercase',
                    }}
                  >
                    <span>📸</span> Foto do Cardápio no Celular
                  </div>
                  <div
                    style={{
                      background: 'rgba(37, 211, 102, 0.2)',
                      color: '#86EFAC',
                      borderRadius: 8,
                      padding: '2px 10px',
                      fontSize: 32,
                      fontWeight: 700,
                    }}
                  >
                    Alta Resolução
                  </div>
                </div>

                {/* Imagem Heroica Apetitosa com Zoom Suave */}
                <div
                  style={{
                    width: '100%',
                    height: 250,
                    borderRadius: 16,
                    overflow: 'hidden',
                    position: 'relative',
                  }}
                >
                  <Img
                    src={staticFile('burger.jpg')}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      transform: `scale(${1.0 + (frame - 44) * 0.0015})`,
                    }}
                  />
                </div>

                {/* Detalhes Gastronômicos Apetitovos */}
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 4,
                  }}
                >
                  <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 900}}>
                    Burger Artesanal
                  </div>
                  <div style={{color: '#CBD5E1', fontSize: 32, fontWeight: 500}}>
                    Pão brioche tostado, blend duplo e cheddar derretido
                  </div>
                </div>
              </div>
            )}

            {/* Mensagem 3: Cliente pergunta sobre queijo */}
            {frame >= 104 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '85%',
                  background: '#202C33',
                  border: '1.5px solid #2A3942',
                  borderRadius: '18px 18px 18px 4px',
                  padding: '12px 18px',
                  transform: `scale(${Math.max(0, msg3Spring)})`,
                  opacity: Math.min(1, msg3Spring),
                  boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                }}
              >
                <div style={{color: '#E9EDEF', fontSize: 34, fontWeight: 500}}>
                  O hambúrguer da foto vem com queijo?
                </div>
                <div
                  style={{
                    color: '#8696A0',
                    fontSize: 32,
                    textAlign: 'right',
                    marginTop: 2,
                  }}
                >
                  20:15
                </div>
              </div>
            )}

            {/* Indicador "IA Respondendo na hora..." */}
            {frame >= 126 && frame < 146 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  background: '#005C4B',
                  borderRadius: '18px 18px 4px 18px',
                  padding: '10px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span
                  style={{
                    color: '#D1F4CC',
                    fontSize: 32,
                    fontStyle: 'italic',
                    fontWeight: 600,
                  }}
                >
                  IA respondendo na hora...
                </span>
                <span style={{fontSize: 30}}>⚡</span>
              </div>
            )}

            {/* Mensagem 4: IA responde instantaneamente */}
            {frame >= 146 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '92%',
                  background: '#005C4B',
                  border: '2px solid #25D366',
                  borderRadius: '18px 18px 4px 18px',
                  padding: '12px 18px',
                  transform: `scale(${Math.max(0, msg4Spring)})`,
                  opacity: Math.min(1, msg4Spring),
                  boxShadow: '0 8px 25px rgba(37, 211, 102, 0.35)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 4,
                  }}
                >
                  <span
                    style={{
                      background: 'rgba(255,255,255,0.2)',
                      borderRadius: 6,
                      padding: '2px 8px',
                      color: '#FFFFFF',
                      fontSize: 32,
                      fontWeight: 800,
                    }}
                  >
                    IA Atendente 🤖
                  </span>
                </div>
                <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 700}}>
                  Sim, vai com queijo e você pode pedir direto por aqui.
                </div>
                <div
                  style={{
                    color: '#D1F4CC',
                    fontSize: 32,
                    textAlign: 'right',
                    marginTop: 4,
                  }}
                >
                  20:15 ✓✓
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
