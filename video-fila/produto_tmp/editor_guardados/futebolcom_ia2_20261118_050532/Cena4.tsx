import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';
import {CORES} from './types';

export const Cena4: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Slow zoom in contínuo na cena até o fim (1.00 -> 1.14)
  const sceneZoom = interpolate(frame, [0, 116], [1.0, 1.14], {
    extrapolateRight: 'clamp',
  });

  // Fundo com zoom contínuo e movimento suave de luz
  const bgScale = interpolate(frame, [0, 116], [1.05, 1.22], {
    extrapolateRight: 'clamp',
  });
  const glowX = interpolate(frame, [0, 116], [35, 65], {
    extrapolateRight: 'clamp',
  });

  // Entradas suaves com spring
  const enterSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Animação contínua de pulso do botão CTA (1.00 a 1.05 em loop até o fim)
  const btnPulse = 1.025 + Math.sin(frame * 0.2) * 0.025;

  // Varredura contínua de brilho (shimmer sweep) cruzando o botão
  const shimmerPos = interpolate(frame % 36, [0, 36], [-120, 220]);

  // Movimento 3D suave e flutuação orgânica do celular
  const phoneFloatY = Math.sin(frame * 0.09) * 8;
  const phoneRotateY = interpolate(frame, [0, 116], [-7, -2], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        fontFamily,
        transform: `scale(${sceneZoom})`,
        transformOrigin: 'center 50%',
      }}
    >
      {/* Fundo Desfocado com Véu Escuro da Marca e Movimento Contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: -40,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(16px)',
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

      {/* Véu Escuro Profundo com Luz Dinâmica */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(circle at ${glowX}% 45%, rgba(225,29,72,0.48) 0%, rgba(49,6,15,0.92) 55%, #150207 100%)`,
        }}
      />

      {/* Container Principal Centralizado na Área Útil (y: 195 a 1540) */}
      <div
        style={{
          position: 'absolute',
          top: 195,
          left: 60,
          right: 60,
          bottom: 380,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          zIndex: 30,
          transform: `scale(${Math.max(0, enterSpring)})`,
          opacity: Math.min(1, enterSpring),
        }}
      >
        {/* Bloco Superior: Marca e Título da Solução */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 10,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              background: 'rgba(250, 204, 21, 0.18)',
              border: `2px solid ${CORES.apoio}`,
              borderRadius: 999,
              padding: '6px 24px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              boxShadow: '0 4px 18px rgba(0,0,0,0.5)',
            }}
          >
            <span style={{fontSize: 30}}>🍔</span>
            <span
              style={{
                color: CORES.apoio,
                fontSize: 32,
                fontWeight: 900,
                letterSpacing: 1.2,
                textTransform: 'uppercase',
              }}
            >
              CARDÁPIO DIGITAL COM IA
            </span>
          </div>

          <div
            style={{
              fontSize: 52,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 0.5,
              textTransform: 'uppercase',
              textShadow: '0 6px 25px rgba(0,0,0,0.85)',
              lineHeight: 1.15,
            }}
          >
            PEDIDOS NO WHATSAPP
          </div>

          <div
            style={{
              color: '#E2E8F0',
              fontSize: 32,
              fontWeight: 600,
            }}
          >
            O cliente vê fotos no celular e tira dúvidas na hora
          </div>
        </div>

        {/* Bloco Central: Mockup 3D de Smartphone exibindo o Cardápio Aberto com a Foto */}
        <div
          style={{
            width: 820,
            height: 480,
            borderRadius: 36,
            background: '#0B141A',
            border: '5px solid #2A3942',
            boxShadow:
              '0 25px 60px rgba(0, 0, 0, 0.85), 0 0 45px rgba(225, 29, 72, 0.35)',
            transform: `perspective(1000px) rotateY(${phoneRotateY}deg) translateY(${phoneFloatY}px)`,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* Header do Chat no Mockup */}
          <div
            style={{
              height: 76,
              background: '#1F2C34',
              borderBottom: '2px solid #2A3942',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 24px',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 999,
                  background: CORES.marca,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 26,
                }}
              >
                🍔
              </div>
              <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 800}}>
                Cardápio Digital
              </div>
            </div>
            <div
              style={{
                color: '#25D366',
                fontSize: 32,
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: 999,
                  background: '#25D366',
                }}
              />
              Online com IA
            </div>
          </div>

          {/* Conteúdo do Cardápio Aberto */}
          <div
            style={{
              flex: 1,
              padding: '18px 24px',
              display: 'flex',
              alignItems: 'center',
              gap: 22,
              background:
                'radial-gradient(circle at 50% 30%, #111B21 0%, #0B141A 100%)',
            }}
          >
            <Img
              src={staticFile('burger.jpg')}
              style={{
                width: 220,
                height: 220,
                borderRadius: 20,
                objectFit: 'cover',
                border: '2px solid rgba(250, 204, 21, 0.6)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.6)',
                flexShrink: 0,
              }}
            />
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
                justifyContent: 'center',
              }}
            >
              <div style={{color: '#FFFFFF', fontSize: 36, fontWeight: 900}}>
                Burger Artesanal
              </div>
              <div style={{color: '#E2E8F0', fontSize: 32, fontWeight: 600}}>
                Com queijo e fotos no celular
              </div>
              <div
                style={{
                  background: 'rgba(37, 211, 102, 0.18)',
                  border: '1.5px solid #25D366',
                  borderRadius: 12,
                  padding: '6px 16px',
                  color: '#86EFAC',
                  fontSize: 32,
                  fontWeight: 700,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  alignSelf: 'flex-start',
                }}
              >
                <span>⚡</span> Pedido no WhatsApp
              </div>
            </div>
          </div>
        </div>

        {/* Bloco Inferior: CTA Gigante Pulsando com Shimmer Sweep, Arroba e Benefício */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            width: '100%',
          }}
        >
          {/* Botão de Ação CTA: "CHAME NO DIRECT" Ampliado e Pulsando */}
          <div
            style={{
              transform: `scale(${btnPulse})`,
              position: 'relative',
              overflow: 'hidden',
              background: 'linear-gradient(135deg, #E11D48 0%, #BE123C 100%)',
              border: `3.5px solid ${CORES.apoio}`,
              borderRadius: 999,
              padding: '24px 64px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 18,
              boxShadow:
                '0 18px 50px rgba(225, 29, 72, 0.85), 0 0 35px rgba(250, 204, 21, 0.5)',
            }}
          >
            {/* Shimmer / Varredura de Brilho contínua cruzando o botão */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 90,
                left: `${shimmerPos}%`,
                background:
                  'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.45) 50%, transparent 100%)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span style={{fontSize: 44}}>💬</span>
            <span
              style={{
                color: '#FFFFFF',
                fontSize: 46,
                fontWeight: 900,
                letterSpacing: 1.5,
                textTransform: 'uppercase',
                textShadow: '0 2px 10px rgba(0,0,0,0.6)',
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>

          {/* Selos Inferiores: Benefício + Arroba Oficial */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.92)',
                border: '2px solid rgba(255, 255, 255, 0.28)',
                borderRadius: 999,
                padding: '12px 30px',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                boxShadow: '0 6px 20px rgba(0,0,0,0.6)',
              }}
            >
              <span style={{fontSize: 32}}>📸</span>
              <span
                style={{
                  color: '#FFFFFF',
                  fontSize: 34,
                  fontWeight: 800,
                  letterSpacing: 0.5,
                }}
              >
                @futebolcom.ia2
              </span>
            </div>

            <div
              style={{
                background: 'rgba(35, 18, 24, 0.88)',
                border: '2px solid rgba(244, 63, 94, 0.4)',
                borderRadius: 999,
                padding: '12px 28px',
                color: '#FCA5A5',
                fontSize: 32,
                fontWeight: 700,
                boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
                whiteSpace: 'nowrap',
              }}
            >
              Demonstração no direct ✨
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
