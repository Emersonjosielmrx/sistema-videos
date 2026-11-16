import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena4Cartao: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (push-in + drift)
  const bgScale = interpolate(frame, [0, 120], [1.02, 1.16], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(frame, [0, 120], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Logo & Nome entram de imediato
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Headline entra aos 0.25s (frame 8)
  const headlineSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Feature 1: Docker + Portainer + Traefik entra aos 0.5s (frame 15)
  const feat1Spring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Botão CTA entra aos 0.8s (frame 24) e segue pulsando até o fim
  const buttonSpring = spring({
    frame: frame - 24,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Arroba entra aos 1.0s (frame 30)
  const handleSpring = spring({
    frame: frame - 30,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Feature 2: n8n + Sentinela entra escalonada aos 1.5s (frame 45)
  const feat2Spring = spring({
    frame: frame - 45,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Feature 3: Backup Automático entra escalonada aos 2.3s (frame 68)
  const feat3Spring = spring({
    frame: frame - 68,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Pulso contínuo do botão (1.00 a 1.06 até o ÚLTIMO FRAME)
  const buttonPulse = 1.0 + Math.sin(frame * 0.18) * 0.045;

  // Brilho/shimmer animado passando no botão periodicamente
  const shimmerX = interpolate(frame % 45, [0, 45], [-150, 950]);

  // Flutuação sutil contínua do logo
  const logoFloat = Math.sin(frame * 0.12) * 6;

  // Movimento contínuo do grid de fundo
  const gridOffset = frame * 1.5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Imagem de Fundo Desfocada com Movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(18px)',
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

      {/* Véu Escuro da Marca com Gradiente Tecnológico */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 30%, rgba(14, 165, 233, 0.28) 0%, rgba(15, 23, 42, 0.9) 55%, rgba(15, 23, 42, 0.98) 100%)',
        }}
      />

      {/* Grid cibernético em movimento constante */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.18,
          backgroundImage:
            'linear-gradient(rgba(14, 165, 233, 0.35) 1px, transparent 1px), linear-gradient(90deg, rgba(14, 165, 233, 0.35) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          backgroundPosition: `${gridOffset}px ${gridOffset}px`,
          pointerEvents: 'none',
        }}
      />

      {/* ================= CONTEÚDO CENTRAL UNIFICADO (y: 200 a 1400) ================= */}
      <div
        style={{
          position: 'absolute',
          top: 210,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 20,
        }}
      >
        {/* Bloco 1: Logo & Marca */}
        <div
          style={{
            opacity: logoSpring,
            transform: `scale(${logoSpring}) translateY(${logoFloat}px)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 14,
          }}
        >
          {/* Escudo 3D com Glow */}
          <div
            style={{
              width: 92,
              height: 92,
              borderRadius: 26,
              background:
                'linear-gradient(135deg, #0EA5E9 0%, #0284C7 60%, #0369A1 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 50,
              boxShadow:
                '0 12px 35px rgba(14, 165, 233, 0.55), inset 0 2px 4px rgba(255, 255, 255, 0.4)',
              border: '2px solid rgba(255, 255, 255, 0.25)',
            }}
          >
            🛡️
          </div>

          <div
            style={{
              fontSize: 62,
              fontWeight: 900,
              letterSpacing: 2,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              textShadow:
                '0 4px 24px rgba(14, 165, 233, 0.7), 0 2px 8px rgba(0,0,0,0.8)',
            }}
          >
            VPS BLINDADA
          </div>
        </div>

        {/* Bloco 2: Slogan dos Fatos */}
        <div
          style={{
            marginTop: 22,
            opacity: headlineSpring,
            transform: `translateY(${(1 - headlineSpring) * 15}px)`,
            maxWidth: 900,
          }}
        >
          <div
            style={{
              fontSize: 42,
              fontWeight: 800,
              color: '#F8FAFC',
              lineHeight: 1.25,
              textWrap: 'balance',
              textShadow: '0 4px 14px rgba(0,0,0,0.8)',
            }}
          >
            Sua VPS pronta, segura e com backup automático.
          </div>
        </div>

        {/* Bloco 3: 3 Cards com Fatos Permitidos escalonados ao longo do encerramento */}
        <div
          style={{
            marginTop: 36,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            width: '100%',
            maxWidth: 880,
          }}
        >
          {/* Card 1: Docker + Portainer + Traefik */}
          <div
            style={{
              opacity: feat1Spring,
              transform: `scale(${feat1Spring}) translateY(${(1 - feat1Spring) * 15}px)`,
              padding: '16px 28px',
              borderRadius: 20,
              background: 'rgba(30, 41, 59, 0.85)',
              border: '1.5px solid rgba(14, 165, 233, 0.5)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
              color: '#F1F5F9',
              fontSize: 34,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 12,
            }}
          >
            <span style={{fontSize: 32}}>⚙️</span>
            <span>Docker + Portainer + Traefik</span>
          </div>

          {/* Card 2: n8n + Bot Sentinela */}
          <div
            style={{
              opacity: feat2Spring,
              transform: `scale(${Math.max(0, feat2Spring)}) translateY(${(1 - Math.max(0, feat2Spring)) * 15}px)`,
              padding: '16px 28px',
              borderRadius: 20,
              background: 'rgba(30, 41, 59, 0.85)',
              border: '1.5px solid rgba(14, 165, 233, 0.5)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
              color: '#F1F5F9',
              fontSize: 34,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 12,
            }}
          >
            <span style={{fontSize: 32}}>🤖</span>
            <span>n8n Self-Hosted • Bot Sentinela</span>
          </div>

          {/* Card 3: Backup Automático */}
          <div
            style={{
              opacity: feat3Spring,
              transform: `scale(${Math.max(0, feat3Spring)}) translateY(${(1 - Math.max(0, feat3Spring)) * 15}px)`,
              padding: '16px 28px',
              borderRadius: 20,
              background: 'rgba(30, 41, 59, 0.85)',
              border: '1.5px solid rgba(16, 185, 129, 0.5)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
              color: '#F1F5F9',
              fontSize: 34,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 12,
            }}
          >
            <span style={{fontSize: 32}}>✓</span>
            <span>Backup Automático e Relatórios</span>
          </div>
        </div>

        {/* Bloco 4: Botão CTA Principal Pulsante */}
        <div
          style={{
            marginTop: 48,
            width: '100%',
            maxWidth: 880,
            opacity: buttonSpring,
            transform: `scale(${buttonSpring * buttonPulse})`,
          }}
        >
          <div
            style={{
              width: '100%',
              height: 114,
              borderRadius: 32,
              background: 'linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%)',
              boxShadow:
                '0 18px 45px rgba(14, 165, 233, 0.55), 0 0 30px rgba(14, 165, 233, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              border: '2px solid rgba(255, 255, 255, 0.4)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer Light Sweep */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shimmerX,
                width: 150,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                color: '#FFFFFF',
                fontSize: 48,
                fontWeight: 900,
                letterSpacing: 2,
                textTransform: 'uppercase',
                textShadow: '0 2px 8px rgba(0,0,0,0.5)',
              }}
            >
              CHAME NO DIRECT
            </span>

            <span style={{fontSize: 44, color: '#FFFFFF'}}>➔</span>
          </div>
        </div>

        {/* Bloco 5: Arroba Oficial + Verificado */}
        <div
          style={{
            marginTop: 28,
            opacity: handleSpring,
            transform: `translateY(${(1 - handleSpring) * 15}px)`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 14,
            padding: '10px 28px',
            borderRadius: 999,
            background: 'rgba(15, 23, 42, 0.8)',
            border: '1.5px solid rgba(14, 165, 233, 0.6)',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span
            style={{
              color: '#38BDF8',
              fontSize: 42,
              fontWeight: 800,
              letterSpacing: 1,
            }}
          >
            @vpsblindada.ia
          </span>
          <div
            style={{
              width: 26,
              height: 26,
              borderRadius: '50%',
              background: '#0EA5E9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF',
              fontSize: 16,
              fontWeight: 900,
            }}
          >
            ✓
          </div>
        </div>

        {/* Micro-nota de Confiança */}
        <div
          style={{
            marginTop: 18,
            opacity: handleSpring,
            color: '#94A3B8',
            fontSize: 32,
            fontWeight: 600,
            letterSpacing: 0.5,
          }}
        >
          Setup Completo • Monitoramento Contínuo
        </div>
      </div>
    </div>
  );
};
