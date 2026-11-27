import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const time = frame / fps;

  // Câmera contínua com push-in ≥ 4%
  const bgScale = interpolate(frame, [0, 200], [1.06, 1.22], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 200], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Microdinâmica constante (respiração viva)
  const floatY = Math.sin(frame / 14) * 6;
  const pulseScale = 1 + Math.sin(frame / 10) * 0.015;

  // Animação de entrada do badge superior (0.1s)
  const badgeSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do bloco 1 da pergunta (0.318s = frame ~10)
  const title1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Entrada do bloco 2 da dor ("mas não entendo nada de tecnologia", 3.107s = frame ~93)
  const dorProgress = spring({
    frame: frame - 93,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do selo gancho de alívio ("Agente sem complicação", 4.27s = frame ~128)
  const ganchoSpring = spring({
    frame: frame - 128,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13', overflow: 'hidden'}}>
      {/* Fundo com foto e movimento contínuo */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <img
          src={staticFile('img_0.jpg')}
          alt="Fundo"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Glow roxo dinâmico e vinheta cinematográfica */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(124, 58, 237, 0.35) 0%, rgba(11, 13, 19, 0.78) 65%, rgba(11, 13, 19, 0.96) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Grid tech animado preenchendo a área ociosa do fundo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'radial-gradient(rgba(124, 58, 237, 0.25) 2px, transparent 2px)',
          backgroundSize: '44px 44px',
          backgroundPosition: `0px ${frame * 1.2}px`,
          opacity: 0.85,
          pointerEvents: 'none',
        }}
      />

      {/* Luz radial pulsante e orbital no centro nobre */}
      <div
        style={{
          position: 'absolute',
          top: '35%',
          left: '50%',
          width: 500,
          height: 500,
          marginLeft: -250,
          marginTop: -250,
          borderRadius: 250,
          background: 'radial-gradient(circle, rgba(124, 58, 237, 0.25) 0%, transparent 70%)',
          transform: `scale(${1 + Math.sin(frame / 12) * 0.1})`,
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo centralizado verticalmente na área nobre da Safe Zone */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 70,
          right: 90,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 22,
        }}
      >
        {/* Badge superior com box protetor */}
        <div
          style={{
            opacity: interpolate(badgeSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(badgeSpring, [0, 1], [-20, 0])}px) scale(${pulseScale})`,
            background: 'rgba(11, 13, 19, 0.95)',
            border: '2px solid rgba(124, 58, 237, 0.7)',
            borderRadius: 999,
            padding: '10px 28px',
            boxShadow: '0 8px 24px rgba(124, 58, 237, 0.35)',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: 7,
              background: '#7C3AED',
              boxShadow: '0 0 14px #7C3AED',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#EDE9FE',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            Dúvida Frequente
          </span>
        </div>

        {/* Card Principal da Pergunta do Cliente */}
        <div
          style={{
            width: '100%',
            opacity: interpolate(title1Spring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(title1Spring, [0, 1], [40, 0]) + floatY}px) scale(${interpolate(title1Spring, [0, 1], [0.94, 1])})`,
            background: 'rgba(11, 13, 19, 0.94)',
            borderRadius: 36,
            border: '2px solid rgba(124, 58, 237, 0.45)',
            padding: '38px 36px',
            boxShadow: '0 24px 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(124, 58, 237, 0.2)',
            display: 'flex',
            flexDirection: 'column',
            gap: 26,
          }}
        >
          {/* Avatar e Usuário simulando pergunta real */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
              paddingBottom: 20,
            }}
          >
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: 32,
                background: 'linear-gradient(135deg, #7C3AED, #4F46E5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                boxShadow: '0 6px 18px rgba(124, 58, 237, 0.5)',
              }}
            >
              💬
            </div>
            <div style={{display: 'flex', flexDirection: 'column'}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Pergunta de Seguidor
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#CBD5E1',
                }}
              >
                Direct • Automação
              </span>
            </div>
          </div>

          {/* Texto Cinético 1: "Quero uma IA trabalhando por mim" */}
          <div
            style={{
              fontFamily,
              fontSize: 52,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.25,
              textWrap: 'balance',
            }}
          >
            "Quero uma{' '}
            <span
              style={{
                background: '#7C3AED',
                color: '#FFFFFF',
                padding: '4px 14px',
                borderRadius: 14,
                boxShadow: '0 4px 16px rgba(124, 58, 237, 0.6)',
              }}
            >
              IA
            </span>{' '}
            trabalhando por mim...
          </div>

          {/* Texto Cinético 2: "mas não entendo nada de tecnologia?" */}
          {time >= 2.9 && (
            <div
              style={{
                opacity: interpolate(dorProgress, [0, 1], [0, 1]),
                transform: `translateY(${interpolate(dorProgress, [0, 1], [25, 0])}px)`,
                background: 'rgba(239, 68, 68, 0.18)',
                border: '2px solid rgba(254, 202, 202, 0.45)',
                borderRadius: 24,
                padding: '24px 28px',
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 46,
                  fontWeight: 900,
                  color: '#FECACA',
                  lineHeight: 1.25,
                  textWrap: 'balance',
                }}
              >
                ...mas não entendo nada de tecnologia?"
              </div>
              {/* Aviso com alto contraste em amarelo claro (#FFD166) e tamanho legível */}
              <div
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#FFD166',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  textShadow: '0 2px 6px rgba(0,0,0,0.8)',
                }}
              >
                ⚠️ O medo de precisar programar
              </div>
            </div>
          )}

          {/* Selo de resposta/alívio com o gancho do briefing */}
          {time >= 4.2 && (
            <div
              style={{
                opacity: interpolate(ganchoSpring, [0, 1], [0, 1]),
                transform: `scale(${interpolate(ganchoSpring, [0, 1], [0.9, 1])})`,
                background: 'linear-gradient(90deg, rgba(124, 58, 237, 0.95), rgba(79, 70, 229, 0.95))',
                borderRadius: 20,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 12,
                boxShadow: '0 10px 25px rgba(124, 58, 237, 0.4)',
              }}
            >
              <span style={{fontSize: 34}}>✨</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Agente de IA sem complicação
              </span>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
