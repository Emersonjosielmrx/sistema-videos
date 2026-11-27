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

interface Cena4Props {
  fontFamily: string;
}

export const Cena4: React.FC<Cena4Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (zoom 1.05 -> 1.16)
  const bgScale = interpolate(frame, [0, 120], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });

  // Entrada escalonada dos blocos com molas suaves
  const logoSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const pill1Spring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const pill2Spring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const pill3Spring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const ctaSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Flutuação sutil da logo
  const floatY = Math.sin(frame / 10) * 6;

  // Pulso contínuo do botão CTA (1.00 a 1.07 em ciclos de ~1.2s = ~36 frames)
  const pulseFactor = Math.sin((frame * 2 * Math.PI) / 36);
  const buttonScale = 1.035 + pulseFactor * 0.035;

  // Shimmer passando pelo botão
  const shimmerX = interpolate(frame % 45, [0, 45], [-200, 700], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Fundo com foto desfocada e zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(30px)',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu escuro da marca com gradiente de alta profundidade */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 32%, rgba(255,169,77,0.18) 0%, rgba(15,23,42,0.88) 45%, rgba(11,13,19,0.97) 85%)',
        }}
      />

      {/* Conteúdo harmoniosamente distribuído na Safe Zone (y: 220 a 1400) */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 60,
        }}
      >
        {/* Bloco de Marca: Ícone + Nome + Posicionamento */}
        <div
          style={{
            transform: `scale(${Math.max(0, logoSpring)}) translateY(${floatY}px)`,
            opacity: Math.min(1, logoSpring),
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <div
            style={{
              width: 108,
              height: 108,
              borderRadius: 30,
              backgroundColor: '#FFA94D',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 14px 40px rgba(255, 169, 77, 0.55)',
            }}
          >
            <span style={{fontSize: 58}}>📅</span>
          </div>

          <span
            style={{
              fontFamily,
              fontSize: 84,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2.5,
              textTransform: 'uppercase',
              textShadow:
                '0 4px 20px rgba(0,0,0,0.8), 0 0 45px rgba(255,169,77,0.45)',
              marginTop: 4,
            }}
          >
            AGENDA IA
          </span>

          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 700,
              color: '#E2E8F0',
              textAlign: 'center',
              maxWidth: 880,
              lineHeight: 1.25,
            }}
          >
            Agendamentos automáticos com IA direto no WhatsApp
          </span>
        </div>

        {/* 3 Destaques Modernos em Pílulas Nativas (sem formato de slide corporativo) */}
        <div
          style={{
            marginTop: 48,
            width: 860,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {/* Destaque 1 */}
          <div
            style={{
              transform: `scale(${Math.max(0, pill1Spring)})`,
              opacity: Math.min(1, pill1Spring),
              backgroundColor: 'rgba(15, 23, 42, 0.94)',
              border: '1.5px solid rgba(255, 169, 77, 0.35)',
              borderRadius: 22,
              padding: '16px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 18,
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}
          >
            <span style={{fontSize: 34, color: '#FFA94D'}}>⚡</span>
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 700,
                color: '#FFFFFF',
              }}
            >
              Atendimento e agendamento 24 horas
            </span>
          </div>

          {/* Destaque 2 */}
          <div
            style={{
              transform: `scale(${Math.max(0, pill2Spring)})`,
              opacity: Math.min(1, pill2Spring),
              backgroundColor: 'rgba(15, 23, 42, 0.94)',
              border: '1.5px solid rgba(255, 169, 77, 0.35)',
              borderRadius: 22,
              padding: '16px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 18,
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}
          >
            <span style={{fontSize: 34, color: '#FFA94D'}}>🤖</span>
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 700,
                color: '#FFFFFF',
              }}
            >
              Agenda, confirma e reagenda sozinha
            </span>
          </div>

          {/* Destaque 3 */}
          <div
            style={{
              transform: `scale(${Math.max(0, pill3Spring)})`,
              opacity: Math.min(1, pill3Spring),
              backgroundColor: 'rgba(15, 23, 42, 0.94)',
              border: '1.5px solid rgba(255, 169, 77, 0.35)',
              borderRadius: 22,
              padding: '16px 28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
              <span style={{fontSize: 34, color: '#4ADE80'}}>✓</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                Sem conflito de horário
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFA94D',
              }}
            >
              A partir de R$ 199/mês
            </span>
          </div>
        </div>

        {/* Botão de Chamada para Ação (CTA) — Enérgico, Pulsando com Shimmer */}
        <div
          style={{
            marginTop: 56,
            width: 860,
            transform: `scale(${Math.max(0, ctaSpring) * buttonScale})`,
            opacity: Math.min(1, ctaSpring),
            position: 'relative',
            overflow: 'hidden',
            borderRadius: 28,
            background: 'linear-gradient(135deg, #FFA94D 0%, #FF922B 100%)',
            boxShadow: '0 16px 45px rgba(255, 169, 77, 0.55)',
            padding: '28px 36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 18,
          }}
        >
          {/* Efeito Shimmer */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 140,
              transform: `translateX(${shimmerX}px) skewX(-20deg)`,
              background:
                'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
              pointerEvents: 'none',
            }}
          />

          <span style={{fontSize: 46}}>💬</span>
          <span
            style={{
              fontFamily,
              fontSize: 50,
              fontWeight: 900,
              color: '#0F172A',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            CHAME NO DIRECT
          </span>
        </div>

        {/* Perfil Oficial (@sintetizerisada) visível desde o início */}
        <div
          style={{
            marginTop: 40,
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            backgroundColor: 'rgba(11, 13, 19, 0.92)',
            padding: '14px 34px',
            borderRadius: 24,
            border: '1.5px solid rgba(255, 169, 77, 0.45)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.75)',
          }}
        >
          <span style={{fontSize: 34, color: '#FFA94D'}}>👉</span>
          <span
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 800,
              color: '#FFA94D',
              letterSpacing: 1,
            }}
          >
            @sintetizerisada
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
