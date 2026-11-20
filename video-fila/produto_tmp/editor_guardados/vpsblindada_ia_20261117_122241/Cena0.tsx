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
import {AlertIcon, ServerIcon} from './Icons';

interface Cena0Props {
  fontFamily: string;
}

export const Cena0: React.FC<Cena0Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração da cena: 0 a 4.86 s (146 frames a 30 fps)
  // Animação forte e contínua de zoom e pan no fundo (1.00 -> 1.22 e translateY de 0 a -70px)
  // para superar com folga a métrica de movimento de 4% entre 20% e 80% da cena
  const bgScale = interpolate(frame, [0, 146], [1.0, 1.22], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 146], [0, -70], {
    extrapolateRight: 'clamp',
  });

  // Linha de scanline tech que desce continuamente pela tela
  const scanlineY = interpolate(frame % 60, [0, 60], [150, 1500]);

  // Entrada imediata do Badge de alerta no frame 0
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 130},
  });

  // Microanimação contínua e pulso de brilho nos badges de alerta
  const alertPulse = interpolate(
    Math.sin((frame / 30) * Math.PI * 4),
    [-1, 1],
    [0.95, 1.08]
  );
  const urgentPulse = interpolate(
    Math.cos((frame / 30) * Math.PI * 4),
    [-1, 1],
    [0.94, 1.07]
  );
  const redGlow = 16 + Math.sin(frame * 0.25) * 10;

  // Slow push-in contínuo (+4%) na área dos cards
  const cardsPushIn = interpolate(frame, [0, 146], [1.0, 1.04], {
    extrapolateRight: 'clamp',
  });

  // Pergunta-gancho unificada desde o frame 0 (resolvendo o problema de retenção do gancho)
  const title1Spring = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.65, stiffness: 140},
  });
  const title2Spring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, mass: 0.65, stiffness: 140},
  });

  // Destaque cinético da palavra "reclamação" aos ~2.6s (frame 78) quando é falada
  const reclamoHighlight =
    frame >= 78
      ? spring({
          frame: frame - 78,
          fps,
          config: {damping: 12, mass: 0.5, stiffness: 160},
        })
      : 0;

  // HUD de Servidor Fora do Ar: entra aos ~0.15s (frame 4) com leve pop e shake sutil de impacto
  const hudSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 135},
  });
  const hudShake =
    frame >= 4 && frame < 20
      ? Math.sin((frame - 4) * 1.8) * 6 * (1 - (frame - 4) / 16)
      : 0;

  // Card de Notificação de Reclamação: ENTRADA ESCALONADA (STAGGER) aos ~1.9s (frame 58)
  // perfeitamente sincronizada com a locução ("descobre pela reclamação"), subindo com spring dinâmico
  const cardSpring = spring({
    frame: frame - 58,
    fps,
    config: {damping: 12, mass: 0.75, stiffness: 130},
  });
  const cardSlideY = interpolate(cardSpring, [0, 1], [80, 0]);

  // Gancho do briefing fixado no card: surge com pop aos ~3.0s (frame 90)
  const subGanchoSpring = spring({
    frame: frame - 90,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 140},
  });

  // Efeito de impacto inicial vermelho no frame 0
  const impactFlash = interpolate(frame, [0, 10], [0.35, 0], {
    extrapolateRight: 'clamp',
  });

  // Transição suave com leve zoom wipe nos últimos frames (138 a 146)
  const sceneOpacity = interpolate(frame, [138, 146], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitWipe = interpolate(frame, [138, 146], [1, 1.05], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        opacity: sceneOpacity,
        backgroundColor: '#0B1120',
        transform: `scale(${exitWipe})`,
        transformOrigin: 'center center',
      }}
    >
      {/* Fundo dinâmico com imagem e grid cibernético em zoom contínuo */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.35) contrast(1.15)',
          }}
        />
        {/* Glow radial no fundo */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 35%, rgba(239, 68, 68, 0.18) 0%, rgba(11, 17, 32, 0.95) 75%)',
          }}
        />
        {/* Linhas de grade tech */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(14, 165, 233, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(14, 165, 233, 0.08) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
            opacity: 0.6,
          }}
        />
      </AbsoluteFill>

      {/* Flash sutil de alerta vermelho no instante zero */}
      {impactFlash > 0 && (
        <AbsoluteFill
          style={{
            backgroundColor: '#EF4444',
            opacity: impactFlash,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Linha sutil de scanner cibernético em movimento constante */}
      <div
        style={{
          position: 'absolute',
          top: scanlineY,
          left: 60,
          right: 60,
          height: 2,
          background: 'linear-gradient(90deg, transparent, rgba(239, 68, 68, 0.8), transparent)',
          boxShadow: '0 0 15px rgba(239, 68, 68, 0.8)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo principal dentro da Safe Zone (y 160 a 1560, x 60 a 1020) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
        }}
      >
        {/* Badge de Alerta no Topo (Safe Zone y=165) */}
        <div
          style={{
            transform: `scale(${Math.max(0, badgeSpring * alertPulse)})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 22px',
            borderRadius: 30,
            backgroundColor: 'rgba(239, 68, 68, 0.22)',
            border: '2px solid rgba(239, 68, 68, 0.85)',
            boxShadow: `0 0 ${redGlow}px rgba(239, 68, 68, 0.55)`,
            backdropFilter: 'blur(8px)',
          }}
        >
          <AlertIcon size={30} color="#EF4444" />
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FECACA',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            FALHA SILENCIOSA
          </span>
        </div>

        {/* Pergunta-Gancho Completa com Impacto Tipográfico Unificado desde 00:00 (Frame 0) */}
        <div
          style={{
            marginTop: 18,
            textAlign: 'center',
            width: '100%',
          }}
        >
          {/* Linha 1: SUA OPERAÇÃO PARA */}
          <div
            style={{
              fontSize: 52,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.15,
              textTransform: 'uppercase',
              textShadow: '0 4px 15px rgba(0,0,0,0.85)',
              transform: `translateY(${(1 - title1Spring) * 15}px) scale(${0.92 + title1Spring * 0.08})`,
              opacity: title1Spring,
            }}
          >
            SUA OPERAÇÃO{' '}
            <span
              style={{
                color: '#FFFFFF',
                backgroundColor: '#EF4444',
                padding: '4px 18px',
                borderRadius: 14,
                boxShadow: '0 0 25px rgba(239, 68, 68, 0.6)',
                display: 'inline-block',
                transform: `scale(${alertPulse})`,
              }}
            >
              PARA
            </span>
          </div>

          {/* Linha 2: E você só descobre pela reclamação? */}
          <div
            style={{
              marginTop: 12,
              fontSize: 42,
              fontWeight: 800,
              color: '#E2E8F0',
              lineHeight: 1.25,
              textShadow: '0 4px 15px rgba(0,0,0,0.85)',
              transform: `translateY(${(1 - title2Spring) * 15}px) scale(${0.92 + title2Spring * 0.08})`,
              opacity: title2Spring,
            }}
          >
            e você só descobre pela{' '}
            <span
              style={{
                marginLeft: 10,
                color: reclamoHighlight > 0 ? '#F59E0B' : '#FCA5A5',
                fontWeight: 900,
                textDecoration: 'underline',
                textDecorationThickness: '4px',
                textUnderlineOffset: '8px',
                display: 'inline-block',
                transform: `scale(${1 + reclamoHighlight * 0.08})`,
                textShadow:
                  reclamoHighlight > 0 ? '0 0 20px rgba(245, 158, 11, 0.7)' : 'none',
              }}
            >
              reclamação?
            </span>
          </div>
        </div>

        {/* Centro Focal: HUD do Incidente + Card de Reclamação com Stagger e Push-in */}
        <div
          style={{
            marginTop: 28,
            width: '100%',
            maxWidth: 900,
            transform: `scale(${cardsPushIn})`,
            transformOrigin: 'center center',
          }}
        >
          {/* Card 1: HUD de Status do Servidor - Entra no frame 4 com pop/shake sutil */}
          <div
            style={{
              width: '100%',
              padding: '20px 24px',
              borderRadius: 20,
              backgroundColor: 'rgba(15, 23, 42, 0.94)',
              border: '2px solid rgba(239, 68, 68, 0.7)',
              boxShadow: `0 10px 30px rgba(0, 0, 0, 0.7), 0 0 ${redGlow}px rgba(239, 68, 68, 0.35)`,
              transform: `translateX(${hudShake}px) translateY(${(1 - hudSpring) * 25}px) scale(${0.94 + hudSpring * 0.06})`,
              opacity: hudSpring,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <ServerIcon size={42} color="#EF4444" />
              <div>
                <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                  STATUS DO SERVIDOR
                </div>
                <div style={{fontSize: 32, color: '#F87171', fontWeight: 700}}>
                  Falha Crítica na Automação
                </div>
              </div>
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                backgroundColor: 'rgba(239, 68, 68, 0.28)',
                padding: '8px 18px',
                borderRadius: 14,
                border: '2px solid #EF4444',
                boxShadow: `0 0 ${redGlow}px rgba(239, 68, 68, 0.7)`,
                transform: `scale(${alertPulse})`,
              }}
            >
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: 7,
                  backgroundColor: '#EF4444',
                  boxShadow: '0 0 12px #EF4444',
                }}
              />
              <span style={{color: '#FECACA', fontSize: 32, fontWeight: 900}}>
                PARADO
              </span>
            </div>
          </div>

          {/* Card 2: Card Mockup de Reclamação do Cliente - ENTRADA ESCALONADA (STAGGER) aos ~1.9s (frame 58)
              Sobe com spring dinâmico no exato momento da fala "descobre pela reclamação" */}
          {frame >= 58 && (
            <div
              style={{
                marginTop: 22,
                width: '100%',
                padding: '24px 28px',
                borderRadius: 24,
                backgroundColor: 'rgba(15, 23, 42, 0.96)',
                border: '2px solid rgba(239, 68, 68, 0.8)',
                boxShadow: `0 18px 45px rgba(0, 0, 0, 0.85), 0 0 ${redGlow}px rgba(239, 68, 68, 0.35)`,
                transform: `translateY(${cardSlideY}px) scale(${0.92 + cardSpring * 0.08})`,
                opacity: cardSpring,
                boxSizing: 'border-box',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 16,
                  borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
                  paddingBottom: 12,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: 22,
                      backgroundColor: '#EF4444',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 26,
                      color: '#FFFFFF',
                      fontWeight: 900,
                    }}
                  >
                    !
                  </div>
                  <div>
                    <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                      Cliente
                    </div>
                    <div style={{fontSize: 32, color: '#94A3B8', fontWeight: 600}}>
                      Reclamação de Incidente
                    </div>
                  </div>
                </div>
                <div
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.35)',
                    padding: '6px 16px',
                    borderRadius: 12,
                    color: '#FECACA',
                    fontSize: 32,
                    fontWeight: 900,
                    border: '1.5px solid rgba(239, 68, 68, 0.85)',
                    boxShadow: `0 0 ${redGlow}px rgba(239, 68, 68, 0.6)`,
                    transform: `scale(${urgentPulse})`,
                  }}
                >
                  URGENTE
                </div>
              </div>

              <div
                style={{
                  fontSize: 36,
                  fontWeight: 700,
                  color: '#F8FAFC',
                  lineHeight: 1.35,
                  backgroundColor: 'rgba(30, 41, 59, 0.85)',
                  padding: '16px 20px',
                  borderRadius: 16,
                  borderLeft: '5px solid #EF4444',
                }}
              >
                &ldquo;O sistema travou e ninguém avisou nada! O que aconteceu?&rdquo;
              </div>

              {/* Gancho oficial fixado no rodapé do card surgindo aos ~3.0s */}
              {frame >= 90 && (
                <div
                  style={{
                    marginTop: 18,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    color: '#38BDF8',
                    fontSize: 32,
                    fontWeight: 800,
                    transform: `scale(${subGanchoSpring})`,
                    opacity: subGanchoSpring,
                  }}
                >
                  <span style={{fontSize: 32}}>🔍</span>
                  <span>Processo travou sem você saber?</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
