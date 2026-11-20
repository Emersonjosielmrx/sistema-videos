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
import {ChatIcon, CheckIcon, InstagramIcon, ShieldIcon} from './Icons';

interface Cena4Props {
  fontFamily: string;
}

export const Cena4: React.FC<Cena4Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração da cena 4: 25.02s a 28.97s = 3.95s (119 frames a 30 fps)
  // Zoom contínuo no fundo: 1.00 -> 1.10
  const bgScale = interpolate(frame, [0, 119], [1.0, 1.1], {
    extrapolateRight: 'clamp',
  });

  // Coreografia de Entrada em Cascata (Stagger):
  // 1. Escudo e Logo: descem com ease-out no frame 0
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.6, stiffness: 125},
  });

  // 2. Proposta de valor: desce aos ~0.15s (frame 4)
  const titleSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, mass: 0.6, stiffness: 125},
  });

  const tags = [
    'Docker + Portainer',
    'Traefik',
    'n8n Próprio',
    'Bot Sentinela',
    'Backup Automático',
  ];

  // 3. Os 5 pills de recursos surgem sequencialmente com pop individual de 4 frames de intervalo
  const pill0Spring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 140},
  });
  const pill1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 140},
  });
  const pill2Spring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 140},
  });
  const pill3Spring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 140},
  });
  const pill4Spring = spring({
    frame: frame - 24,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 140},
  });
  const pillSprings = [pill0Spring, pill1Spring, pill2Spring, pill3Spring, pill4Spring];

  // 4. Botão CTA: entra com scale-pop no frame 16 sincronizado com o comando de voz ("Chame a gente no direct")
  const ctaSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 12, mass: 0.65, stiffness: 135},
  });

  // Pulso contínuo e glow pulsante no botão CTA direcionando o clique
  const buttonPulse = interpolate(
    Math.sin((frame / 30) * Math.PI * 3.5),
    [-1, 1],
    [1.0, 1.05]
  );
  const buttonGlow = 25 + Math.sin(frame * 0.25) * 15;

  // Efeito contínuo de varredura de luz (shine sweep) cruzando o botão CTA
  const shimmerPos = interpolate(frame % 38, [0, 38], [-120, 240]);

  // 5. Arroba da marca: entra com slide-up elegante aos ~0.85s (frame 26)
  const arrobaSpring = spring({
    frame: frame - 26,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 130},
  });

  // Pulso sutil no logo
  const logoFloat = Math.sin((frame / 30) * Math.PI * 2) * 5;

  return (
    <AbsoluteFill style={{backgroundColor: '#0B1120'}}>
      {/* Imagem de Fundo com zoom e escurecimento */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.24) contrast(1.15)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(14, 165, 233, 0.25) 0%, rgba(11, 17, 32, 0.96) 75%)',
          }}
        />
        {/* Linhas tech de grade */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(14, 165, 233, 0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(14, 165, 233, 0.07) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
            opacity: 0.5,
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo Perfeitamente Distribuído na Safe Zone (y 175 a 1430, x 60 a 1020, rigorosamente acima de y=1520) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          bottom: 490,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontFamily,
          zIndex: 50,
          boxSizing: 'border-box',
        }}
      >
        {/* Bloco Superior: Logo + Nome + Proposta de Valor (y ~175 a 450) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              transform: `translateY(${logoFloat}px) scale(${logoSpring})`,
              opacity: logoSpring,
            }}
          >
            <div
              style={{
                width: 100,
                height: 100,
                borderRadius: 50,
                backgroundColor: 'rgba(14, 165, 233, 0.22)',
                border: '3px solid #0EA5E9',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 40px rgba(14, 165, 233, 0.7)',
                marginBottom: 16,
              }}
            >
              <ShieldIcon size={58} color="#38BDF8" />
            </div>
            <div
              style={{
                fontSize: 58,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
                textShadow:
                  '0 4px 20px rgba(0,0,0,0.9), 0 0 25px rgba(14, 165, 233, 0.6)',
              }}
            >
              VPS BLINDADA
            </div>
          </div>

          {/* Proposta de Valor Oficial dos Fatos */}
          <div
            style={{
              marginTop: 18,
              textAlign: 'center',
              maxWidth: 900,
              transform: `translateY(${(1 - titleSpring) * 15}px)`,
              opacity: titleSpring,
            }}
          >
            <div
              style={{
                fontSize: 40,
                fontWeight: 800,
                color: '#E2E8F0',
                lineHeight: 1.3,
                textShadow: '0 3px 12px rgba(0,0,0,0.85)',
              }}
            >
              Sua VPS{' '}
              <span style={{color: '#38BDF8', fontWeight: 900}}>pronta</span>,{' '}
              <span style={{color: '#34D399', fontWeight: 900}}>segura</span> e com{' '}
              <span style={{color: '#38BDF8', fontWeight: 900}}>backup</span>
            </div>
          </div>
        </div>

        {/* Bloco Central: Selos de Recursos com Entrada em Cascata (Stagger) */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: 22,
            maxWidth: 940,
          }}
        >
          {tags.map((tag, idx) => {
            const pSpring = pillSprings[idx];
            return (
              <div
                key={idx}
                style={{
                  padding: '20px 32px',
                  borderRadius: 24,
                  backgroundColor: 'rgba(15, 23, 42, 0.94)',
                  border: '2px solid rgba(14, 165, 233, 0.55)',
                  color: '#F8FAFC',
                  fontSize: 38,
                  fontWeight: 800,
                  boxShadow: '0 8px 24px rgba(0,0,0,0.65)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                  transform: `translateY(${(1 - pSpring) * 20}px) scale(${pSpring})`,
                  opacity: pSpring,
                }}
              >
                <CheckIcon size={32} color="#34D399" />
                <span>{tag}</span>
              </div>
            );
          })}
        </div>

        {/* Bloco Inferior: Botão CTA + @ da Conta (foco limpo de conversão, sem texto duplicado) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          {/* Botão CTA: Entrada escalonada com scale-pop no frame 16 sincronizado com o áudio,
              recebendo pulso de brilho (glow pulsante) e shine sweep contínuo */}
          <div
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'center',
              transform: `scale(${ctaSpring * buttonPulse})`,
              opacity: ctaSpring,
            }}
          >
            <div
              style={{
                position: 'relative',
                overflow: 'hidden',
                width: '100%',
                maxWidth: 860,
                padding: '24px 38px',
                borderRadius: 36,
                background: 'linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%)',
                boxShadow: `0 16px 45px rgba(14, 165, 233, 0.55), 0 0 ${buttonGlow}px rgba(14, 165, 233, 0.6)`,
                border: '2.5px solid rgba(255, 255, 255, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 20,
              }}
            >
              {/* Efeito contínuo de varredura de luz (shine sweep) que atrai o clique */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  width: 90,
                  left: `${shimmerPos}%`,
                  background:
                    'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent)',
                  transform: 'skewX(-25deg)',
                }}
              />
              <ChatIcon size={44} color="#FFFFFF" />
              <span
                style={{
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  letterSpacing: 2,
                  textTransform: 'uppercase',
                  textShadow: '0 2px 10px rgba(0,0,0,0.5)',
                }}
              >
                CHAME NO DIRECT
              </span>
            </div>
          </div>

          {/* Arroba Oficial da Marca - Posicionado com folga acima de y=1520 */}
          <div
            style={{
              marginTop: 18,
              transform: `scale(${arrobaSpring})`,
              opacity: arrobaSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 30px',
              borderRadius: 24,
              backgroundColor: 'rgba(15, 23, 42, 0.94)',
              border: '1.5px solid rgba(14, 165, 233, 0.5)',
              boxShadow: '0 8px 22px rgba(0,0,0,0.5)',
            }}
          >
            <InstagramIcon size={34} color="#38BDF8" />
            <span
              style={{
                fontSize: 36,
                fontWeight: 900,
                color: '#38BDF8',
                letterSpacing: 1,
              }}
            >
              @vpsblindada.ia
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
