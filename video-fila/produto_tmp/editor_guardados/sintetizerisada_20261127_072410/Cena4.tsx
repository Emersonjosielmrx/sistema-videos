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
import {FONT_FAMILY, THEME} from './theme';

// Cena 4: Cartão Final (ini 29.45, fim 33.44 -> 3.99s -> 120 frames)
// Fala: "Chame a gente no direct."

export const Cena4: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de fundo (push-in contínuo >= 4% de movimento)
  const bgScale = interpolate(frame, [0, 120], [1.05, 1.22], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 120], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Entradas escalonadas com stagger de 4 frames
  const logoSpring = spring({
    frame: frame - 1,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const subtitleSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  const card1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const card2Spring = spring({
    frame: frame - 13,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const card3Spring = spring({
    frame: frame - 17,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const card4Spring = spring({
    frame: frame - 21,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const highlightSpring = spring({
    frame: frame - 25,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const ctaSpring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const handleSpring = spring({
    frame: frame - 32,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Animação contínua no botão: pulso suave de escala (entre 1.0 e 1.04)
  const buttonPulse = 1.0 + Math.sin(frame * 0.18) * 0.035;

  // Efeito shimmer de luz contínuo passando pelo botão a cada 40 frames (~1.3s)
  const shimmerX = interpolate(frame % 40, [0, 26], [-250, 950], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.darkBg, overflow: 'hidden'}}>
      {/* Background com desfoque e push-in contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(16px)',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at center, rgba(31,41,55,0.85) 0%, rgba(11,15,25,0.96) 100%)',
          }}
        />
      </div>

      {/* Container Centralizado na Safe Zone */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          fontFamily: FONT_FAMILY,
          zIndex: 10,
        }}
      >
        {/* Bloco Superior: Marca e Frase de Produto (y: 165 a 330) */}
        <div
          style={{
            position: 'absolute',
            top: THEME.safeZone.top + 15,
            left: THEME.safeZone.left,
            right: THEME.safeZone.left,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
          }}
        >
          {/* Logo Badge */}
          {frame >= 1 && (
            <div
              style={{
                transform: `scale(${logoSpring})`,
                opacity: logoSpring,
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                background: '#1F2937F5',
                border: `2px solid ${THEME.colors.primary}`,
                padding: '10px 34px',
                borderRadius: 36,
                boxShadow: '0 12px 36px rgba(0,0,0,0.7)',
                marginBottom: 12,
              }}
            >
              <span style={{fontSize: 40}}>⚡</span>
              <span
                style={{
                  fontSize: 50,
                  fontWeight: 900,
                  color: THEME.colors.textPrimary,
                  letterSpacing: 2,
                  textTransform: 'uppercase',
                }}
              >
                Agenda IA
              </span>
            </div>
          )}

          {/* Subtítulo: 1 frase do que o produto faz */}
          {frame >= 5 && (
            <div
              style={{
                transform: `scale(${subtitleSpring})`,
                opacity: subtitleSpring,
                maxWidth: 840,
                fontSize: 36,
                fontWeight: 700,
                color: THEME.colors.textSecondary,
                lineHeight: 1.25,
                textShadow: '0 3px 12px rgba(0,0,0,0.8)',
              }}
            >
              Agendamentos automáticos 24h direto no WhatsApp, sem conflito de horários.
            </div>
          )}
        </div>

        {/* Pilares e Benefícios (distribuídos entre y: 390 e 1260, preenchendo harmoniosamente o centro) */}
        <div
          style={{
            position: 'absolute',
            top: 400,
            left: THEME.safeZone.left,
            right: THEME.safeZone.left,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
          }}
        >
          {/* Card 1: Atendimento automático 24 horas */}
          {frame >= 9 && (
            <div
              style={{
                width: 840,
                background: '#111827F5',
                border: '1.5px solid rgba(255,255,255,0.16)',
                borderRadius: 20,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                transform: `translateY(${(1 - card1Spring) * 20}px)`,
                opacity: card1Spring,
              }}
            >
              <div
                style={{
                  width: 46,
                  height: 46,
                  borderRadius: 23,
                  background: '#064E3B',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#10B981',
                  fontSize: 30,
                  fontWeight: 900,
                }}
              >
                ✓
              </div>
              <span style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}>
                Atendimento automático 24 horas
              </span>
            </div>
          )}

          {/* Card 2: Sem duplo agendamento */}
          {frame >= 13 && (
            <div
              style={{
                width: 840,
                background: '#111827F5',
                border: '1.5px solid rgba(255,255,255,0.16)',
                borderRadius: 20,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                transform: `translateY(${(1 - card2Spring) * 20}px)`,
                opacity: card2Spring,
              }}
            >
              <div
                style={{
                  width: 46,
                  height: 46,
                  borderRadius: 23,
                  background: '#064E3B',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#10B981',
                  fontSize: 30,
                  fontWeight: 900,
                }}
              >
                ✓
              </div>
              <span style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}>
                Sem conflito e sem duplo agendamento
              </span>
            </div>
          )}

          {/* Card 3: IA agenda, confirma e reagenda sozinha */}
          {frame >= 17 && (
            <div
              style={{
                width: 840,
                background: '#111827F5',
                border: '1.5px solid rgba(255,255,255,0.16)',
                borderRadius: 20,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                transform: `translateY(${(1 - card3Spring) * 20}px)`,
                opacity: card3Spring,
              }}
            >
              <div
                style={{
                  width: 46,
                  height: 46,
                  borderRadius: 23,
                  background: '#1E293B',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#60A5FA',
                  fontSize: 28,
                  fontWeight: 900,
                }}
              >
                💬
              </div>
              <span style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}>
                IA agenda, confirma e reagenda sozinha
              </span>
            </div>
          )}

          {/* Card 4: Planos a partir de R$ 199 */}
          {frame >= 21 && (
            <div
              style={{
                width: 840,
                background: '#181E2EFA',
                border: `2px solid ${THEME.colors.primary}`,
                borderRadius: 20,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 8px 26px rgba(255,169,77,0.25)',
                transform: `translateY(${(1 - card4Spring) * 20}px)`,
                opacity: card4Spring,
              }}
            >
              <div
                style={{
                  width: 46,
                  height: 46,
                  borderRadius: 23,
                  background: '#78350F',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: THEME.colors.primary,
                  fontSize: 28,
                  fontWeight: 900,
                }}
              >
                ⚡
              </div>
              <span style={{fontSize: 34, fontWeight: 800, color: THEME.colors.primary}}>
                Planos a partir de R$ 199 por mês
              </span>
            </div>
          )}

          {/* Destaque Central de Solução (preenche os ~450px centrais com autoridade) */}
          {frame >= 25 && (
            <div
              style={{
                width: 840,
                background: 'linear-gradient(135deg, #111827FA, #1F2937FA)',
                border: '1.5px dashed rgba(255,169,77,0.5)',
                borderRadius: 22,
                padding: '20px 24px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 10,
                textAlign: 'center',
                boxShadow: '0 10px 30px rgba(0,0,0,0.6)',
                transform: `scale(${highlightSpring})`,
                opacity: highlightSpring,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <span style={{fontSize: 28}}>📱</span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: THEME.colors.primary,
                    textTransform: 'uppercase',
                    letterSpacing: 1,
                  }}
                >
                  Direto no seu WhatsApp
                </span>
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.25,
                }}
              >
                Sua empresa atendendo 24 horas sem perder nenhum cliente
              </div>
            </div>
          )}
        </div>

        {/* Bloco de CTA (posicionado em y=1330 e y=1465, 100% acima de y=1580 e livre de corte do Reels) */}
        {/* Botão CTA Principal: y=1330 a 1440 */}
        {frame >= 28 && (
          <div
            style={{
              position: 'absolute',
              top: 1330,
              left: THEME.safeZone.left,
              right: THEME.safeZone.left,
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                transform: `scale(${ctaSpring * buttonPulse})`,
                opacity: ctaSpring,
                position: 'relative',
                width: 840,
                height: 105,
                background: `linear-gradient(135deg, ${THEME.colors.primary}, #F59E0B)`,
                borderRadius: 28,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow:
                  '0 14px 40px rgba(255,169,77,0.5), 0 0 30px rgba(255,169,77,0.35)',
                overflow: 'hidden',
              }}
            >
              {/* Shimmer contínuo varrendo o botão */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  left: 0,
                  width: 160,
                  background:
                    'linear-gradient(90deg, transparent, rgba(255,255,255,0.65), transparent)',
                  transform: `translateX(${shimmerX}px) skewX(-25deg)`,
                  pointerEvents: 'none',
                }}
              />

              <span
                style={{
                  fontSize: 44,
                  fontWeight: 900,
                  color: THEME.colors.textOnPrimary,
                  letterSpacing: 2,
                  textTransform: 'uppercase',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                }}
              >
                <span>📩</span> Chame no Direct
              </span>
            </div>
          </div>
        )}

        {/* Identificador da conta: y=1465 a 1520 (acima de y=1580, sem espaço indevido @sintetizerisada) */}
        {frame >= 32 && (
          <div
            style={{
              position: 'absolute',
              top: 1465,
              left: THEME.safeZone.left,
              right: THEME.safeZone.left,
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                transform: `scale(${handleSpring})`,
                opacity: handleSpring,
                background: '#0B0F19F5',
                border: '2px solid rgba(255,255,255,0.18)',
                borderRadius: 24,
                padding: '10px 32px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 8px 24px rgba(0,0,0,0.7)',
              }}
            >
              <span
                style={{
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  letterSpacing: 1,
                }}
              >
                <span style={{color: THEME.colors.primary}}>@</span>sintetizerisada
              </span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
