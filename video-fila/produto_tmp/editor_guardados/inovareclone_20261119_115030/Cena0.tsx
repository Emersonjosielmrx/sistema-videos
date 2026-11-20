import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES, fontFamily} from './constants';

export const Cena0: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera no fundo (push-in 1.0 -> 1.12)
  const bgScale = interpolate(frame, [0, 160], [1.0, 1.12], {
    extrapolateRight: 'clamp',
  });

  // Fade de saída sutil na transição final (frames 145 a 158)
  const sceneOpacity = interpolate(frame, [145, 158], [1, 0.85], {
    extrapolateRight: 'clamp',
  });

  // 1. Badge superior "DÚVIDA FREQUENTE" (entra frame 5)
  const badgeSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 2. Gancho fixo "Vídeos sem gravar câmera" (entra frame 35 ~ 1.2s)
  const ganchoSpring = spring({
    frame: frame - 35,
    fps,
    config: {damping: 15, stiffness: 100},
  });

  // 3. Bloco 1: "CONSIGO TER" (entra frame 9 ~ 0.3s)
  const bloco1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // 4. Bloco 2: "VÍDEOS MEUS" (entra frame 26 ~ 0.9s com fala "vídeos")
  const bloco2Spring = spring({
    frame: frame - 26,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 5. Bloco 3: "SEM PRECISAR SENTAR" (entra frame 48 ~ 1.6s)
  const bloco3Spring = spring({
    frame: frame - 48,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 6. Bloco 4: "NA FRENTE DA CÂMERA?" (entra frame 82 ~ 2.7s com fala "na frente")
  const bloco4Spring = spring({
    frame: frame - 82,
    fps,
    config: {damping: 11, stiffness: 150},
  });

  // 7. Selo de benefício oficial do briefing (entra frame 98 ~ 3.3s)
  const factSpring = spring({
    frame: frame - 98,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Flutuação contínua suave dos textos
  const floatY = Math.sin(frame / 12) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: CORES.fundoEscuro,
        overflow: 'hidden',
        fontFamily,
        opacity: sceneOpacity,
      }}
    >
      {/* Imagem de fundo com push-in */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
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
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(139, 92, 246, 0.18) 0%, rgba(11, 13, 20, 0.82) 55%, rgba(11, 13, 20, 0.98) 100%)',
          }}
        />
      </div>

      {/* Grid e grafismo tecnológico em movimento */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 540,
          width: 600,
          height: 600,
          borderRadius: '50%',
          border: '1.5px dashed rgba(139, 92, 246, 0.25)',
          transform: `translate(-50%, -50%) rotate(${frame * 0.4}deg)`,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 540,
          width: 440,
          height: 440,
          borderRadius: '50%',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          transform: `translate(-50%, -50%) rotate(${-frame * 0.25}deg)`,
          pointerEvents: 'none',
        }}
      />

      {/* TOPO: Safe zone y: 150 a 480 */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 20,
        }}
      >
        {/* Badge 1: DÚVIDA COMUM */}
        <div
          style={{
            opacity: Math.max(0, badgeSpring),
            transform: `translateY(${(1 - badgeSpring) * -20}px)`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 24px',
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            border: '1.5px solid rgba(139, 92, 246, 0.45)',
            borderRadius: 30,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: CORES.marca,
              boxShadow: `0 0 12px ${CORES.marca}`,
              transform: `scale(${1 + Math.sin(frame / 6) * 0.25})`,
            }}
          />
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            Dúvida Frequente
          </span>
        </div>

        {/* Gancho fixo (gancho_tela) */}
        {frame >= 35 && (
          <div
            style={{
              opacity: Math.max(0, ganchoSpring),
              transform: `scale(${Math.max(0.7, ganchoSpring)})`,
              padding: '8px 22px',
              backgroundColor: 'rgba(139, 92, 246, 0.22)',
              border: '1px solid rgba(139, 92, 246, 0.55)',
              borderRadius: 20,
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 700,
                color: CORES.marcaClara,
                letterSpacing: 0.5,
              }}
            >
              ⚡ Vídeos sem gravar câmera
            </span>
          </div>
        )}
      </div>

      {/* ÁREA CENTRAL FOCAL: y: 480 a 1280 */}
      <div
        style={{
          position: 'absolute',
          top: 470,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          gap: 18,
          transform: `translateY(${floatY}px)`,
          zIndex: 20,
        }}
      >
        {/* Bloco 1: CONSIGO TER */}
        <div
          style={{
            opacity: Math.max(0, bloco1Spring),
            transform: `translateY(${(1 - bloco1Spring) * 30}px) scale(${Math.max(0.8, bloco1Spring)})`,
          }}
        >
          <span
            style={{
              fontSize: 66,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
              textTransform: 'uppercase',
              textShadow: '0 4px 20px rgba(0, 0, 0, 0.9)',
            }}
          >
            Consigo ter
          </span>
        </div>

        {/* Bloco 2: VÍDEOS MEUS */}
        <div
          style={{
            opacity: Math.max(0, bloco2Spring),
            transform: `translateY(${(1 - bloco2Spring) * 35}px) scale(${Math.max(0.85, bloco2Spring)})`,
          }}
        >
          <span
            style={{
              fontSize: 88,
              fontWeight: 900,
              color: CORES.marca,
              letterSpacing: 1.5,
              textTransform: 'uppercase',
              textShadow: `0 0 40px rgba(139, 92, 246, 0.75), 0 4px 16px rgba(0,0,0,0.9)`,
            }}
          >
            Vídeos Meus
          </span>
        </div>

        {/* Bloco 3: SEM PRECISAR SENTAR */}
        {frame >= 48 && (
          <div
            style={{
              opacity: Math.max(0, bloco3Spring),
              transform: `translateY(${(1 - bloco3Spring) * 25}px)`,
            }}
          >
            <span
              style={{
                fontSize: 52,
                fontWeight: 800,
                color: '#E2E8F0',
                letterSpacing: 0.5,
                textTransform: 'uppercase',
                textShadow: '0 4px 16px rgba(0, 0, 0, 0.9)',
              }}
            >
              Sem precisar sentar
            </span>
          </div>
        )}

        {/* Bloco 4: NA FRENTE DA CÂMERA? */}
        {frame >= 82 && (
          <div
            style={{
              opacity: Math.max(0, bloco4Spring),
              transform: `translateY(${(1 - bloco4Spring) * 30}px) scale(${Math.max(0.88, bloco4Spring)})`,
              backgroundColor: CORES.marca,
              padding: '16px 36px',
              borderRadius: 22,
              boxShadow: '0 16px 45px rgba(139, 92, 246, 0.65)',
            }}
          >
            <span
              style={{
                fontSize: 68,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1,
                textTransform: 'uppercase',
                textShadow: '0 3px 10px rgba(0, 0, 0, 0.5)',
              }}
            >
              Na frente da câmera?
            </span>
          </div>
        )}

        {/* Bloco 5: Selo Oficial do Briefing */}
        {frame >= 98 && (
          <div
            style={{
              marginTop: 16,
              opacity: Math.max(0, factSpring),
              transform: `scale(${Math.max(0.8, factSpring)})`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 28px',
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              border: '1.5px solid rgba(139, 92, 246, 0.5)',
              borderRadius: 20,
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.7)',
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: '#10B981',
                boxShadow: '0 0 10px #10B981',
              }}
            />
            <span
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 0.5,
              }}
            >
              Avatar com IA da pessoa
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
