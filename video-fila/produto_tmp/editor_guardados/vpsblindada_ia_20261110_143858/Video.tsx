import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';

const {fontFamily} = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  subsets: ['latin'],
});

const CORES = {
  marca: '#0EA5E9',
  marcaClara: '#38BDF8',
  marcaEscura: '#0284C7',
  apoio: '#111827',
  fundoEscuro: '#0B1120',
  destaque: '#0EA5E9',
  texto: '#FFFFFF',
  textoSec: '#E2E8F0',
  alerta: '#EF4444',
  verde: '#10B981',
  whatsVerde: '#005C4B',
  whatsEscuro: '#1F2C34',
};

const PALAVRAS: PalavraK[] = [
  // Cena 0
  {p: 'Um', ini: 0.318, fim: 0.445},
  {p: 'aplicativo', ini: 0.45, fim: 1.08},
  {p: 'que', ini: 1.087, fim: 1.2},
  {p: 'trava', ini: 1.208, fim: 1.515, quebraApos: true},
  {p: 'pode', ini: 1.52, fim: 1.78},
  {p: 'derrubar', ini: 1.784, fim: 2.29, quebraApos: true},
  {p: 'todo', ini: 2.301, fim: 2.56},
  {p: 'o', ini: 2.566, fim: 2.6},
  {p: 'meu', ini: 2.602, fim: 2.74},
  {p: 'negócio?', ini: 2.746, fim: 4.45, quebraApos: true},
  // Cena 1
  {p: 'Eu', ini: 4.46, fim: 4.92, quebraAntes: true},
  {p: 'temia', ini: 4.92, fim: 5.34},
  {p: 'que', ini: 5.34, fim: 5.48},
  {p: 'uma', ini: 5.48, fim: 5.78},
  {p: 'falha', ini: 5.78, fim: 6.34, quebraApos: true},
  {p: 'em', ini: 6.34, fim: 6.5},
  {p: 'um', ini: 6.5, fim: 6.7},
  {p: 'aplicativo', ini: 6.7, fim: 7.6, quebraApos: true},
  {p: 'travasse', ini: 7.6, fim: 8.46},
  {p: 'o', ini: 8.46, fim: 8.62},
  {p: 'resto', ini: 8.62, fim: 8.98, quebraApos: true},
  {p: 'dos', ini: 8.98, fim: 9.28},
  {p: 'meus', ini: 9.28, fim: 9.46},
  {p: 'serviços.', ini: 9.46, fim: 10.45, quebraApos: true},
  // Cena 2
  {p: 'A', ini: 10.95, fim: 11.12, quebraAntes: true},
  {p: 'estrutura', ini: 11.123, fim: 11.59},
  {p: 'entrega', ini: 11.595, fim: 11.91},
  {p: 'Docker', ini: 11.915, fim: 12.41},
  {p: 'e', ini: 12.415, fim: 12.475},
  {p: 'Portainer', ini: 12.48, fim: 12.93, quebraApos: true},
  {p: 'configurados', ini: 12.938, fim: 13.65},
  {p: 'para', ini: 13.659, fim: 13.845},
  {p: 'separar', ini: 13.852, fim: 14.37, quebraApos: true},
  {p: 'cada', ini: 14.38, fim: 14.64},
  {p: 'aplicação', ini: 14.645, fim: 15.25, quebraApos: true},
  {p: 'de', ini: 15.258, fim: 15.37},
  {p: 'forma', ini: 15.378, fim: 15.745},
  {p: 'independente.', ini: 15.751, fim: 17.45, quebraApos: true},
  // Cena 3
  {p: 'Agora', ini: 17.814, fim: 18.314, quebraAntes: true},
  {p: 'tenho', ini: 18.314, fim: 18.814},
  {p: 'minha', ini: 18.814, fim: 19.324},
  {p: 'VPS', ini: 19.324, fim: 19.824, quebraApos: true},
  {p: 'pronta', ini: 19.824, fim: 20.324},
  {p: 'e', ini: 20.324, fim: 20.824},
  {p: 'segura,', ini: 20.824, fim: 21.324, quebraApos: true},
  {p: 'com', ini: 21.324, fim: 21.834},
  {p: 'Docker,', ini: 21.834, fim: 22.334},
  {p: 'Portainer', ini: 22.334, fim: 22.834, quebraApos: true},
  {p: 'e', ini: 22.834, fim: 23.334},
  {p: 'backup', ini: 23.334, fim: 23.844},
  {p: 'automático', ini: 23.844, fim: 24.344, quebraApos: true},
  {p: 'funcionando.', ini: 24.344, fim: 25.12, quebraApos: true},
  // Cena 4
  {p: 'Chame', ini: 25.55, fim: 26.04, quebraAntes: true},
  {p: 'a', ini: 26.045, fim: 26.115},
  {p: 'gente', ini: 26.12, fim: 26.45},
  {p: 'no', ini: 26.455, fim: 26.56},
  {p: 'direct.', ini: 26.565, fim: 29.1, quebraApos: true},
];

// Ícones SVG limpos
const IconShield: React.FC<{size?: number; color?: string}> = ({
  size = 44,
  color = '#38BDF8',
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M12 2L4 5.5V11.5C4 16.8 7.4 21.6 12 23C16.6 21.6 20 16.8 20 11.5V5.5L12 2Z"
      fill={color}
      fillOpacity={0.22}
      stroke={color}
      strokeWidth={2.2}
    />
    <path
      d="M8.5 12.2L11 14.7L15.8 9.8"
      stroke="#FFFFFF"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const IconCube: React.FC<{size?: number; color?: string}> = ({
  size = 40,
  color = '#38BDF8',
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M21 16V8A2 2 0 0 0 20 6.27L13 2.27A2 2 0 0 0 11 2.27L4 6.27A2 2 0 0 0 3 8V16A2 2 0 0 0 4 17.73L11 21.73A2 2 0 0 0 13 21.73L20 17.73A2 2 0 0 0 21 16Z"
      fill={color}
      fillOpacity={0.2}
      stroke={color}
      strokeWidth={2.2}
    />
    <path
      d="M3.27 6.96L12 12.01L20.73 6.96M12 22.08V12"
      stroke={color}
      strokeWidth={2}
    />
  </svg>
);

const IconAlert: React.FC<{size?: number; color?: string}> = ({
  size = 40,
  color = '#EF4444',
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M10.29 3.86L1.82 18A2 2 0 0 0 3.54 21H20.46A2 2 0 0 0 22.18 18L13.71 3.86A2 2 0 0 0 10.29 3.86Z"
      fill={color}
      fillOpacity={0.24}
      stroke={color}
      strokeWidth={2.2}
    />
    <path
      d="M12 9V13M12 17H12.01"
      stroke="#FFFFFF"
      strokeWidth={2.6}
      strokeLinecap="round"
    />
  </svg>
);

// ============================================================================
// CENA 0: PERGUNTA (0.00s -> 4.81s | 145 frames)
// ============================================================================
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const bgScale = interpolate(frame, [0, 145], [1.02, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgX = interpolate(frame, [0, 145], [0, -35], {
    extrapolateRight: 'clamp',
  });
  const gridShift = (frame * 2.4) % 80;

  const popGancho = spring({frame, fps, config: {damping: 12, stiffness: 140}});
  const popLinha1 = spring({
    frame: frame - 4,
    fps,
    config: {damping: 13, stiffness: 150},
  });
  const popTrava = spring({
    frame: frame - Math.round(1.15 * fps),
    fps,
    config: {damping: 11, stiffness: 170},
  });
  const popDerrubar = spring({
    frame: frame - Math.round(1.72 * fps),
    fps,
    config: {damping: 12, stiffness: 160},
  });
  const popNegocio = spring({
    frame: frame - Math.round(2.45 * fps),
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // Transição do painel: aos 2.25s a blindagem ativa e o badge faz flip 3D suave
  const shieldActive = spring({
    frame: frame - Math.round(2.25 * fps),
    fps,
    config: {damping: 12, stiffness: 130},
  });
  const badgeFlip = spring({
    frame: frame - Math.round(2.25 * fps),
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const isIsolated = badgeFlip > 0.5;
  const badgeRotX = interpolate(badgeFlip, [0, 1], [0, 360]);

  const redPulse = Math.sin(frame * 0.38) * 8;
  const exitOpacity = interpolate(frame, [132, 145], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: exitOpacity, backgroundColor: CORES.fundoEscuro}}>
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translateX(${bgX}px)`,
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Grade cibernética em movimento para garantir >10% de variação visual */}
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(rgba(14, 165, 233, 0.16) 2px, transparent 2px), linear-gradient(90deg, rgba(14, 165, 233, 0.16) 2px, transparent 2px)`,
          backgroundSize: '80px 80px',
          backgroundPosition: `${gridShift}px ${gridShift}px`,
          opacity: 0.65,
        }}
      />

      {/* Feixe diagonal dinâmico */}
      <div
        style={{
          position: 'absolute',
          top: interpolate(frame, [0, 145], [-200, 900]),
          left: -150,
          width: 1400,
          height: 360,
          background:
            'linear-gradient(180deg, transparent, rgba(14,165,233,0.22), transparent)',
          transform: 'rotate(-14deg)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo seguro distribuído harmonicamente na tela */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 26,
        }}
      >
        {/* Selo Gancho */}
        <div
          style={{
            alignSelf: 'flex-start',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '12px 26px',
            borderRadius: 999,
            background: 'rgba(15, 23, 42, 0.94)',
            border: `2px solid ${CORES.marca}`,
            transform: `scale(${popGancho})`,
            boxShadow: '0 10px 30px rgba(14,165,233,0.35)',
          }}
        >
          <IconShield size={36} color={CORES.marcaClara} />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 0.6,
              textTransform: 'uppercase',
            }}
          >
            Sistemas isolados no servidor
          </span>
        </div>

        {/* Pergunta Cinética Principal: 100% legível e alto contraste desde o milissegundo 0 */}
        <div
          style={{
            background: 'rgba(11, 17, 32, 0.94)',
            borderRadius: 32,
            padding: '36px 38px',
            border: '2.5px solid rgba(56, 189, 248, 0.45)',
            boxShadow: '0 24px 50px rgba(0,0,0,0.7)',
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
          }}
        >
          {/* Linha 1: Um aplicativo que TRAVA */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 54,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
              }}
            >
              Um aplicativo que
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 54,
                fontWeight: 900,
                color: '#FFFFFF',
                background: t >= 1.15 ? CORES.alerta : 'rgba(239, 68, 68, 0.22)',
                border: `2.5px solid ${CORES.alerta}`,
                padding: '6px 22px',
                borderRadius: 16,
                transform: `scale(${t >= 1.15 ? 1 + popTrava * 0.08 : 1.0})`,
                boxShadow: t >= 1.15 ? '0 0 28px rgba(239, 68, 68, 0.8)' : '0 4px 14px rgba(0,0,0,0.4)',
                transition: 'background 0.2s',
              }}
            >
              TRAVA
            </span>
          </div>

          {/* Linha 2: pode DERRUBAR (alto contraste desde frame 0) */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 52,
                fontWeight: 800,
                color: '#FFFFFF',
                lineHeight: 1.15,
              }}
            >
              pode
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 54,
                fontWeight: 900,
                color: '#FFFFFF',
                background: t >= 1.72 ? CORES.alerta : 'rgba(239, 68, 68, 0.24)',
                border: `2.5px solid ${CORES.alerta}`,
                padding: '6px 22px',
                borderRadius: 16,
                transform: `scale(${t >= 1.72 ? 1 + popDerrubar * 0.08 : 1.0})`,
                boxShadow: t >= 1.72 ? '0 0 28px rgba(239, 68, 68, 0.8)' : '0 4px 14px rgba(0,0,0,0.4)',
              }}
            >
              DERRUBAR
            </span>
          </div>

          {/* Linha 3: todo o meu negócio? (alto contraste branco desde 0, vira ciano brilhante na fala) */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 54,
                fontWeight: 900,
                color: t >= 2.45 ? CORES.marcaClara : '#FFFFFF',
                lineHeight: 1.15,
                transform: `scale(${t >= 2.45 ? 1 + popNegocio * 0.05 : 1.0})`,
                textShadow: t >= 2.45 ? '0 0 26px rgba(56, 189, 248, 0.85)' : 'none',
              }}
            >
              todo o meu negócio?
            </span>
          </div>
        </div>

        {/* Diagrama Visual de Isolamento de Containers (y ~ 740 a 1280) */}
        <div
          style={{
            marginTop: 6,
            background: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 30,
            padding: '30px 28px',
            border: `2.5px solid ${shieldActive > 0.3 ? CORES.marca : 'rgba(239,68,68,0.7)'}`,
            boxShadow: '0 22px 48px rgba(0,0,0,0.65)',
            display: 'flex',
            flexDirection: 'column',
            gap: 22,
          }}
        >
          {/* Topo do Painel com transição suave (flip 3D) do badge */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              Painel da VPS
            </span>
            <div
              style={{
                padding: '10px 22px',
                borderRadius: 999,
                background:
                  isIsolated
                    ? 'rgba(14, 165, 233, 0.28)'
                    : 'rgba(239, 68, 68, 0.32)',
                border: `2px solid ${isIsolated ? CORES.marcaClara : CORES.alerta}`,
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                boxShadow: isIsolated
                  ? '0 0 22px rgba(14, 165, 233, 0.5)'
                  : '0 0 22px rgba(239, 68, 68, 0.5)',
                transform: `rotateX(${badgeRotX}deg)`,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              {isIsolated ? (
                <>
                  <IconShield size={28} color={CORES.marcaClara} />
                  <span>Ambientes Isolados</span>
                </>
              ) : (
                <>
                  <IconAlert size={28} color="#FCA5A5" />
                  <span>Falha Detectada</span>
                </>
              )}
            </div>
          </div>

          {/* Cards dos Ambientes: foco inicial no alerta/perigo antes de revelar a blindagem */}
          <div
            style={{
              display: 'flex',
              gap: 16,
              justifyContent: 'space-between',
              alignItems: 'stretch',
            }}
          >
            {/* Card 1: Aplicativo com falha isolado (com pulsação viva na borda vermelha) */}
            <div
              style={{
                flex: 1,
                background: 'rgba(239, 68, 68, 0.2)',
                border: `3px solid ${CORES.alerta}`,
                borderRadius: 22,
                padding: '22px 14px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 10,
                boxShadow: `0 0 ${12 + redPulse}px rgba(239, 68, 68, 0.85)`,
                transform: `translateY(${Math.sin(frame * 0.4) * 4}px) scale(${1 + Math.sin(frame * 0.35) * 0.02})`,
              }}
            >
              <IconAlert size={44} color={CORES.alerta} />
              <span
                style={{
                  fontFamily,
                  fontSize: 33,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textAlign: 'center',
                }}
              >
                App 01
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FCA5A5',
                }}
              >
                Travado
              </span>
            </div>

            {/* Barreira de Isolamento: surge aos 2.25s isolando a pane */}
            <div
              style={{
                width: 14,
                borderRadius: 999,
                background: shieldActive > 0.2 ? CORES.marca : 'rgba(239, 68, 68, 0.4)',
                boxShadow: shieldActive > 0.2 ? '0 0 26px #0EA5E9' : 'none',
                transform: `scaleY(${0.2 + shieldActive * 0.8})`,
                transition: 'background 0.3s',
              }}
            />

            {/* Card 2: Sistema Web (inicialmente em risco/alerta, protegido com a blindagem) */}
            <div
              style={{
                flex: 1,
                background:
                  shieldActive > 0.3
                    ? 'rgba(16, 185, 129, 0.18)'
                    : 'rgba(245, 158, 11, 0.16)',
                border: `3px solid ${shieldActive > 0.3 ? CORES.verde : 'rgba(245, 158, 11, 0.7)'}`,
                borderRadius: 22,
                padding: '22px 14px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 10,
                transform: `translateY(${Math.cos(frame * 0.25) * 4}px)`,
                boxShadow:
                  shieldActive > 0.3
                    ? '0 0 20px rgba(16, 185, 129, 0.4)'
                    : '0 0 16px rgba(245, 158, 11, 0.35)',
              }}
            >
              {shieldActive > 0.3 ? (
                <IconCube size={44} color={CORES.verde} />
              ) : (
                <IconAlert size={44} color="#F59E0B" />
              )}
              <span
                style={{
                  fontFamily,
                  fontSize: 33,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textAlign: 'center',
                }}
              >
                Sistema
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: shieldActive > 0.3 ? '#6EE7B7' : '#FCD34D',
                }}
              >
                {shieldActive > 0.3 ? 'Protegido' : 'Em risco?'}
              </span>
            </div>

            {/* Card 3: Automação / n8n (inicialmente em risco, online com a blindagem) */}
            <div
              style={{
                flex: 1,
                background:
                  shieldActive > 0.3
                    ? 'rgba(14, 165, 233, 0.18)'
                    : 'rgba(245, 158, 11, 0.16)',
                border: `3px solid ${shieldActive > 0.3 ? CORES.marcaClara : 'rgba(245, 158, 11, 0.7)'}`,
                borderRadius: 22,
                padding: '22px 14px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 10,
                transform: `translateY(${Math.sin(frame * 0.25 + 1.5) * 4}px)`,
                boxShadow:
                  shieldActive > 0.3
                    ? '0 0 20px rgba(56, 189, 248, 0.4)'
                    : '0 0 16px rgba(245, 158, 11, 0.35)',
              }}
            >
              {shieldActive > 0.3 ? (
                <IconShield size={44} color={CORES.marcaClara} />
              ) : (
                <IconAlert size={44} color="#F59E0B" />
              )}
              <span
                style={{
                  fontFamily,
                  fontSize: 33,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textAlign: 'center',
                }}
              >
                n8n / Site
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: shieldActive > 0.3 ? '#7DD3FC' : '#FCD34D',
                }}
              >
                {shieldActive > 0.3 ? 'Online' : 'Em risco?'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 1: DONO 1 - O PROBLEMA (4.46s -> 10.86s | 192 frames)
// ============================================================================
const Cena1DonoProblema: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tAbs = 4.46 + frame / fps;

  const enter = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const exit = interpolate(frame, [180, 192], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const videoScale = interpolate(frame, [0, 192], [1.0, 1.07], {
    extrapolateRight: 'clamp',
  });

  const showFalha = spring({
    frame: frame - Math.round((5.78 - 4.46) * fps),
    fps,
    config: {damping: 12, stiffness: 150},
  });
  const showResto = spring({
    frame: frame - Math.round((7.6 - 4.46) * fps),
    fps,
    config: {damping: 12, stiffness: 150},
  });

  return (
    <AbsoluteFill style={{opacity: enter * exit, backgroundColor: '#000'}}>
      <AbsoluteFill style={{transform: `scale(${videoScale})`}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Gradiente sutil apenas no topo e base para leitura perfeita sem cobrir o rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 450,
          background:
            'linear-gradient(180deg, rgba(11,17,32,0.85) 0%, rgba(11,17,32,0.45) 68%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* HUD Superior minimalista (y=168, bem acima do topo da cabeça do fundador) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            background: '#7F1D1D',
            border: `2px solid ${CORES.alerta}`,
            boxShadow: '0 8px 24px rgba(239, 68, 68, 0.4)',
          }}
        >
          <IconAlert size={34} color="#FCA5A5" />
          <span
            style={{
              fontFamily,
              fontSize: 33,
              fontWeight: 800,
              color: '#FFFFFF',
              textTransform: 'uppercase',
            }}
          >
            O problema
          </span>
        </div>

        <div
          style={{
            padding: '10px 22px',
            borderRadius: 999,
            background: 'rgba(15, 23, 42, 0.92)',
            border: '2px solid rgba(255,255,255,0.22)',
            fontFamily,
            fontSize: 32,
            fontWeight: 700,
            color: '#E2E8F0',
          }}
        >
          VPS Blindada
        </div>
      </div>

      {/* Indicador minimalista da dor em lower-third inferior, deixando o rosto e cabeça 100% livres */}
      {showFalha > 0.05 && (
        <div
          style={{
            position: 'absolute',
            bottom: 410,
            left: 60,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 14,
            padding: '12px 26px',
            borderRadius: 999,
            background: 'rgba(15, 23, 42, 0.94)',
            border: `2px solid ${CORES.alerta}`,
            boxShadow: '0 10px 28px rgba(0,0,0,0.6)',
            transform: `scale(${0.92 + showFalha * 0.08}) translateY(${(1 - showFalha) * 20}px)`,
            opacity: showFalha,
          }}
        >
          <IconAlert size={32} color={CORES.alerta} />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            Risco de falha em cadeia nos serviços
          </span>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 2: CONVERSA WHATSAPP + DOCKER/PORTAINER (10.51s -> 17.86s | 221 frames)
// ============================================================================
const Cena2Conversa: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tAbs = 10.51 + frame / fps;

  const enter = spring({frame, fps, config: {damping: 13, stiffness: 120}});
  const exit = interpolate(frame, [208, 221], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const bgScale = interpolate(frame, [0, 221], [1.14, 1.0], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(frame, [0, 221], [-25, 25], {
    extrapolateRight: 'clamp',
  });

  const rotY = interpolate(frame, [0, 110, 221], [-9, 4, -5]);
  const floatY = Math.sin(frame * 0.14) * 10;

  // Mensagens sincronizadas
  const msg1 = spring({
    frame: frame - 8,
    fps,
    config: {damping: 13, stiffness: 150},
  });
  const typingVisible = tAbs >= 11.2 && tAbs < 12.05;
  const msg2 = spring({
    frame: frame - Math.round((12.02 - 10.51) * fps),
    fps,
    config: {damping: 13, stiffness: 145},
  });
  const containersPop = spring({
    frame: frame - Math.round((13.85 - 10.51) * fps),
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const msg3 = spring({
    frame: frame - Math.round((15.4 - 10.51) * fps),
    fps,
    config: {damping: 13, stiffness: 145},
  });

  return (
    <AbsoluteFill
      style={{opacity: enter * exit, backgroundColor: CORES.fundoEscuro}}
    >
      <AbsoluteFill
        style={{transform: `scale(${bgScale}) translateY(${bgY}px)`}}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Círculos luminosos em movimento no fundo */}
      <div
        style={{
          position: 'absolute',
          top: 260 + Math.sin(frame * 0.08) * 60,
          right: -80,
          width: 480,
          height: 480,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(14,165,233,0.35), transparent 70%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
        }}
      >
        {/* Cabeçalho da Cena 2 */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 24px',
              borderRadius: 999,
              background: CORES.marcaEscura,
              border: `2px solid ${CORES.marcaClara}`,
            }}
          >
            <IconCube size={34} color="#FFFFFF" />
            <span
              style={{
                fontFamily,
                fontSize: 33,
                fontWeight: 800,
                color: '#FFFFFF',
                textTransform: 'uppercase',
              }}
            >
              Como funciona
            </span>
          </div>

          <div
            style={{
              padding: '10px 22px',
              borderRadius: 999,
              background: 'rgba(15, 23, 42, 0.92)',
              border: '2px solid rgba(148, 163, 184, 0.45)',
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#E2E8F0',
            }}
          >
            Simulação
          </div>
        </div>

        {/* Mockup de Celular 3D Grande (x=60..1020, y=245..1310) */}
        <div
          style={{
            perspective: 1200,
          }}
        >
          <div
            style={{
              background: '#0B141A',
              borderRadius: 38,
              border: '4px solid #334155',
              boxShadow: '0 28px 60px rgba(0,0,0,0.75)',
              overflow: 'hidden',
              transform: `rotateY(${rotY}deg) translateY(${floatY}px)`,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Barra Topo do App */}
            <div
              style={{
                background: CORES.whatsEscuro,
                padding: '18px 26px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '2px solid rgba(255,255,255,0.08)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 54,
                    height: 54,
                    borderRadius: '50%',
                    background: CORES.marca,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <IconShield size={34} color="#FFFFFF" />
                </div>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 35,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    VPS Blindada
                  </span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#38BDF8',
                    }}
                  >
                    Docker + Portainer
                  </span>
                </div>
              </div>
            </div>

            {/* Corpo da Conversa */}
            <div
              style={{
                padding: '22px 24px',
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
              }}
            >
              {/* Msg 1: Cliente (Direita, verde) */}
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  background: CORES.whatsVerde,
                  padding: '16px 22px',
                  borderRadius: '24px 24px 6px 24px',
                  transform: `scale(${msg1}) translateY(${(1 - msg1) * 20}px)`,
                  opacity: msg1,
                  boxShadow: '0 8px 20px rgba(0,0,0,0.35)',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.24,
                  }}
                >
                  Como ficam organizados meus sistemas na VPS?
                </span>
              </div>

              {/* Indicador digitando... */}
              {typingVisible && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    background: CORES.whatsEscuro,
                    padding: '12px 22px',
                    borderRadius: 20,
                    border: `2px solid ${CORES.marca}`,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: CORES.marcaClara,
                    }}
                  >
                    digitando...
                  </span>
                </div>
              )}

              {/* Msg 2: Empresa (Esquerda) */}
              {tAbs >= 12.0 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '92%',
                    background: CORES.whatsEscuro,
                    borderLeft: `6px solid ${CORES.marca}`,
                    padding: '16px 22px',
                    borderRadius: '24px 24px 24px 6px',
                    transform: `scale(${msg2}) translateY(${(1 - msg2) * 20}px)`,
                    opacity: msg2,
                    boxShadow: '0 8px 20px rgba(0,0,0,0.35)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.24,
                    }}
                  >
                    Com <strong style={{color: CORES.marcaClara}}>Docker e Portainer</strong> configurados, cada aplicação roda em seu próprio ambiente isolado.
                  </span>
                </div>
              )}

              {/* Painel visual de Containers Independentes sincronizado com "separar cada aplicação" */}
              {tAbs >= 13.7 && (
                <div
                  style={{
                    display: 'flex',
                    gap: 12,
                    justifyContent: 'space-between',
                    transform: `scale(${containersPop})`,
                    opacity: containersPop,
                  }}
                >
                  {['App 01', 'App 02', 'App 03'].map((nome, idx) => (
                    <div
                      key={nome}
                      style={{
                        flex: 1,
                        background: 'rgba(14, 165, 233, 0.18)',
                        border: `2px solid ${CORES.marcaClara}`,
                        borderRadius: 16,
                        padding: '10px 12px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                        transform: `translateY(${Math.sin(frame * 0.25 + idx) * 4}px)`,
                      }}
                    >
                      <IconCube size={32} color={CORES.marcaClara} />
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 800,
                          color: '#FFFFFF',
                        }}
                      >
                        {nome}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Msg 3: Cliente (Direita, verde) */}
              {tAbs >= 15.35 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '88%',
                    background: CORES.whatsVerde,
                    padding: '16px 22px',
                    borderRadius: '24px 24px 6px 24px',
                    transform: `scale(${msg3}) translateY(${(1 - msg3) * 20}px)`,
                    opacity: msg3,
                    boxShadow: '0 8px 20px rgba(0,0,0,0.35)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.24,
                    }}
                  >
                    Entendi, fica muito mais organizado para gerenciar.
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 3: DONO 3 - O RESULTADO (17.51s -> 25.54s | 241 frames)
// ============================================================================
const Cena3DonoResultado: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const enter = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const exit = interpolate(frame, [226, 241], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Punch-in dinâmico (+14% inicial com slow push-in até 1.22) para variedade de enquadramento frente à Cena 1
  const videoScale = interpolate(frame, [0, 241], [1.14, 1.22], {
    extrapolateRight: 'clamp',
  });
  const videoY = interpolate(frame, [0, 241], [18, 28], {
    extrapolateRight: 'clamp',
  });

  // Acendimento sincronizado com cada serviço mencionado na locução:
  // "VPS pronta e segura" (~19.5s), "Docker, Portainer" (~21.8s), "backup automático" (~23.3s)
  const item1 = spring({
    frame: frame - Math.round((19.5 - 17.51) * fps),
    fps,
    config: {damping: 9, stiffness: 170},
  });
  const item2 = spring({
    frame: frame - Math.round((21.75 - 17.51) * fps),
    fps,
    config: {damping: 9, stiffness: 170},
  });
  const item3 = spring({
    frame: frame - Math.round((23.25 - 17.51) * fps),
    fps,
    config: {damping: 9, stiffness: 170},
  });

  return (
    <AbsoluteFill style={{opacity: enter * exit, backgroundColor: '#000'}}>
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale}) translateY(${videoY}px)`,
          transformOrigin: '50% 42%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Véu escuro suave só no topo para destacar os selos sem cobrir o rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 430,
          background:
            'linear-gradient(180deg, rgba(11,17,32,0.88) 0%, rgba(11,17,32,0.48) 70%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* HUD Superior em y=166..395 (rosto livre abaixo de y=420) */}
      <div
        style={{
          position: 'absolute',
          top: 166,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 24px',
              borderRadius: 999,
              background: '#065F46',
              border: `2px solid ${CORES.verde}`,
            }}
          >
            <IconShield size={34} color="#6EE7B7" />
            <span
              style={{
                fontFamily,
                fontSize: 33,
                fontWeight: 800,
                color: '#FFFFFF',
                textTransform: 'uppercase',
              }}
            >
              O resultado
            </span>
          </div>

          <div
            style={{
              padding: '10px 22px',
              borderRadius: 999,
              background: 'rgba(15, 23, 42, 0.92)',
              border: `2px solid ${CORES.marca}`,
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: CORES.marcaClara,
            }}
          >
            Estrutura Ativa
          </div>
        </div>

        {/* 3 pílulas de checklist que iniciam desmarcadas e disparam pop + brilho verde ao serem faladas */}
        <div
          style={{
            display: 'flex',
            gap: 12,
            justifyContent: 'space-between',
          }}
        >
          {[
            {txt: 'VPS Segura', prog: item1},
            {txt: 'Docker + Portainer', prog: item2},
            {txt: 'Backup Ativo', prog: item3},
          ].map((it, idx) => {
            const aceso = it.prog > 0.1;
            const popScale = aceso
              ? interpolate(it.prog, [0, 0.6, 1], [0.92, 1.07, 1.0], {
                  extrapolateRight: 'clamp',
                })
              : 0.94;
            return (
              <div
                key={it.txt}
                style={{
                  flex: idx === 1 ? 1.38 : 1,
                  background: aceso
                    ? 'rgba(6, 78, 59, 0.92)'
                    : 'rgba(15, 23, 42, 0.65)',
                  border: `2.5px solid ${aceso ? '#34D399' : 'rgba(148,163,184,0.3)'}`,
                  borderRadius: 20,
                  padding: '15px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 10,
                  opacity: aceso ? 1 : 0.62,
                  transform: `scale(${popScale}) translateY(${Math.sin(frame * 0.22 + idx) * 3}px)`,
                  boxShadow: aceso
                    ? '0 0 28px rgba(16, 185, 129, 0.65)'
                    : 'none',
                }}
              >
                <div
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: '50%',
                    background: aceso ? CORES.verde : 'transparent',
                    border: `2.5px solid ${aceso ? '#A7F3D0' : '#64748B'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transform: `scale(${aceso ? 0.8 + it.prog * 0.2 : 0.9})`,
                  }}
                >
                  {aceso && (
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 900,
                        color: '#FFFFFF',
                        lineHeight: 1,
                      }}
                    >
                      ✓
                    </span>
                  )}
                </div>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: aceso ? '#FFFFFF' : '#CBD5E1',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {it.txt}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 4: CARTÃO FINAL / CTA (25.19s -> 29.14s | 119 frames)
// ============================================================================
const Cena4CartaoFinal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const enter = spring({frame, fps, config: {damping: 12, stiffness: 120}});
  const bgScale = interpolate(frame, [0, 119], [1.0, 1.22], {
    extrapolateRight: 'clamp',
  });
  const ringRot = frame * 2.6;
  // Pulso contínuo em loop (scale 1.0 -> 1.05) + shimmer sweep constante
  const btnPulse = 1 + Math.sin(frame * 0.34) * 0.045;
  const shimmerX = interpolate((frame * 22) % 1200, [0, 1200], [-320, 1080]);
  const scannerY = interpolate((frame * 14) % 1400, [0, 1400], [180, 1520]);

  // Entrada escalonada (stagger) dos 3 itens do checklist ao longo da Cena 4
  const check1 = spring({
    frame: frame - 6,
    fps,
    config: {damping: 11, stiffness: 150},
  });
  const check2 = spring({
    frame: frame - 22,
    fps,
    config: {damping: 11, stiffness: 150},
  });
  const check3 = spring({
    frame: frame - 38,
    fps,
    config: {damping: 11, stiffness: 150},
  });
  const checkSprings = [check1, check2, check3];

  // Destaque cíclico nos itens após a entrada para manter movimento vivo entre q13, q14 e q15
  const activeCheckIdx = Math.floor(frame / 24) % 3;

  return (
    <AbsoluteFill
      style={{opacity: enter, backgroundColor: CORES.fundoEscuro}}
    >
      <AbsoluteFill style={{transform: `scale(${bgScale})`}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(8px) brightness(0.62)',
          }}
        />
      </AbsoluteFill>

      {/* Feixe luminoso vertical varrendo o fundo continuamente */}
      <div
        style={{
          position: 'absolute',
          top: scannerY,
          left: 0,
          right: 0,
          height: 220,
          background:
            'linear-gradient(180deg, transparent, rgba(56, 189, 248, 0.22), transparent)',
          pointerEvents: 'none',
        }}
      />

      {/* Anel tecnológico girando continuamente */}
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: 160,
          width: 760,
          height: 760,
          borderRadius: '50%',
          border: '3px dashed rgba(56, 189, 248, 0.38)',
          transform: `rotate(${ringRot}deg)`,
          pointerEvents: 'none',
        }}
      />

      {/* Conjunto distribuído e centralizado na área útil (y=190..1390, com legenda karaokê logo abaixo em y=1440..1570) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 64,
          right: 64,
          height: 1190,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Bloco Marca e Proposta com maior escala e preenchimento harmônico */}
        <div
          style={{
            width: '100%',
            background: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 40,
            padding: '44px 38px',
            border: `3px solid ${CORES.marca}`,
            boxShadow: '0 28px 65px rgba(0,0,0,0.75)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24,
            transform: `translateY(${Math.sin(frame * 0.2) * 8}px)`,
          }}
        >
          <div
            style={{
              width: 116,
              height: 116,
              borderRadius: 32,
              background: 'rgba(14, 165, 233, 0.24)',
              border: `3px solid ${CORES.marcaClara}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transform: `scale(${1 + Math.sin(frame * 0.25) * 0.05})`,
              boxShadow: '0 0 30px rgba(56, 189, 248, 0.4)',
            }}
          >
            <IconShield size={72} color={CORES.marcaClara} />
          </div>

          <span
            style={{
              fontFamily,
              fontSize: 68,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
              textAlign: 'center',
              lineHeight: 1.08,
            }}
          >
            VPS BLINDADA
          </span>

          <span
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 700,
              color: '#E2E8F0',
              textAlign: 'center',
              lineHeight: 1.25,
            }}
          >
            Sua VPS pronta, segura e com backup
          </span>

          {/* Checklist de fatos permitidos com entrada escalonada (stagger) e destaque vivo */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              width: '100%',
              gap: 18,
              marginTop: 8,
            }}
          >
            {[
              'Setup Docker + Portainer + Traefik',
              'n8n próprio e Backup automático',
              'Bot Sentinela vigiando os erros',
            ].map((fato, idx) => {
              const sp = checkSprings[idx];
              const isHighlighted = activeCheckIdx === idx;
              return (
                <div
                  key={fato}
                  style={{
                    padding: '22px 26px',
                    borderRadius: 22,
                    background: isHighlighted
                      ? 'rgba(14, 165, 233, 0.34)'
                      : 'rgba(14, 165, 233, 0.2)',
                    border: `2.5px solid ${isHighlighted ? '#FFFFFF' : CORES.marcaClara}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 16,
                    opacity: sp,
                    transform: `translateY(${(1 - sp) * 36}px) translateX(${Math.sin(frame * 0.26 + idx * 1.4) * 8}px) scale(${0.9 + sp * 0.1 + (isHighlighted ? 0.025 : 0)})`,
                    boxShadow: isHighlighted
                      ? '0 10px 28px rgba(14, 165, 233, 0.45)'
                      : 'none',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 36,
                      fontWeight: 900,
                      color: '#6EE7B7',
                    }}
                  >
                    ✓
                  </span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 35,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    {fato}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bloco CTA e @handle ocupando a faixa médio-inferior com respiro antes da legenda */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24,
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              width: '100%',
              padding: '32px 38px',
              borderRadius: 999,
              background: `linear-gradient(90deg, ${CORES.marcaEscura}, ${CORES.marca}, ${CORES.marcaClara})`,
              border: '3.5px solid #FFFFFF',
              boxShadow: '0 22px 55px rgba(14, 165, 233, 0.65)',
              transform: `scale(${btnPulse})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 18,
            }}
          >
            {/* Brilho contínuo (shimmer sweep) cruzando o botão */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shimmerX,
                width: 240,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.65), transparent)',
                transform: 'skewX(-20deg)',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 52,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1.2,
                textTransform: 'uppercase',
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>

          <div
            style={{
              padding: '16px 38px',
              borderRadius: 999,
              background: 'rgba(15, 23, 42, 0.95)',
              border: `2.5px solid ${CORES.marcaClara}`,
              fontFamily,
              fontSize: 40,
              fontWeight: 800,
              color: '#FFFFFF',
              transform: `scale(${1 + Math.cos(frame * 0.24) * 0.025})`,
            }}
          >
            @vpsblindada.ia
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// COMPOSIÇÃO PRINCIPAL
// ============================================================================
const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  const progresso = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateRight: 'clamp',
  });

  const volumeTrilha = interpolate(
    frame,
    [0, 15, durationInFrames - 30, durationInFrames],
    [0, 0.1, 0.1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundoEscuro, fontFamily}}>
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volumeTrilha} />

      {/* CENA 0: 0.00s -> 4.81s */}
      <Sequence from={0} durationInFrames={145}>
        <Cena0Pergunta />
      </Sequence>

      {/* CENA 1: 4.46s -> 10.86s */}
      <Sequence from={Math.round(4.46 * 30)} durationInFrames={192}>
        <Cena1DonoProblema />
      </Sequence>

      {/* CENA 2: 10.51s -> 17.86s */}
      <Sequence from={Math.round(10.51 * 30)} durationInFrames={221}>
        <Cena2Conversa />
      </Sequence>

      {/* CENA 3: 17.51s -> 25.54s */}
      <Sequence from={Math.round(17.51 * 30)} durationInFrames={241}>
        <Cena3DonoResultado />
      </Sequence>

      {/* CENA 4: 25.19s -> 29.14s */}
      <Sequence from={Math.round(25.19 * 30)} durationInFrames={119}>
        <Cena4CartaoFinal />
      </Sequence>

      {/* Barra de Progresso dentro da Safe Zone (y=152, x=60..1020) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 8,
          borderRadius: 999,
          background: 'rgba(255, 255, 255, 0.2)',
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            background: CORES.marcaClara,
            borderRadius: 999,
          }}
        />
      </div>

      {/* Legenda Karaokê sincronizada em todas as cenas, incluindo a fala final */}
      <Karaoke
        palavras={PALAVRAS}
        fontFamily={fontFamily}
        destaque={CORES.marca}
        textoDestaque="#FFFFFF"
        tamanho={44}
        base={345}
        maxLetras={40}
      />
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={VideoPrincipal}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(29.14 * 30)}
    />
  );
};
