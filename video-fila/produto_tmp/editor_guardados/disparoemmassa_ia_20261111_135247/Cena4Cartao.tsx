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

const VERDE = '#22C55E';
const ESCURO = '#111827';
const TEXTO_ESCURO = '#121216';

export const Cena4Cartao: React.FC<{
  fontFamily: string;
  marca: string;
  arroba: string;
}> = ({fontFamily, marca, arroba}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  // Cena 4: 25.95s a 29.90s (119 frames)

  // Zoom e pan contínuos até o último milissegundo (>8% de variação entre 20% e 80%)
  const bgScale = interpolate(frame, [0, 119], [1.04, 1.18], {extrapolateRight: 'clamp'});
  const bgRotate = interpolate(frame, [0, 119], [0, 2], {extrapolateRight: 'clamp'});
  const glowY = interpolate(frame, [0, 119], [-80, 100], {extrapolateRight: 'clamp'});

  // Stagger escalonado suave dos elementos (ícone -> título -> descrição -> destaques -> botão -> @handle)
  const iconPop = spring({frame: frame - 1, fps, config: {damping: 13, stiffness: 150}});
  const titlePop = spring({frame: frame - 6, fps, config: {damping: 13, stiffness: 140}});
  const descPop = spring({frame: frame - 11, fps, config: {damping: 14, stiffness: 140}});
  const tagsPop = spring({frame: frame - 16, fps, config: {damping: 14, stiffness: 140}});
  const ctaPop = spring({frame: frame - 21, fps, config: {damping: 12, stiffness: 150}});
  const handlePop = spring({frame: frame - 26, fps, config: {damping: 14, stiffness: 140}});

  // Pulso sutil de escala [1, 1.03, 1] a cada 1.2s (36 frames) no botão CTA
  const cycle36 = frame % 36;
  const btnPulse = interpolate(cycle36, [0, 18, 36], [1, 1.035, 1], {extrapolateRight: 'clamp'});
  const floatY = Math.sin(frame * 0.14) * 6;

  // Brilhos passando no botão de CTA e no @ da conta
  const shineX = interpolate(frame % 45, [0, 45], [-200, 950]);
  const handleShineX = interpolate((frame + 18) % 48, [0, 48], [-180, 600]);

  return (
    <AbsoluteFill style={{backgroundColor: ESCURO}}>
      {/* Fundo de foto desfocada com véu da marca em movimento contínuo */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(18px) brightness(0.38)',
            transform: `scale(${bgScale}) rotate(${bgRotate}deg)`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 48%, rgba(34, 197, 94, 0.25) 0%, rgba(17, 24, 39, 0.94) 75%)',
            transform: `translateY(${glowY}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo central distribuído verticalmente com harmonia na Safe Zone (y=260..1540) */}
      <div
        style={{
          position: 'absolute',
          top: 260,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: 26,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* 1. Ícone da marca com entrada em stagger */}
        <div
          style={{
            width: 124,
            height: 124,
            borderRadius: 36,
            background: VERDE,
            color: TEXTO_ESCURO,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily,
            fontSize: 58,
            fontWeight: 900,
            boxShadow: '0 20px 45px rgba(34,197,94,0.5)',
            opacity: iconPop,
            transform: `scale(${interpolate(iconPop, [0, 1], [0.75, 1])})`,
          }}
        >
          IA
        </div>

        {/* 2. Título da Marca */}
        <div
          style={{
            fontFamily,
            fontSize: 64,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.1,
            textShadow: '0 8px 28px rgba(0,0,0,0.8)',
            opacity: titlePop,
            transform: `translateY(${interpolate(titlePop, [0, 1], [24, 0])}px)`,
          }}
        >
          {marca}
        </div>

        {/* 3. Card explicativo da proposta de valor */}
        <div
          style={{
            fontFamily,
            fontSize: 38,
            fontWeight: 700,
            color: '#E2E8F0',
            maxWidth: 880,
            lineHeight: 1.25,
            background: 'rgba(17, 24, 39, 0.9)',
            padding: '18px 30px',
            borderRadius: 24,
            border: '2px solid rgba(34, 197, 94, 0.55)',
            boxShadow: '0 16px 36px rgba(0,0,0,0.6)',
            opacity: descPop,
            transform: `translateY(${interpolate(descPop, [0, 1], [24, 0])}px) scale(${interpolate(descPop, [0, 1], [0.95, 1])})`,
          }}
        >
          Disparo em massa inteligente com envio automático no WhatsApp
        </div>

        {/* 4. Destaques dos fatos permitidos */}
        <div
          style={{
            display: 'flex',
            gap: 14,
            justifyContent: 'center',
            opacity: tagsPop,
            transform: `translateY(${interpolate(tagsPop, [0, 1], [20, 0])}px)`,
          }}
        >
          <div
            style={{
              background: 'rgba(34, 197, 94, 0.16)',
              border: '2px solid rgba(34, 197, 94, 0.55)',
              borderRadius: 999,
              padding: '10px 22px',
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#86EFAC',
            }}
          >
            ✓ Rotação de números
          </div>
          <div
            style={{
              background: 'rgba(34, 197, 94, 0.16)',
              border: '2px solid rgba(34, 197, 94, 0.55)',
              borderRadius: 999,
              padding: '10px 22px',
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#86EFAC',
            }}
          >
            ✓ Mensagens personalizadas
          </div>
        </div>

        {/* 5. Botão CTA Principal com pulso contínuo a cada 1.2s e varredura de luz */}
        <div
          style={{
            marginTop: 10,
            opacity: ctaPop,
            transform: `scale(${ctaPop * btnPulse})`,
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              background: VERDE,
              color: TEXTO_ESCURO,
              fontFamily,
              fontSize: 42,
              fontWeight: 900,
              padding: '24px 44px',
              borderRadius: 999,
              boxShadow: '0 22px 55px rgba(34, 197, 94, 0.65)',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              whiteSpace: 'nowrap',
            }}
          >
            <span>CHAME A GENTE NO DIRECT</span>
            {/* Sheen passando */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shineX,
                width: 120,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.65), transparent)',
                transform: 'skewX(-20deg)',
              }}
            />
          </div>
        </div>

        {/* 6. @arroba com brilho de entrada e destaque verde */}
        <div
          style={{
            position: 'relative',
            overflow: 'hidden',
            marginTop: 6,
            opacity: handlePop,
            transform: `translateY(${interpolate(handlePop, [0, 1], [20, 0])}px) scale(${interpolate(handlePop, [0, 1], [0.92, 1])})`,
            background: 'rgba(17, 24, 39, 0.95)',
            border: `3px solid ${VERDE}`,
            borderRadius: 999,
            padding: '14px 42px',
            fontFamily,
            fontSize: 42,
            fontWeight: 800,
            color: '#FFFFFF',
            boxShadow: '0 12px 32px rgba(34, 197, 94, 0.4)',
          }}
        >
          <span>{arroba}</span>
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: handleShineX,
              width: 90,
              background:
                'linear-gradient(90deg, transparent, rgba(34,197,94,0.5), transparent)',
              transform: 'skewX(-20deg)',
            }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};
