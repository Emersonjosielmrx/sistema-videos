import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Câmera dinâmica contínua: push suave e pan vertical
  const scale = interpolate(frame, [0, 247], [1.06, 1.20], {
    extrapolateRight: 'clamp',
  });
  const panY = interpolate(frame, [0, 247], [20, -25], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída
  const opacity = interpolate(frame, [0, 10, 235, 247], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação de entrada dos balões de conversa
  // Balão 1: Cliente aos ~11.5s (frame 15)
  const b1Spring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 13, mass: 0.6, stiffness: 120},
  });
  const b1Opacity = interpolate(b1Spring, [0, 0.35, 1], [0, 1, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Indicador Digitando entre frame 52 e 74
  const isTyping = frame >= 52 && frame < 75;
  const dot1 = Math.sin(frame * 0.4) * 6;
  const dot2 = Math.sin(frame * 0.4 + 1.2) * 6;
  const dot3 = Math.sin(frame * 0.4 + 2.4) * 6;

  // Balão 2: Agenda IA aos ~13.5s (frame 75)
  const b2Spring = spring({
    frame: frame - 75,
    fps,
    config: {damping: 13, mass: 0.6, stiffness: 120},
  });
  const b2Opacity = interpolate(b2Spring, [0, 0.35, 1], [0, 1, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Balão 3: Cliente escolhe horário aos ~15.5s (frame 134) — nunca aparece antes do frame 134
  const b3Spring = spring({
    frame: frame - 134,
    fps,
    config: {damping: 13, mass: 0.6, stiffness: 120},
  });
  const b3Opacity = interpolate(b3Spring, [0, 0.35, 1], [0, 1, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Balão 4: Confirmação aos ~16.5s (frame 164)
  const b4Spring = spring({
    frame: frame - 164,
    fps,
    config: {damping: 13, mass: 0.6, stiffness: 120},
  });
  const b4Opacity = interpolate(b4Spring, [0, 0.35, 1], [0, 1, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Selo de sucesso aos ~17.5s (frame 195)
  const successSpring = spring({
    frame: frame - 195,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 140},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0F172A',
        opacity,
      }}
    >
      {/* Background Image com Desfoque suave e ambiente escurecido atrás do celular */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${scale}) translateY(${panY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(16px) brightness(0.65)',
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
      </div>

      {/* Véu escuro moderado */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.90) 0%, rgba(15,23,42,0.60) 45%, rgba(15,23,42,0.92) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Safe Zone container: respiro confortável abaixo da barra de progresso */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Top Header com Selo Simulação Obrigatório */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            width: 860,
            maxWidth: '100%',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 24px',
              borderRadius: 999,
              backgroundColor: 'rgba(31, 41, 55, 0.95)',
              border: '1.5px solid rgba(245, 158, 11, 0.6)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#F59E0B',
                letterSpacing: 1.2,
                textTransform: 'uppercase',
                whiteSpace: 'nowrap',
              }}
            >
              COMO FUNCIONA
            </span>
          </div>

          <div
            style={{
              padding: '8px 18px',
              borderRadius: 10,
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              border: '1.5px solid #475569',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#94A3B8',
                letterSpacing: 1.2,
                textTransform: 'uppercase',
                whiteSpace: 'nowrap',
              }}
            >
              Simulação
            </span>
          </div>
        </div>

        {/* Mockup de Celular WhatsApp 3D */}
        <div
          style={{
            marginTop: 25,
            width: 860,
            borderRadius: 36,
            backgroundColor: '#0B141A',
            border: '8px solid #334155',
            boxShadow:
              '0 25px 60px rgba(0,0,0,0.85), inset 0 0 20px rgba(0,0,0,0.5)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            transform: 'perspective(1200px) rotateY(3deg)',
          }}
        >
          {/* Header do WhatsApp */}
          <div
            style={{
              backgroundColor: '#1F2C34',
              padding: '18px 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1.5px solid #2A3942',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: '50%',
                  backgroundColor: '#475569',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  fontWeight: 900,
                  color: '#F8FAFC',
                }}
              >
                👤
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 800,
                    color: '#E9EDEF',
                  }}
                >
                  Cliente
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#25D366',
                  }}
                >
                  ● Online
                </span>
              </div>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#8696A0',
              }}
            >
              23:48
            </span>
          </div>

          {/* Área de Mensagens */}
          <div
            style={{
              padding: '24px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              minHeight: 520,
              backgroundColor: '#0B141A',
            }}
          >
            {/* Mensagem 1: Cliente */}
            {frame >= 15 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  backgroundColor: '#202C33',
                  padding: '16px 22px',
                  borderRadius: '18px 18px 18px 4px',
                  boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                  transform: `translateY(${interpolate(
                    b1Spring,
                    [0, 1],
                    [24, 0]
                  )}px) scale(${interpolate(b1Spring, [0, 1], [0.95, 1])})`,
                  opacity: b1Opacity,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.3,
                  }}
                >
                  Boa noite! Tem horário amanhã de manhã?
                </div>
                <div
                  style={{
                    textAlign: 'right',
                    fontSize: 32,
                    color: '#8696A0',
                    marginTop: 4,
                  }}
                >
                  23:48
                </div>
              </div>
            )}

            {/* Digitando indicador */}
            {isTyping && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: '#005C4B',
                  padding: '14px 24px',
                  borderRadius: '18px 18px 4px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    color: '#D1E7DD',
                    marginRight: 6,
                  }}
                >
                  Agenda IA digitando
                </span>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#FFFFFF',
                    transform: `translateY(${dot1}px)`,
                  }}
                />
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#FFFFFF',
                    transform: `translateY(${dot2}px)`,
                  }}
                />
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#FFFFFF',
                    transform: `translateY(${dot3}px)`,
                  }}
                />
              </div>
            )}

            {/* Mensagem 2: Empresa / Agenda IA */}
            {frame >= 75 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '85%',
                  backgroundColor: '#005C4B',
                  padding: '16px 22px',
                  borderRadius: '18px 18px 4px 18px',
                  boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                  transform: `translateY(${interpolate(
                    b2Spring,
                    [0, 1],
                    [24, 0]
                  )}px) scale(${interpolate(b2Spring, [0, 1], [0.95, 1])})`,
                  opacity: b2Opacity,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.3,
                  }}
                >
                  Boa noite! Tenho 9h ou 10h30 livres. Qual prefere?
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    alignItems: 'center',
                    gap: 6,
                    fontSize: 32,
                    color: '#A9C7BD',
                    marginTop: 4,
                  }}
                >
                  <span>23:48</span>
                  <span style={{color: '#53BDEB'}}>✓✓</span>
                </div>
              </div>
            )}

            {/* Mensagem 3: Cliente — Entra estritamente a partir do frame 134 com fade suave e sem miniaturização */}
            {frame >= 134 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  backgroundColor: '#202C33',
                  padding: '16px 22px',
                  borderRadius: '18px 18px 18px 4px',
                  boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                  transform: `translateY(${interpolate(
                    b3Spring,
                    [0, 1],
                    [24, 0]
                  )}px) scale(${interpolate(b3Spring, [0, 1], [0.95, 1])})`,
                  opacity: b3Opacity,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.3,
                  }}
                >
                  Pode ser às 10h30.
                </div>
                <div
                  style={{
                    textAlign: 'right',
                    fontSize: 32,
                    color: '#8696A0',
                    marginTop: 4,
                  }}
                >
                  23:49
                </div>
              </div>
            )}

            {/* Mensagem 4: Confirmação da IA */}
            {frame >= 164 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '85%',
                  backgroundColor: '#005C4B',
                  padding: '16px 22px',
                  borderRadius: '18px 18px 4px 18px',
                  border: '1.5px solid rgba(245, 158, 11, 0.6)',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
                  transform: `translateY(${interpolate(
                    b4Spring,
                    [0, 1],
                    [24, 0]
                  )}px) scale(${interpolate(b4Spring, [0, 1], [0.95, 1])})`,
                  opacity: b4Opacity,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Pronto, agendado para amanhã às 10h30. Até lá!
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    alignItems: 'center',
                    gap: 6,
                    fontSize: 32,
                    color: '#A9C7BD',
                    marginTop: 4,
                  }}
                >
                  <span>23:49</span>
                  <span style={{color: '#53BDEB'}}>✓✓</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Badge de Destaque Final da Cena — Alto contraste com verde escuro oficial e texto branco */}
        {frame >= 195 && (
          <div
            style={{
              marginTop: 20,
              transform: `scale(${successSpring})`,
              padding: '14px 30px',
              borderRadius: 999,
              backgroundColor: '#005C4B',
              border: '1.5px solid #25D366',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.7)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              ✓ Agendado no WhatsApp sem atendente
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
