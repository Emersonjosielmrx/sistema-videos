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

  // Duração local da cena final: ~118 frames (28.09s a 32.03s)
  // Slow-zoom contínuo na cena final até o corte
  const sceneScale = interpolate(frame, [0, 118], [1.0, 1.03], {
    extrapolateRight: 'clamp',
  });
  const bgScale = interpolate(frame, [0, 118], [1.06, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 118], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Micro-movimento contínuo de flutuação
  const floatY = Math.sin(frame / 12) * 5;

  // MICRO-MOTION CONTÍNUO NO BOTÃO DE CTA (elimina o congelamento entre q14 e q15):
  // 1. Pulso de escala suave contínuo entre 1.00 e 1.04
  const ctaPulse = 1.02 + Math.sin((frame * Math.PI * 2) / 18) * 0.02;

  // 2. Balanço suave na seta (atrai o olhar para o clique)
  const arrowX = Math.sin((frame * Math.PI * 2) / 14) * 8;

  // 3. Efeito shimmer contínuo de brilho diagonal varrendo o botão em loop
  const shimmerProgress = (frame % 28) / 28;
  const shimmerTranslateX = interpolate(shimmerProgress, [0, 1], [-250, 950]);

  // 4. Pulsação sutil na luz de fundo do botão
  const glowAlpha = 0.55 + Math.sin(frame / 6) * 0.2;

  // Entrada em mola dos elementos do cartão final (com stagger ágil para presença total já em q13)
  const brandSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Linha de Valor Forte no centro com pulso sutil contínuo
  const valueSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 130},
  });
  const valuePulse = 1 + Math.sin((frame * Math.PI * 2) / 24) * 0.02;

  // Entrada em mola do Botão CTA (presente com destaque total e movimento contínuo)
  const btnSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Entrada do Perfil Oficial @
  const atSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#111827',
        fontFamily,
        overflow: 'hidden',
      }}
    >
      {/* Imagem de Fundo com zoom contínuo e desfoque suave */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(10px) brightness(0.6)',
          }}
        />
        {/* Véu escuro da marca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 50%, rgba(20, 184, 166, 0.22) 0%, rgba(17, 24, 39, 0.94) 80%)',
          }}
        />
      </AbsoluteFill>

      {/* Partículas / orbes de luz ambiente animados */}
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: 140,
          width: 440,
          height: 440,
          borderRadius: '50%',
          background: 'rgba(20, 184, 166, 0.16)',
          filter: 'blur(75px)',
          transform: `scale(${1 + Math.sin(frame / 14) * 0.12})`,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 380,
          right: 120,
          width: 480,
          height: 480,
          borderRadius: '50%',
          background: 'rgba(13, 148, 136, 0.2)',
          filter: 'blur(85px)',
          transform: `scale(${1 - Math.sin(frame / 16) * 0.12})`,
          pointerEvents: 'none',
        }}
      />

      {/* CONTEÚDO CENTRAL DO CARTÃO FINAL (Safe Zone y=190 a 1340, elevado e com respiro total do rodapé) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          bottom: 580,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          transform: `scale(${sceneScale})`,
          zIndex: 30,
        }}
      >
        {/* 1. Bloco da Marca e Logo com leve flutuação */}
        <div
          style={{
            transform: `translateY(${floatY}px) scale(${0.9 + brandSpring * 0.1})`,
            opacity: brandSpring,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 12,
          }}
        >
          {/* Ícone de Marca com brilho */}
          <div
            style={{
              width: 90,
              height: 90,
              borderRadius: 28,
              background: 'linear-gradient(135deg, #14B8A6 0%, #0D9488 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow:
                '0 12px 35px rgba(20, 184, 166, 0.55), 0 0 25px rgba(20, 184, 166, 0.45)',
              border: '2.5px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
                fill="#FFFFFF"
              />
            </svg>
          </div>

          {/* Nome da Marca Grande */}
          <div
            style={{
              fontSize: 54,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -0.5,
              textShadow: '0 6px 20px rgba(0,0,0,0.85)',
            }}
          >
            GESTÃO DE GRUPOS IA
          </div>

          {/* 1 Frase do que o produto faz (fatos do briefing) */}
          <div
            style={{
              fontSize: 36,
              fontWeight: 700,
              color: '#5EEAD4',
              lineHeight: 1.3,
              maxWidth: 860,
              textWrap: 'balance',
            }}
          >
            Seus grupos de WhatsApp no automático
          </div>
        </div>

        {/* 2. Linha de Valor Forte e Direta no Centro (substitui os 3 blocos densos de bullets por valor direto e limpo) */}
        <div
          style={{
            opacity: valueSpring,
            transform: `scale(${(0.92 + valueSpring * 0.08) * valuePulse}) translateY(${(1 - valueSpring) * 16}px)`,
            background: 'rgba(17, 24, 39, 0.92)',
            border: '2px solid rgba(20, 184, 166, 0.65)',
            borderRadius: 26,
            padding: '18px 36px',
            boxShadow:
              '0 12px 35px rgba(0, 0, 0, 0.7), 0 0 25px rgba(20, 184, 166, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            maxWidth: 920,
          }}
        >
          <span style={{fontSize: 34, color: '#2DD4BF'}}>✦</span>
          <span
            style={{
              fontSize: 36,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
              textAlign: 'center',
              textShadow: '0 2px 8px rgba(0,0,0,0.5)',
            }}
          >
            Tudo automático nos seus grupos
          </span>
          <span style={{fontSize: 34, color: '#2DD4BF'}}>✦</span>
        </div>

        {/* 3. Bloco CTA + Perfil Oficial (elevados em ~140px, preenchendo o vazio central e garantindo respiro total da legenda) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 18,
            width: '100%',
          }}
        >
          {/* BOTÃO CTA COM MICROINTERAÇÃO CONTÍNUA (Pulso de escala 1.0 a 1.04 + Shimmer varrendo em loop + Balanço na seta) */}
          <div
            style={{
              transform: `scale(${btnSpring * ctaPulse})`,
              opacity: btnSpring,
              position: 'relative',
              overflow: 'hidden',
              width: '100%',
              maxWidth: 820,
              borderRadius: 28,
              padding: '22px 36px',
              background: 'linear-gradient(135deg, #14B8A6 0%, #0D9488 100%)',
              boxShadow: `0 15px 45px rgba(20, 184, 166, ${glowAlpha}), 0 0 35px rgba(20, 184, 166, 0.45)`,
              border: '2.5px solid rgba(255, 255, 255, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 18,
            }}
          >
            {/* Faixa de brilho (shimmer) contínua varrendo o botão diagonalmente em loop */}
            <div
              style={{
                position: 'absolute',
                top: -40,
                bottom: -40,
                left: 0,
                width: 160,
                background:
                  'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.75) 50%, transparent 100%)',
                transform: `translateX(${shimmerTranslateX}px) skewX(-25deg)`,
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
                textShadow: '0 2px 10px rgba(0,0,0,0.35)',
              }}
            >
              CHAME NO DIRECT
            </span>

            {/* Seta animada com balanço contínuo */}
            <div
              style={{
                transform: `translateX(${arrowX}px)`,
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <svg width="38" height="38" viewBox="0 0 24 24" fill="none">
                <path
                  d="M5 12h14M12 5l7 7-7 7"
                  stroke="#FFFFFF"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>

          {/* Perfil Oficial (@gestaodegrupos.ia) com folga total acima do rodapé */}
          <div
            style={{
              transform: `scale(${atSpring})`,
              opacity: atSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1.5px solid rgba(255, 255, 255, 0.2)',
              padding: '12px 28px',
              borderRadius: 22,
              boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
            }}
          >
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <rect
                x="2"
                y="2"
                width="20"
                height="20"
                rx="5"
                stroke="#14B8A6"
                strokeWidth="2.5"
              />
              <circle
                cx="12"
                cy="12"
                r="4"
                stroke="#14B8A6"
                strokeWidth="2.5"
              />
              <circle cx="17.5" cy="6.5" r="1.5" fill="#14B8A6" />
            </svg>
            <span
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 0.5,
              }}
            >
              @gestaodegrupos.ia
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
