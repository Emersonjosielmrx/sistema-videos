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
import briefing from '../../../trabalhos/followupia_ia_20261116_052420/public/briefing.json';

interface Cena4Props {
  fontFamily: string;
  corMarca: string;
  corFundo: string;
  corTextoMarca: string;
}

export const Cena4: React.FC<Cena4Props> = ({
  fontFamily,
  corMarca,
  corFundo,
  corTextoMarca,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((31.34 - 27.4) * fps);

  // Transição de entrada suave com slide direcional e fade (conecta suavemente vindo da filmagem da Cena 3)
  const enterTrans = spring({
    frame,
    fps,
    config: {damping: 15, stiffness: 140},
  });
  const enterSlideY = interpolate(enterTrans, [0, 1], [45, 0]);

  // Entrada escalonada (stagger com spring) para cada elemento
  const s0 = spring({frame: frame - 0, fps, config: {damping: 14, stiffness: 160}}); // Selo categoria
  const s1 = spring({frame: frame - 5, fps, config: {damping: 14, stiffness: 160}}); // Marca Hero
  const s2 = spring({frame: frame - 10, fps, config: {damping: 14, stiffness: 160}}); // Proposta de valor
  const s3 = spring({frame: frame - 16, fps, config: {damping: 14, stiffness: 160}}); // Botão CTA
  const s4 = spring({frame: frame - 22, fps, config: {damping: 14, stiffness: 160}}); // Arroba
  const s5 = spring({frame: frame - 28, fps, config: {damping: 14, stiffness: 160}}); // Slogan

  // Push-in contínuo de câmera na cena inteira (1.0x para 1.06x)
  const scenePushIn = interpolate(frame, [0, durFrames], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Zoom contínuo na foto de fundo
  const bgScale = interpolate(frame, [0, durFrames], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });
  const bgPanY = interpolate(frame, [0, durFrames], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Pulso contínuo e orgânico no botão CTA (scale 1.0 para 1.04 em loop contínuo até o final)
  const btnPulse = 1.0 + 0.04 * Math.sin(frame * 0.18);
  const btnGlow = interpolate(Math.sin(frame * 0.18), [-1, 1], [30, 60]);

  // Efeito de brilho/shimmer deslizando continuamente pelo botão 'CHAME NO DIRECT' em loop constante
  const shimmerPos = interpolate(frame % 32, [0, 32], [-350, 950]);

  // Micro-flutuações contínuas de respiração
  const floatBrand = Math.sin(frame / 8) * 5;
  const floatPill = Math.cos(frame / 9) * 4;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: corFundo,
        overflow: 'hidden',
        opacity: enterTrans,
      }}
    >
      {/* Imagem de fundo com zoom e blur suave */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(12px) brightness(0.6)',
          }}
        />
      </AbsoluteFill>

      {/* Degradê escuro com iluminação radial no centro */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle at 50% 45%, rgba(78,205,196,0.22) 0%, rgba(17,24,39,0.85) 55%, rgba(17,24,39,0.98) 100%)',
        }}
      />

      {/* Círculo de luz decorativo central pulsando */}
      <div
        style={{
          position: 'absolute',
          top: 850,
          left: '50%',
          width: 800,
          height: 800,
          transform: 'translate(-50%, -50%)',
          borderRadius: 400,
          background: `radial-gradient(circle, rgba(78,205,196,0.2) 0%, transparent 70%)`,
          filter: 'blur(70px)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo limpo, hierarquizado e 100% acima de y: 1580 (Safe Zone rigorosa do Reels) */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          transform: `scale(${scenePushIn}) translateY(${enterSlideY}px)`,
        }}
      >
        {/* 1. Selo do Topo */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            backgroundColor: 'rgba(78, 205, 196, 0.16)',
            border: `2px solid ${corMarca}`,
            borderRadius: 999,
            padding: '10px 28px',
            marginBottom: 20,
            transform: `translateY(${interpolate(s0, [0, 1], [30, 0]) + floatPill}px)`,
            opacity: s0,
            boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: 7,
              backgroundColor: corMarca,
              boxShadow: `0 0 10px ${corMarca}`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: corMarca,
              letterSpacing: 0.5,
            }}
          >
            FOLLOW-UP AUTOMÁTICO QUE VENDE
          </span>
        </div>

        {/* 2. Nome da Marca Hero */}
        <div
          style={{
            fontFamily,
            fontSize: 98,
            fontWeight: 900,
            color: '#FFFFFF',
            marginBottom: 16,
            lineHeight: 1.1,
            textShadow: '0 8px 30px rgba(0,0,0,0.8)',
            transform: `translateY(${interpolate(s1, [0, 1], [30, 0]) + floatBrand}px)`,
            opacity: s1,
          }}
        >
          {briefing.marca}
        </div>

        {/* 3. Proposta de Valor em 1 linha única (sem panfleto nem caixas concorrentes) */}
        <div
          style={{
            fontFamily,
            fontSize: 44,
            fontWeight: 700,
            color: '#E2E8F0',
            maxWidth: 900,
            lineHeight: 1.3,
            textWrap: 'balance',
            marginBottom: 70,
            textShadow: '0 4px 15px rgba(0,0,0,0.6)',
            transform: `translateY(${interpolate(s2, [0, 1], [30, 0])}px)`,
            opacity: s2,
          }}
        >
          Follow-ups com IA que recuperam vendas no WhatsApp
        </div>

        {/* 4. Botão CTA Protagonista com pulso contínuo (scale 1.0 a 1.04) e shimmer contínuo */}
        <div
          style={{
            position: 'relative',
            backgroundColor: corMarca,
            borderRadius: 999,
            width: '100%',
            maxWidth: 880,
            padding: '28px 0',
            boxShadow: `0 15px ${btnGlow}px rgba(78, 205, 196, 0.65)`,
            transform: `translateY(${interpolate(s3, [0, 1], [30, 0])}px) scale(${btnPulse})`,
            opacity: s3,
            marginBottom: 36,
            overflow: 'hidden',
          }}
        >
          {/* Reflexo metálico/shimmer deslizando continuamente em loop */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 180,
              background:
                'linear-gradient(90deg, transparent, rgba(255,255,255,0.75), transparent)',
              transform: `translateX(${shimmerPos}px) skewX(-25deg)`,
              pointerEvents: 'none',
            }}
          />

          <span
            style={{
              position: 'relative',
              fontFamily,
              fontSize: 56,
              fontWeight: 900,
              color: corTextoMarca,
              letterSpacing: 2,
            }}
          >
            CHAME NO DIRECT
          </span>
        </div>

        {/* 5. Identificador Obrigatório @followupia.ia em pílula luminosa de alto contraste */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            backgroundColor: 'rgba(255,255,255,0.14)',
            border: '2px solid rgba(255,255,255,0.4)',
            borderRadius: 999,
            padding: '16px 54px',
            marginBottom: 28,
            boxShadow: '0 8px 25px rgba(0,0,0,0.5)',
            transform: `translateY(${interpolate(s4, [0, 1], [30, 0]) + floatPill}px)`,
            opacity: s4,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1,
            }}
          >
            {briefing.arroba}
          </span>
        </div>

        {/* 6. Slogan seguro, 100% acima de y: 1580, com cor branca (#FFFFFF) de alto contraste */}
        <div
          style={{
            transform: `translateY(${interpolate(s5, [0, 1], [30, 0])}px)`,
            opacity: s5,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 36,
              fontWeight: 800,
              color: '#FFFFFF',
              textShadow: '0 4px 15px rgba(0,0,0,0.85)',
              letterSpacing: 0.5,
            }}
          >
            Pare de perder venda por esquecimento
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
