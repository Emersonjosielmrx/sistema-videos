import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena0Props {
  fontFamily: string;
}

export const Cena0: React.FC<Cena0Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no fundo: push-in contínuo
  const zoom = interpolate(frame, [0, 157], [1.02, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Entrada dos elementos sincronizados com as palavras
  // 1. "Consigo" aos 0.318s (~frame 10)
  const sprConsigo = spring({
    frame: frame - 9,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 2. "reativar" aos 0.799s (~frame 24)
  const sprReativar = spring({
    frame: frame - 24,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 3. "clientes antigos" aos 1.364s (~frame 41)
  const sprClientes = spring({
    frame: frame - 41,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 4. "que não compram faz tempo?" aos 2.361s (~frame 71)
  const sprNaoCompram = spring({
    frame: frame - 71,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // 5. Gancho tela ("Reative clientes no WhatsApp") aos 3.8s (~frame 114)
  const sprGancho = spring({
    frame: frame - 114,
    fps,
    config: {damping: 15, stiffness: 100},
  });

  // Micro-pulso sutil no gancho após entrar
  const ganchoPulse =
    frame > 114
      ? 1 + 0.03 * Math.sin(((frame - 114) / 30) * Math.PI * 2)
      : 1;

  // Grafismo de partículas flutuando
  const particleOffset = (frame * 1.5) % 300;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        background: '#111827',
      }}
    >
      {/* Imagem de Fundo com zoom e escurecimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${zoom})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta escura para alto contraste */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at center, rgba(17, 24, 39, 0.65) 0%, rgba(17, 24, 39, 0.95) 100%)',
          }}
        />
      </div>

      {/* Grafismos de fundo vivos: ondas de sinal e partículas */}
      <div
        style={{
          position: 'absolute',
          top: 300 - particleOffset,
          right: 120,
          width: 240,
          height: 240,
          borderRadius: '50%',
          border: '2px solid rgba(34, 197, 94, 0.18)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 450 + particleOffset * 0.7,
          left: 100,
          width: 180,
          height: 180,
          borderRadius: '50%',
          border: '2px solid rgba(34, 197, 94, 0.15)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo informativo (y=175) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 30,
            background: 'rgba(17, 24, 39, 0.88)',
            border: '2px solid rgba(34, 197, 94, 0.5)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              background: '#22C55E',
              boxShadow: '0 0 10px #22C55E',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            DÚVIDA FREQUENTE
          </span>
        </div>
      </div>

      {/* Centro: Texto Cinético Principal da Pergunta (y=380 a 1150) */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: 24,
          zIndex: 20,
        }}
      >
        {/* 1. "CONSIGO" */}
        {frame >= 8 && (
          <div
            style={{
              opacity: sprConsigo,
              transform: `scale(${0.85 + sprConsigo * 0.15}) translateY(${
                (1 - sprConsigo) * 20
              }px)`,
              fontFamily,
              fontSize: 64,
              fontWeight: 800,
              color: '#F8FAFC',
              letterSpacing: 1,
              textTransform: 'uppercase',
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
            }}
          >
            CONSIGO
          </div>
        )}

        {/* 2. "REATIVAR" destacado na marca */}
        {frame >= 22 && (
          <div
            style={{
              opacity: sprReativar,
              transform: `scale(${0.8 + sprReativar * 0.2}) translateY(${
                (1 - sprReativar) * 25
              }px)`,
              display: 'inline-block',
              background: '#22C55E',
              padding: '12px 36px',
              borderRadius: 24,
              boxShadow: '0 12px 32px rgba(34, 197, 94, 0.45)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 88,
                fontWeight: 900,
                color: '#111827',
                letterSpacing: 2,
                textTransform: 'uppercase',
                lineHeight: 1,
              }}
            >
              REATIVAR
            </span>
          </div>
        )}

        {/* 3. "CLIENTES ANTIGOS" */}
        {frame >= 39 && (
          <div
            style={{
              opacity: sprClientes,
              transform: `scale(${0.85 + sprClientes * 0.15}) translateY(${
                (1 - sprClientes) * 20
              }px)`,
              fontFamily,
              fontSize: 72,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
              textShadow: '0 4px 20px rgba(0,0,0,0.9)',
            }}
          >
            CLIENTES ANTIGOS
          </div>
        )}

        {/* 4. "QUE NÃO COMPRAM FAZ TEMPO?" */}
        {frame >= 70 && (
          <div
            style={{
              opacity: sprNaoCompram,
              transform: `scale(${0.9 + sprNaoCompram * 0.1}) translateY(${
                (1 - sprNaoCompram) * 15
              }px)`,
              padding: '16px 34px',
              borderRadius: 22,
              background: 'rgba(239, 68, 68, 0.32)',
              border: '2px solid rgba(248, 113, 113, 0.75)',
              boxShadow: '0 8px 26px rgba(0,0,0,0.7)',
              maxWidth: 880,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                lineHeight: 1.25,
                textShadow: '0 2px 10px rgba(0,0,0,0.9)',
              }}
            >
              QUE NÃO COMPRAM FAZ TEMPO?
            </span>
          </div>
        )}

        {/* 5. Gancho de tela fixo que aparece após a pergunta: "Reative clientes no WhatsApp" */}
        {frame >= 112 && (
          <div
            style={{
              marginTop: 18,
              opacity: sprGancho,
              transform: `scale(${
                (0.85 + sprGancho * 0.15) * ganchoPulse
              }) translateY(${(1 - sprGancho) * 20}px)`,
              padding: '18px 36px',
              borderRadius: 28,
              background: 'rgba(17, 24, 39, 0.95)',
              border: '2px solid #22C55E',
              boxShadow: '0 10px 30px rgba(34, 197, 94, 0.35)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <span style={{fontSize: 40}}>⚡</span>
            <span
              style={{
                fontFamily,
                fontSize: 40,
                fontWeight: 900,
                color: '#22C55E',
                letterSpacing: 1,
              }}
            >
              Reative clientes no WhatsApp
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
