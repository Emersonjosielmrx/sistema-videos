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

interface Cena0Props {
  fontFamily: string;
}

export const Cena0: React.FC<Cena0Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera no fundo (zoom in suave + leve drift)
  const bgScale = interpolate(frame, [0, 133], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 133], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Animação de entrada dos blocos de texto sincronizados com a narração
  // 1. Tag superior: entra aos 0.15s (frame 4)
  const tagSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 2. Linha 1: "VOU CONTINUAR" entra aos 0.3s (frame 9)
  const l1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // 3. Linha 2: "RECEBENDO OS PEDIDOS" entra aos 1.0s (frame 30)
  const l2Spring = spring({
    frame: frame - 30,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // 4. Linha 3: "NO MEU WHATSAPP?" entra aos 2.1s (frame 63)
  const l3Spring = spring({
    frame: frame - 63,
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // 5. Selo de resposta / Gancho fixo entra aos 2.8s (frame 84)
  const ganchoSpring = spring({
    frame: frame - 84,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Movimento contínuo flutuante nos textos para garantir > 10% de dinamismo
  const floatY = Math.sin(frame / 12) * 5;
  const pulseScale = 1 + Math.sin(frame / 8) * 0.02;

  return (
    <AbsoluteFill style={{backgroundColor: '#1a0509', overflow: 'hidden'}}>
      {/* Imagem de Fundo com zoom vivo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
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
      </div>

      {/* Véu com gradiente luminoso para contraste mantendo a foto visível */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 35%, rgba(49, 6, 15, 0.45) 0%, rgba(20, 2, 5, 0.78) 100%)',
        }}
      />

      {/* Conteúdo Seguro (y=170 a 750 — blindagem total do pizzaiolo que fica em y >= 800) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
        }}
      >
        {/* Tag Superior Dinâmica: Dúvida -> Gancho de Resposta */}
        {frame < 75 ? (
          <div
            style={{
              opacity: Math.max(0, tagSpring),
              transform: `translateY(${(1 - tagSpring) * -20}px)`,
              backgroundColor: 'rgba(225, 29, 72, 0.3)',
              border: '2px solid rgba(225, 29, 72, 0.85)',
              padding: '8px 28px',
              borderRadius: 999,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              boxShadow: '0 4px 20px rgba(225, 29, 72, 0.4)',
              marginBottom: 30,
            }}
          >
            <span style={{fontSize: 34}}>❓</span>
            <span
              style={{
                color: '#FFFFFF',
                fontSize: 34,
                fontWeight: 800,
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              Dúvida Frequente
            </span>
          </div>
        ) : (
          <div
            style={{
              opacity: Math.max(0, ganchoSpring),
              transform: `scale(${ganchoSpring}) translateY(${(1 - ganchoSpring) * -15}px)`,
              backgroundColor: 'rgba(20, 20, 25, 0.92)',
              border: '2px solid #FACC15',
              padding: '8px 30px',
              borderRadius: 999,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              boxShadow: '0 4px 25px rgba(250, 204, 21, 0.4)',
              marginBottom: 30,
            }}
          >
            <span style={{fontSize: 34}}>📲</span>
            <span
              style={{
                color: '#FACC15',
                fontSize: 34,
                fontWeight: 900,
                letterSpacing: 1,
                textTransform: 'uppercase',
              }}
            >
              Pedidos direto no seu WhatsApp
            </span>
          </div>
        )}

        {/* Bloco Cinético Central da Pergunta (Texto da fala) */}
        <div
          style={{
            marginTop: 20,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 18,
            transform: `translateY(${floatY}px)`,
          }}
        >
          {/* Linha 1 */}
          <div
            style={{
              opacity: Math.max(0, l1Spring),
              transform: `scale(${interpolate(l1Spring, [0, 1], [0.8, 1])}) translateY(${(1 - l1Spring) * 30}px)`,
            }}
          >
            <span
              style={{
                fontSize: 66,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                textShadow: '0 6px 20px rgba(0,0,0,0.85)',
                letterSpacing: '-1px',
              }}
            >
              Vou continuar
            </span>
          </div>

          {/* Linha 2 */}
          <div
            style={{
              opacity: Math.max(0, l2Spring),
              transform: `scale(${interpolate(l2Spring, [0, 1], [0.8, 1])}) translateY(${(1 - l2Spring) * 30}px)`,
            }}
          >
            <span
              style={{
                fontSize: 66,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                textShadow: '0 6px 20px rgba(0,0,0,0.85)',
                letterSpacing: '-1px',
              }}
            >
              recebendo os pedidos
            </span>
          </div>

          {/* Linha 3: Destaque no WhatsApp */}
          <div
            style={{
              marginTop: 10,
              opacity: Math.max(0, l3Spring),
              transform: `scale(${interpolate(l3Spring, [0, 1], [0.75, 1]) * pulseScale}) translateY(${(1 - l3Spring) * 30}px)`,
              backgroundColor: '#25D366',
              padding: '12px 36px',
              borderRadius: 24,
              boxShadow: '0 10px 30px rgba(37, 211, 102, 0.45)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <span style={{fontSize: 48}}>💬</span>
            <span
              style={{
                fontSize: 68,
                fontWeight: 900,
                color: '#052E16',
                textTransform: 'uppercase',
                letterSpacing: '-0.5px',
              }}
            >
              no meu WhatsApp?
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
