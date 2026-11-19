import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES} from './constants';

interface Cena4Props {
  fontFamily: string;
}

export const Cena4: React.FC<Cena4Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de push-in no fundo
  const bgScale = interpolate(frame, [0, 120], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Fade in rápido do cartão final (frames 0 a 6)
  const entryOpacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Animação imediata e fluida (pronta nos primeiros 10 frames)
  const contentSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Pulso contínuo do botão CTA (de 1.0 a 1.07 até o último frame)
  const pulseScale = 1.035 + Math.sin(frame * 0.16) * 0.035;

  // Shimmer passando pelo botão
  const shimmerPos = ((frame * 3.5) % 280) - 90;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: CORES.fundoEscuro,
        opacity: entryOpacity,
        fontFamily,
      }}
    >
      {/* Imagem de fundo desfocada com push-in */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(22px)',
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

      {/* Véu escuro da marca para contraste total */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(ellipse at 50% 40%, rgba(15, 23, 42, 0.90) 0%, rgba(15, 23, 42, 0.97) 100%)',
        }}
      />

      {/* Conteúdo Centralizado Distribuído na Safe Zone (y=200 a 1400) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          opacity: interpolate(contentSpring, [0, 1], [0, 1]),
          transform: `scale(${interpolate(contentSpring, [0, 1], [0.95, 1])})`,
        }}
      >
        {/* Selo Tecnológico */}
        <div
          style={{
            marginTop: 220,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 24px',
            borderRadius: 999,
            backgroundColor: 'rgba(139, 92, 246, 0.25)',
            border: `1.5px solid ${CORES.marcaClara}`,
            boxShadow: '0 4px 15px rgba(139, 92, 246, 0.4)',
          }}
        >
          <span style={{fontSize: 32}}>⚡</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            Avatar com Inteligência Artificial
          </span>
        </div>

        {/* Nome da Marca Grande */}
        <div
          style={{
            marginTop: 28,
            fontSize: 72,
            fontWeight: 900,
            color: '#FFFFFF',
            textTransform: 'uppercase',
            letterSpacing: '-1px',
            textAlign: 'center',
            textShadow: '0 8px 30px rgba(139, 92, 246, 0.6)',
          }}
        >
          Inovare Clone
        </div>

        {/* Frase oficial do que o produto faz (briefing) */}
        <div
          style={{
            marginTop: 20,
            fontSize: 38,
            fontWeight: 700,
            color: '#CBD5E1',
            textAlign: 'center',
            lineHeight: 1.3,
            maxWidth: 880,
          }}
        >
          Seu avatar com IA todo dia nas redes sociais.
        </div>

        {/* Chips de Diferenciais */}
        <div
          style={{
            marginTop: 45,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            width: '100%',
            maxWidth: 750,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              padding: '14px 24px',
              borderRadius: 16,
              backgroundColor: 'rgba(31, 41, 55, 0.88)',
              border: '1.5px solid rgba(139, 92, 246, 0.4)',
              boxShadow: '0 4px 15px rgba(0, 0, 0, 0.3)',
            }}
          >
            <span style={{fontSize: 34, color: '#10B981'}}>✓</span>
            <span style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}>
              Posturas automáticas e naturais
            </span>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              padding: '14px 24px',
              borderRadius: 16,
              backgroundColor: 'rgba(31, 41, 55, 0.88)',
              border: '1.5px solid rgba(139, 92, 246, 0.4)',
              boxShadow: '0 4px 15px rgba(0, 0, 0, 0.3)',
            }}
          >
            <span style={{fontSize: 34, color: '#10B981'}}>✓</span>
            <span style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}>
              Fala com voz em português
            </span>
          </div>
        </div>

        {/* Botão de Ação CTA (pulsando continuamente) */}
        <div
          style={{
            marginTop: 65,
            transform: `scale(${pulseScale})`,
            position: 'relative',
            overflow: 'hidden',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            padding: '24px 60px',
            borderRadius: 999,
            background: `linear-gradient(90deg, ${CORES.marcaEscura}, ${CORES.marca}, ${CORES.marcaClara})`,
            boxShadow: '0 14px 40px rgba(139, 92, 246, 0.8)',
            border: '2px solid rgba(255, 255, 255, 0.35)',
          }}
        >
          {/* Shimmer */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: `${shimmerPos}%`,
              width: 70,
              background:
                'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.45), transparent)',
              transform: 'skewX(-25deg)',
              pointerEvents: 'none',
            }}
          />
          <span
            style={{
              fontSize: 50,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            Chame no Direct
          </span>
          <span style={{fontSize: 46, color: '#FFFFFF'}}>💬</span>
        </div>

        {/* Perfil Oficial da Marca (@inovareclone) — presente desde o frame 0 */}
        <div
          style={{
            marginTop: 45,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 999,
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            border: '1.5px solid rgba(255, 255, 255, 0.25)',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.45)',
          }}
        >
          <span style={{fontSize: 34}}>📸</span>
          <span
            style={{
              fontSize: 40,
              fontWeight: 800,
              color: CORES.marcaClara,
              letterSpacing: '0.5px',
            }}
          >
            @inovareclone
          </span>
        </div>
      </div>
    </div>
  );
};
