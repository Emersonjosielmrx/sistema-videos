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

  // Fundo com push-in suave constante
  const bgScale = interpolate(frame, [0, 116], [1.04, 1.14], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada suave
  const sceneOpacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Mola da Marca e Logo
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Mola do Texto de Proposta
  const textSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Mola dos Itens de Benefício
  const itemsSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Mola do Botão CTA
  const buttonSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Mola do @Handle: Ativo e com alto contraste desde o PRIMEIRO FRAME da Cena 4
  const handleSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Pulso contínuo do botão CTA até o último frame (scale 1.0 a 1.06)
  const buttonPulse = 1.0 + 0.035 * Math.sin(frame * 0.22);

  // Efeito shimmer / brilho metálico passando no botão
  const shimmerProgress = (frame % 45) / 45;
  const shimmerX = interpolate(shimmerProgress, [0, 1], [-200, 920]);

  // Flutuação sutil da marca
  const logoFloat = Math.sin(frame * 0.12) * 4;

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#1A0307'}}>
      {/* Imagem de Fundo com visual aquecido da pizzaria e Zoom Lento */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(8px)',
            transform: `scale(${bgScale})`,
          }}
        />
        {/* Véu Escuro Sofisticado da Marca preservando iluminação acolhedora */}
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(22, 3, 7, 0.90) 0%, rgba(49, 6, 15, 0.82) 45%, rgba(15, 2, 4, 0.88) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo Central do Cartão Final (Safe Zone y=150 a 1580) */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 24,
        }}
      >
        {/* Marca / Logotipo com Ícone (y=240 a 400) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
            transform: `scale(${Math.min(logoSpring, 1)}) translateY(${logoFloat}px)`,
            opacity: logoSpring,
          }}
        >
          <div
            style={{
              width: 96,
              height: 96,
              borderRadius: '50%',
              backgroundColor: '#E11D48',
              border: '3px solid #FACC15',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 50,
              boxShadow: '0 8px 32px rgba(225, 29, 72, 0.65)',
            }}
          >
            🍕
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 62,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -1,
              textAlign: 'center',
              textShadow: '0 4px 20px rgba(0,0,0,0.85)',
            }}
          >
            CARDÁPIO DIGITAL
          </div>
        </div>

        {/* Frase Resumo do Produto (y=420 a 540) */}
        <div
          style={{
            maxWidth: 920,
            textAlign: 'center',
            transform: `translateY(${(1 - textSpring) * 20}px)`,
            opacity: textSpring,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 600,
              color: '#E2E8F0',
              lineHeight: 1.35,
              textShadow: '0 2px 10px rgba(0,0,0,0.8)',
            }}
          >
            Cardápio com fotos no celular e pedidos direto no WhatsApp com IA
          </div>
        </div>

        {/* Checklist com Fatos Comprovados (y=560 a 860) */}
        <div
          style={{
            width: '100%',
            maxWidth: 900,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            transform: `translateY(${(1 - itemsSpring) * 20}px)`,
            opacity: itemsSpring,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(26, 4, 9, 0.90)',
              border: '1.5px solid rgba(250, 204, 21, 0.45)',
              borderRadius: 20,
              padding: '16px 24px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            }}
          >
            <span style={{fontSize: 34, color: '#25D366'}}>✓</span>
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 700,
                color: '#FFFFFF',
              }}
            >
              Cardápio digital com fotos no celular
            </span>
          </div>

          <div
            style={{
              backgroundColor: 'rgba(26, 4, 9, 0.90)',
              border: '1.5px solid rgba(225, 29, 72, 0.45)',
              borderRadius: 20,
              padding: '16px 24px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            }}
          >
            <span style={{fontSize: 34, color: '#25D366'}}>✓</span>
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 700,
                color: '#FFFFFF',
              }}
            >
              Pedidos direto pelo WhatsApp
            </span>
          </div>

          <div
            style={{
              backgroundColor: 'rgba(26, 4, 9, 0.90)',
              border: '1.5px solid rgba(250, 204, 21, 0.45)',
              borderRadius: 20,
              padding: '16px 24px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            }}
          >
            <span style={{fontSize: 34, color: '#25D366'}}>✓</span>
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 700,
                color: '#FACC15',
              }}
            >
              IA respondendo dúvidas na hora
            </span>
          </div>
        </div>

        {/* Botão de Ação CTA Principal Pulsando (y=900 a 1050) */}
        <div
          style={{
            marginTop: 12,
            width: '100%',
            maxWidth: 900,
            display: 'flex',
            justifyContent: 'center',
            transform: `scale(${Math.min(buttonSpring, 1) * buttonPulse})`,
            opacity: buttonSpring,
          }}
        >
          <div
            style={{
              width: '100%',
              background: 'linear-gradient(90deg, #E11D48 0%, #BE123C 100%)',
              border: '3px solid rgba(255, 255, 255, 0.45)',
              borderRadius: 24,
              padding: '24px 36px',
              boxShadow:
                '0 18px 45px rgba(225, 29, 72, 0.65), 0 0 30px rgba(225, 29, 72, 0.35)',
              textAlign: 'center',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer / reflexo de brilho passando */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shimmerX,
                width: 140,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
                textShadow: '0 3px 12px rgba(0,0,0,0.5)',
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>
        </div>

        {/* Handle Oficial @futebolcom.ia2 com Alto Contraste desde o Primeiro Frame (y=1080 a 1180) */}
        <div
          style={{
            marginTop: 8,
            transform: `scale(${Math.min(handleSpring, 1)}) translateY(${(1 - handleSpring) * 12}px)`,
            opacity: Math.max(0.95, handleSpring),
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              backgroundColor: 'rgba(26, 4, 9, 0.96)',
              border: '2.5px solid #FACC15',
              padding: '12px 36px',
              borderRadius: 50,
              boxShadow:
                '0 8px 24px rgba(0,0,0,0.7), 0 0 22px rgba(250, 204, 21, 0.4)',
            }}
          >
            <span style={{fontSize: 32}}>👉</span>
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#FACC15',
                letterSpacing: 0.8,
                textShadow: '0 2px 8px rgba(0,0,0,0.8)',
              }}
            >
              @futebolcom.ia2
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
