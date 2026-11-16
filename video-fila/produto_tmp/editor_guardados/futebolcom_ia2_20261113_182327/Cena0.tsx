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

  // Efeito Ken Burns dinâmico e suave (zoom contínuo e pan diagonal)
  const bgScale = interpolate(frame, [0, 164], [1.06, 1.24], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 164], [0, -40], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 164], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Transição de saída suave no final da cena
  const sceneOpacity = interpolate(frame, [150, 164], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação do Badge de Topo
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Gancho Completo Imediato (entra no primeiro frame)
  const hookSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Animação Palavra 2 "PERDE VENDAS?" com destaque imediato e pulso
  const perdeVendasSpring = spring({
    frame,
    fps,
    config: {damping: 10, stiffness: 160},
  });

  // Animação Card Alerta: "Demora no WhatsApp" (~1.8s / frame 54)
  const cardSpring = spring({
    frame: frame - 54,
    fps,
    config: {damping: 13, stiffness: 115},
  });

  // Pulso contínuo sutil
  const pulse = Math.sin(frame * 0.14) * 4;
  const destaqueScale = 1.0 + 0.025 * Math.sin(frame * 0.2);

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#1A0307'}}>
      {/* Imagem de Fundo com Movimento Ken Burns */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translate(${bgTranslateX}px, ${bgTranslateY}px)`,
          }}
        />
        {/* Overlay escuro elegante preservando contraste */}
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(26, 3, 7, 0.78) 0%, rgba(26, 3, 7, 0.45) 45%, rgba(15, 2, 4, 0.88) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Badge Topo Informativo (y=180 a 240) */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
        }}
      >
        <div
          style={{
            fontFamily,
            fontSize: 32,
            fontWeight: 800,
            color: '#FACC15',
            backgroundColor: 'rgba(26, 4, 9, 0.88)',
            border: '2px solid rgba(250, 204, 21, 0.5)',
            padding: '10px 26px',
            borderRadius: 50,
            letterSpacing: 1.2,
            textTransform: 'uppercase',
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <span>🍕</span>
          <span>ATENDIMENTO NO WHATSAPP</span>
        </div>
      </div>

      {/* Bloco Central de Impacto / Gancho Cinético Imediato (y=290 a 720) */}
      <div
        style={{
          position: 'absolute',
          top: 290,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
        }}
      >
        {/* Pergunta Completa de Impacto Visível desde o Frame 0 */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
            transform: `scale(${Math.min(hookSpring, 1)}) translateY(${(1 - hookSpring) * 20}px)`,
            opacity: Math.min(hookSpring, 1),
          }}
        >
          {/* Linha 1: SUA PIZZARIA */}
          <div
            style={{
              fontFamily,
              fontSize: 54,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -0.5,
              textAlign: 'center',
              textShadow: '0 4px 16px rgba(0,0,0,0.85)',
            }}
          >
            SUA PIZZARIA
          </div>

          {/* Destaque Linha 2: PERDE VENDAS com super contraste e pulso */}
          <div
            style={{
              transform: `scale(${Math.min(perdeVendasSpring, 1) * destaqueScale})`,
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 66,
                fontWeight: 900,
                color: '#FFFFFF',
                background: 'linear-gradient(135deg, #E11D48 0%, #BE123C 100%)',
                padding: '14px 38px',
                borderRadius: 22,
                boxShadow:
                  '0 16px 36px rgba(225, 29, 72, 0.6), 0 0 20px rgba(225, 29, 72, 0.4)',
                border: '2px solid rgba(255, 255, 255, 0.35)',
                letterSpacing: -0.5,
                textAlign: 'center',
              }}
            >
              PERDE VENDAS?
            </div>
          </div>

          {/* Linha 3: NO WHATSAPP? */}
          <div
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              color: '#FACC15',
              letterSpacing: -0.5,
              textAlign: 'center',
              textShadow: '0 3px 12px rgba(0,0,0,0.9)',
            }}
          >
            NO WHATSAPP?
          </div>
        </div>

        {/* Card Alerta: Demora nas mensagens */}
        {frame >= 50 && (
          <div
            style={{
              marginTop: 14,
              width: '100%',
              maxWidth: 920,
              backgroundColor: 'rgba(22, 3, 7, 0.94)',
              border: '2px solid rgba(250, 204, 21, 0.55)',
              borderRadius: 24,
              padding: '22px 28px',
              boxShadow: `0 16px 40px rgba(0,0,0,0.65), 0 0 24px rgba(250, 204, 21, 0.15)`,
              transform: `scale(${Math.min(cardSpring, 1)}) translateY(${(1 - cardSpring) * 30 + pulse}px)`,
              opacity: cardSpring,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                marginBottom: 8,
              }}
            >
              <span style={{fontSize: 38}}>⏳</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#FACC15',
                  lineHeight: 1.2,
                }}
              >
                Demora nas mensagens do WhatsApp?
              </span>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
                color: '#E2E8F0',
                lineHeight: 1.3,
                paddingLeft: 54,
              }}
            >
              Clientes esperam no pico e desistem de pedir
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
