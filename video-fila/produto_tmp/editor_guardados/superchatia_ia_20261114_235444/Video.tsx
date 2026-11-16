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
import briefing from '../../../trabalhos/superchatia_ia_20261114_235444/public/briefing.json';

const {fontFamily} = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  subsets: ['latin'],
});

const COR_MARCA = '#5B6CFF';
const COR_ESCURA = '#111827';
const COR_WHATS = '#16A34A';
const COR_INSTA = '#DB2777';
const COR_TELE = '#0284C7';

const DURACAO_S = briefing.duracao_s;
const FPS = 30;
const TOTAL_FRAMES = Math.ceil(DURACAO_S * FPS);

const IconWhats: React.FC<{size?: number}> = ({size = 38}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.37 5.07L2 22l5.09-1.34C8.54 21.5 10.21 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2z"
      fill="#FFFFFF"
      fillOpacity={0.22}
    />
    <path
      d="M16.6 14.2c-.2-.1-1.3-.6-1.5-.7-.2-.1-.3-.1-.5.1-.1.2-.6.7-.7.8-.1.1-.3.2-.5.1-.9-.4-1.7-1-2.3-1.9-.2-.2 0-.4.1-.5.1-.1.2-.3.3-.4.1-.1.1-.2.2-.4.1-.1 0-.3 0-.4-.1-.1-.5-1.2-.7-1.6-.2-.4-.4-.3-.5-.3h-.4c-.2 0-.4.1-.6.3-.2.2-.8.8-.8 1.9s.8 2.2.9 2.4c.1.2 1.6 2.5 4 3.4 1.5.6 2.1.6 2.8.5.5-.1 1.3-.5 1.5-1.1.2-.5.2-1 .1-1.1-.1-.1-.2-.2-.4-.3z"
      fill="#FFFFFF"
    />
  </svg>
);

const IconInsta: React.FC<{size?: number}> = ({size = 38}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <rect
      x="3"
      y="3"
      width="18"
      height="18"
      rx="5"
      stroke="#FFFFFF"
      strokeWidth="2.5"
    />
    <circle cx="12" cy="12" r="4" stroke="#FFFFFF" strokeWidth="2.5" />
    <circle cx="17.5" cy="6.5" r="1.5" fill="#FFFFFF" />
  </svg>
);

const IconTele: React.FC<{size?: number}> = ({size = 38}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M21.2 4.4L2.9 11.5c-1.2.5-1.2 1.2-.2 1.5l4.7 1.5 10.8-6.8c.5-.3 1-.1.6.2l-8.8 7.9-.3 4.8c.5 0 .7-.2 1-.5l2.3-2.2 4.8 3.5c.9.5 1.5.2 1.7-.8L22.6 5.7c.3-1.2-.5-1.8-1.4-1.3z"
      fill="#FFFFFF"
    />
  </svg>
);

const IconCheck: React.FC<{size?: number; color?: string}> = ({
  size = 34,
  color = '#FFFFFF',
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="11" fill={color} fillOpacity={0.22} />
    <path
      d="M7 12.5l3.2 3.2L17.5 8.5"
      stroke={color}
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

// CENA 0: 0.00s a 5.89s — Vídeo vivo em movimento + Pergunta completa no topo ('Cansado de trocar de tela para responder WhatsApp, Instagram e Telegram?') + Notificações urgentes acumulando em cascata
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const durFrames = Math.round(5.89 * fps);
  // Push-in contínuo (1.00 -> 1.12) + pan dinâmico sobre vídeo real em movimento (nunca foto congelada)
  const zoom = interpolate(frame, [0, durFrames], [1.0, 1.12], {
    extrapolateRight: 'clamp',
  });
  const panX = interpolate(frame, [0, durFrames], [-16, 26], {
    extrapolateRight: 'clamp',
  });
  const panY = interpolate(frame, [0, durFrames], [0, -18], {
    extrapolateRight: 'clamp',
  });

  // Transição de saída suave com whip-slide para a esquerda
  const fadeOut = interpolate(t, [5.45, 5.86], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitSlideX = interpolate(t, [5.45, 5.86], [0, -120], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const popGancho = spring({
    frame: Math.max(0, frame - 1),
    fps,
    config: {damping: 12, stiffness: 180},
  });

  const popPergunta = spring({
    frame: Math.max(0, frame - 3),
    fps,
    config: {damping: 12, stiffness: 165},
  });

  const popTrocar = spring({
    frame: Math.max(0, frame - Math.round(0.9 * fps)),
    fps,
    config: {damping: 10, stiffness: 195},
  });

  const canais = [
    {
      nome: 'WhatsApp',
      cor: COR_WHATS,
      iniFala: 2.54,
      icon: <IconWhats size={42} />,
      alerta: 'Cliente aguardando resposta',
      tag: 'Celular 1',
    },
    {
      nome: 'Instagram',
      cor: COR_INSTA,
      iniFala: 3.28,
      icon: <IconInsta size={42} />,
      alerta: 'Direct pendente na fila',
      tag: 'Aba 2',
    },
    {
      nome: 'Telegram',
      cor: COR_TELE,
      iniFala: 3.9,
      icon: <IconTele size={42} />,
      alerta: 'Mensagem não lida no chat',
      tag: 'Tela 3',
    },
  ];

  const floatY = Math.sin(frame * 0.18) * 6;
  const pulseScale = 1 + Math.sin(frame * 0.24) * 0.028;
  const alertaFreneticoIdx = Math.floor(frame / 6) % 3;

  return (
    <AbsoluteFill
      style={{
        opacity: fadeOut,
        transform: `translateX(${exitSlideX}px)`,
      }}
    >
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('video_2.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${zoom}) translate(${panX}px, ${panY}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Vinheta dramática com alerta de urgência nos primeiros segundos preservando a pessoa à direita */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.90) 0%, rgba(17,24,39,0.40) 38%, rgba(17,24,39,0.22) 64%, rgba(17,24,39,0.88) 100%)',
        }}
      />

      {/* TOPO: Pílula de Gancho + Pergunta Completa com os 3 Canais para quem assiste sem áudio (y=168..475) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          gap: 14,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            width: '100%',
          }}
        >
          <div
            style={{
              transform: `scale(${popGancho * pulseScale})`,
              transformOrigin: 'left center',
              background: COR_MARCA,
              color: '#FFFFFF',
              padding: '10px 24px',
              borderRadius: 999,
              fontSize: 33,
              fontWeight: 800,
              whiteSpace: 'nowrap',
              boxShadow: '0 10px 28px rgba(91,108,255,0.45)',
            }}
          >
            TRÊS CANAIS NO MESMO PAINEL
          </div>

          <div
            style={{
              background: '#DC2626',
              color: '#FFFFFF',
              padding: '10px 22px',
              borderRadius: 999,
              fontSize: 32,
              fontWeight: 900,
              whiteSpace: 'nowrap',
              border: '2px solid #FCA5A5',
              transform: `scale(${1 + Math.sin(frame * 0.36) * 0.05})`,
              boxShadow: '0 8px 24px rgba(220,38,38,0.55)',
            }}
          >
            3 TELAS ABERTAS
          </div>
        </div>

        {/* Cartão superior com a dor completa: WhatsApp, Instagram e Telegram explícitos desde o início */}
        <div
          style={{
            width: '100%',
            background: 'rgba(17, 24, 39, 0.95)',
            border: `3px solid ${t >= 0.85 ? '#EF4444' : COR_MARCA}`,
            borderRadius: 28,
            padding: '20px 26px',
            boxShadow: '0 18px 42px rgba(0,0,0,0.62)',
            transform: `translateY(${(1 - popPergunta) * 28 + floatY * 0.35}px) scale(${0.95 + 0.05 * popPergunta})`,
            opacity: popPergunta,
          }}
        >
          <div
            style={{
              fontSize: 42,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.18,
            }}
          >
            Cansado de{' '}
            <span
              style={{
                display: 'inline-block',
                background: '#DC2626',
                color: '#FFFFFF',
                padding: '2px 14px',
                borderRadius: 12,
                transform: `scale(${0.92 + 0.08 * popTrocar})`,
              }}
            >
              trocar de tela
            </span>{' '}
            entre{' '}
            <span style={{color: '#4ADE80', textDecoration: t >= 2.5 ? 'underline' : 'none'}}>
              WhatsApp
            </span>
            ,{' '}
            <span style={{color: '#F472B6', textDecoration: t >= 3.25 ? 'underline' : 'none'}}>
              Instagram
            </span>{' '}
            e{' '}
            <span style={{color: '#38BDF8', textDecoration: t >= 3.88 ? 'underline' : 'none'}}>
              Telegram
            </span>
            ?
          </div>
        </div>
      </div>

      {/* CENTRO-ESQUERDA (y=800..1295): Notificações urgentes empilhando na lateral sem cobrir a pessoa à direita */}
      <div
        style={{
          position: 'absolute',
          top: 800,
          left: 60,
          width: 650,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        {canais.map((c, idx) => {
          const staggerFrame = 4 + idx * 5;
          const sEntrada = spring({
            frame: Math.max(0, frame - staggerFrame),
            fps,
            config: {damping: 10, stiffness: 175, mass: 0.85},
          });

          const frameFala = Math.round(c.iniFala * fps);
          const sFala = spring({
            frame: Math.max(0, frame - frameFala),
            fps,
            config: {damping: 9, stiffness: 190, mass: 0.8},
          });

          const citado = frame >= frameFala - 2;
          const emFocoConflito = !citado && alertaFreneticoIdx === idx;
          const ativoFala = t >= c.iniFala && t < c.iniFala + 0.95;
          const destaqueCard = citado || emFocoConflito;

          const slideEntradaX = (1 - sEntrada) * -240;
          const bounceFalaX = citado ? (1 - sFala) * 45 : 0;
          const oscX = Math.sin((frame + idx * 9) * 0.24) * 7;
          const scaleCard =
            (0.86 + 0.14 * sEntrada) *
            (ativoFala ? 1.05 : emFocoConflito ? 1.03 : 1.0);

          return (
            <div
              key={c.nome}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: citado
                  ? 'rgba(17, 24, 39, 0.96)'
                  : emFocoConflito
                    ? 'rgba(30, 41, 59, 0.95)'
                    : 'rgba(17, 24, 39, 0.90)',
                borderLeft: `14px solid ${c.cor}`,
                borderTop: `3px solid ${ativoFala || emFocoConflito ? '#FFFFFF' : 'rgba(255,255,255,0.28)'}`,
                borderRight: `3px solid ${ativoFala || emFocoConflito ? '#FFFFFF' : 'rgba(255,255,255,0.28)'}`,
                borderBottom: `3px solid ${ativoFala || emFocoConflito ? '#FFFFFF' : 'rgba(255,255,255,0.28)'}`,
                borderRadius: 22,
                padding: '14px 22px',
                transform: `translateX(${slideEntradaX + bounceFalaX + oscX}px) scale(${scaleCard})`,
                opacity: Math.min(1, sEntrada * 1.25),
                boxShadow: destaqueCard
                  ? '0 18px 36px rgba(0,0,0,0.62)'
                  : '0 10px 24px rgba(0,0,0,0.42)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: 16,
                    background: c.cor,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {c.icon}
                </div>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span
                    style={{
                      fontSize: 38,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      lineHeight: 1.1,
                    }}
                  >
                    {c.nome}
                  </span>
                  <span
                    style={{
                      fontSize: 32,
                      fontWeight: 700,
                      color: citado ? '#FFFFFF' : '#CBD5E1',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {c.alerta}
                  </span>
                </div>
              </div>
              <div
                style={{
                  background: citado
                    ? c.cor
                    : emFocoConflito
                      ? '#DC2626'
                      : 'rgba(255,255,255,0.16)',
                  color: '#FFFFFF',
                  padding: '8px 18px',
                  borderRadius: 999,
                  fontSize: 32,
                  fontWeight: 800,
                  whiteSpace: 'nowrap',
                }}
              >
                {c.tag}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// CENA 1: 5.54s a 13.72s — Dono falando (dono_1.mp4) com punch-in sincronizado em 'Hoje recebo' + Antes x Hoje no topo (y=168..420)
const Cena1Dono: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const iniS = 5.54;
  const durS = 13.72 - 5.54;
  const durFrames = Math.round(durS * fps);
  const tAbs = iniS + frame / fps;

  const sEntradaCena = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 170},
  });
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(tAbs, [13.32, 13.7], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const slideTransitionX = (1 - sEntradaCena) * 90;

  const chegouHoje = tAbs >= 8.98;
  // Punch-in digital de aproximação (1.0x -> 1.15x) sincronizado exatamente em 'Hoje recebo' (8.98s)
  const zoomBase = interpolate(frame, [0, durFrames], [1.0, 1.04], {
    extrapolateRight: 'clamp',
  });
  const punchInHoje = chegouHoje ? 1.14 : 1.0;
  const panYHoje = chegouHoje ? 55 : 0;

  const popAntes = spring({
    frame: Math.max(0, Math.round((tAbs - 5.84) * fps)),
    fps,
    config: {damping: 13, stiffness: 160},
  });

  const popHoje = spring({
    frame: Math.max(0, Math.round((tAbs - 8.98) * fps)),
    fps,
    config: {damping: 12, stiffness: 170},
  });

  const floatAntes = Math.sin(frame * 0.14) * 4;
  const floatHoje = Math.cos(frame * 0.16) * 5;

  return (
    <AbsoluteFill
      style={{
        opacity: fadeIn * fadeOut,
        transform: `translateX(${slideTransitionX}px)`,
      }}
    >
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${zoomBase * punchInHoje}) translateY(${panYHoje}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Cabeçalho compacto estritamente na faixa y=166..425 para NUNCA tocar no rosto do dono */}
      <div
        style={{
          position: 'absolute',
          top: 168,
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
              background: 'rgba(17, 24, 39, 0.92)',
              border: `2px solid ${COR_MARCA}`,
              color: '#FFFFFF',
              padding: '8px 22px',
              borderRadius: 999,
              fontSize: 32,
              fontWeight: 800,
            }}
          >
            A SITUAÇÃO REAL
          </div>
          <div
            style={{
              background: COR_MARCA,
              color: '#FFFFFF',
              padding: '8px 22px',
              borderRadius: 999,
              fontSize: 32,
              fontWeight: 800,
            }}
          >
            SuperChat IA
          </div>
        </div>

        {/* Comparativo Antes x Hoje no topo (y=240..420) em layout fixo de 2 colunas (50%/50%) desde o início */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 18,
            width: '100%',
          }}
        >
          {/* Card ANTES (sempre 50% da largura, sem encolher bruscamente) */}
          <div
            style={{
              background: 'rgba(17, 24, 39, 0.94)',
              border: `3px solid ${chegouHoje ? 'rgba(239,68,68,0.72)' : '#EF4444'}`,
              borderRadius: 24,
              padding: '16px 20px',
              transform: `translateY(${(1 - popAntes) * -24 + floatAntes}px)`,
              opacity: Math.max(0.82, popAntes),
              boxShadow: '0 12px 28px rgba(0,0,0,0.48)',
            }}
          >
            <div
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: '#FCA5A5',
                marginBottom: 4,
              }}
            >
              ANTES
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
                lineHeight: 1.16,
              }}
            >
              Alternando celulares
            </div>
          </div>

          {/* Coluna HOJE reservada desde o início (50% da largura) e ativada quando diz "Hoje recebo..." */}
          <div
            style={{
              background: chegouHoje ? COR_MARCA : 'rgba(17, 24, 39, 0.72)',
              border: chegouHoje
                ? '3px solid #FFFFFF'
                : '3px dashed rgba(91, 108, 255, 0.65)',
              borderRadius: 24,
              padding: '16px 20px',
              transform: chegouHoje
                ? `translateY(${(1 - popHoje) * 24 + floatHoje}px) scale(${0.94 + 0.06 * popHoje})`
                : `translateY(${-floatAntes * 0.6}px)`,
              opacity: chegouHoje ? popHoje : 0.78,
              boxShadow: chegouHoje
                ? '0 16px 34px rgba(91,108,255,0.55)'
                : '0 8px 20px rgba(0,0,0,0.35)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 4,
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                HOJE
              </span>
              {chegouHoje && <IconCheck size={34} color="#FFFFFF" />}
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.16,
              }}
            >
              Tudo num único painel
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// CENA 2: 13.37s a 23.51s — Demonstração centralizada de tela cheia do SaaS SuperChat IA (Caixa de Entrada Unificada + Multi Atendimento & CRM), rompendo totalmente o layout lateral da Cena 0
const Cena2ComoFunciona: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const iniS = 13.37;
  const durS = 23.51 - 13.37;
  const durFrames = Math.round(durS * fps);
  const tAbs = iniS + frame / fps;

  const sEntradaCena = spring({
    frame,
    fps,
    config: {damping: 13, stiffness: 160},
  });
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(tAbs, [23.12, 23.49], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitScale = interpolate(tAbs, [23.12, 23.49], [1, 1.08], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Camera pan/zoom contínuo na interface do sistema
  const zoomUI = interpolate(
    frame,
    [0, Math.round(durFrames * 0.5), durFrames],
    [0.96, 1.0, 1.02],
    {extrapolateRight: 'clamp'}
  );
  const tiltX = interpolate(frame, [0, durFrames], [4, -2], {
    extrapolateRight: 'clamp',
  });
  const floatY = Math.sin(frame * 0.14) * 5;

  const itensPainel = [
    {
      canal: 'WhatsApp',
      cor: COR_WHATS,
      ini: 16.85,
      updateIni: 19.15,
      msgInicial: 'Cliente: Quero conhecer o plano',
      msgAtualizada: 'Respondido no painel único ✓',
      badge: 'WHATSAPP',
      badgeUpdate: 'NO CRM',
      icon: <IconWhats size={40} />,
    },
    {
      canal: 'Instagram',
      cor: COR_INSTA,
      ini: 17.7,
      updateIni: 19.65,
      msgInicial: 'Direct: Vi o anúncio no Reels',
      msgAtualizada: 'Respondido na mesma fila ✓',
      badge: 'DIRECT',
      badgeUpdate: 'ATIVO',
      icon: <IconInsta size={40} />,
    },
    {
      canal: 'Telegram',
      cor: COR_TELE,
      ini: 18.38,
      updateIni: 20.15,
      msgInicial: 'Chat: Equipe conectada aqui',
      msgAtualizada: 'Histórico sincronizado no CRM ✓',
      badge: 'TELEGRAM',
      badgeUpdate: 'UNIFICADO',
      icon: <IconTele size={40} />,
    },
  ];

  const mostrarJuntas = tAbs >= 18.9;
  const mostrarCRM = tAbs >= 19.85;
  const popCRM = spring({
    frame: Math.max(0, Math.round((tAbs - 19.85) * fps)),
    fps,
    config: {damping: 11, stiffness: 175},
  });
  const shineCRM = interpolate(frame % 48, [0, 48], [-240, 960]);

  const etapasCRM = [
    {nome: 'Entrada', ini: 19.9},
    {nome: 'Atendimento', ini: 20.65},
    {nome: 'CRM', ini: 21.45},
  ];

  return (
    <AbsoluteFill
      style={{
        opacity: fadeIn * fadeOut,
        transform: `scale(${(0.92 + 0.08 * sEntradaCena) * exitScale})`,
        background:
          'radial-gradient(circle at 50% 25%, #1E293B 0%, #0F172A 60%, #090D16 100%)',
      }}
    >
      {/* Grade tecnológica arquitetônica em movimento contínuo (sem banco de imagem corporativo repetido) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(91,108,255,0.10) 2px, transparent 2px), linear-gradient(90deg, rgba(91,108,255,0.10) 2px, transparent 2px)',
          backgroundSize: '72px 72px',
          transform: `translateY(${(frame * 1.4) % 72}px)`,
        }}
      />

      {/* TOPO: Rótulo + Cabeçalho SaaS Centralizado (y=168..355) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
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
              background: COR_MARCA,
              color: '#FFFFFF',
              padding: '8px 24px',
              borderRadius: 999,
              fontSize: 33,
              fontWeight: 800,
            }}
          >
            COMO FUNCIONA
          </div>
          <div
            style={{
              background: 'rgba(17, 24, 39, 0.92)',
              color: '#FFFFFF',
              padding: '8px 22px',
              borderRadius: 999,
              fontSize: 32,
              fontWeight: 700,
              border: '2px solid rgba(255,255,255,0.28)',
            }}
          >
            Simulação
          </div>
        </div>

        <div
          style={{
            background: 'rgba(17, 24, 39, 0.96)',
            borderRadius: 24,
            padding: '16px 28px',
            borderLeft: `12px solid ${COR_MARCA}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 14px 32px rgba(0,0,0,0.52)',
          }}
        >
          <span
            style={{
              fontSize: 44,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.12,
            }}
          >
            SuperChat IA · Painel Único
          </span>
          <div
            style={{
              background: mostrarJuntas ? COR_WHATS : COR_MARCA,
              color: '#FFFFFF',
              padding: '8px 20px',
              borderRadius: 999,
              fontSize: 32,
              fontWeight: 800,
              whiteSpace: 'nowrap',
            }}
          >
            Fila Única
          </div>
        </div>
      </div>

      {/* CENTRO: Interface SaaS de largura total (x=60..1020, width=960) — todas as 4 abas cabem com folga sem jamais estourar a borda direita */}
      <div
        style={{
          position: 'absolute',
          top: 382,
          left: 60,
          right: 60,
          perspective: 1400,
        }}
      >
        <div
          style={{
            background: '#0F172A',
            borderRadius: 34,
            border: `3px solid ${COR_MARCA}`,
            padding: '24px 26px',
            boxShadow: '0 28px 64px rgba(0,0,0,0.72)',
            transform: `rotateX(${tiltX}deg) translateY(${floatY}px) scale(${zoomUI})`,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {/* Cabeçalho da Caixa de Entrada Unificada */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(255,255,255,0.16)',
              paddingBottom: 14,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: 7,
                  background: COR_MARCA,
                }}
              />
              <span
                style={{
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  whiteSpace: 'nowrap',
                }}
              >
                Caixa de Entrada Unificada
              </span>
            </div>
            <div
              style={{
                background: 'rgba(22, 163, 74, 0.22)',
                border: '2px solid #4ADE80',
                color: '#FFFFFF',
                padding: '6px 18px',
                borderRadius: 999,
                fontSize: 32,
                fontWeight: 800,
                whiteSpace: 'nowrap',
              }}
            >
              3 Canais
            </div>
          </div>

          {/* Barra de 4 abas com grid de 4 colunas contida 100% dentro do container de 960px (sem estourar 'Telegram') */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: 10,
              width: '100%',
            }}
          >
            {[
              {rot: 'Todos', ativo: mostrarJuntas, cor: COR_MARCA},
              {rot: 'WhatsApp', ativo: tAbs >= 16.85, cor: COR_WHATS},
              {rot: 'Instagram', ativo: tAbs >= 17.7, cor: COR_INSTA},
              {rot: 'Telegram', ativo: tAbs >= 18.38, cor: COR_TELE},
            ].map((aba) => (
              <div
                key={aba.rot}
                style={{
                  background: aba.ativo ? aba.cor : 'rgba(30, 41, 59, 0.92)',
                  color: '#FFFFFF',
                  padding: '10px 8px',
                  borderRadius: 16,
                  fontSize: 32,
                  fontWeight: 800,
                  textAlign: 'center',
                  whiteSpace: 'nowrap',
                  border: aba.ativo
                    ? '2px solid #FFFFFF'
                    : '2px solid rgba(255,255,255,0.2)',
                }}
              >
                {aba.rot}
              </div>
            ))}
          </div>

          {/* Mensagens dos 3 canais entrando e sendo respondidas em uma única fila */}
          {itensPainel.map((item, idx) => {
            const apareceu = tAbs >= item.ini - 0.08;
            const atualizado = tAbs >= item.updateIni;
            const s = spring({
              frame: Math.max(0, Math.round((tAbs - item.ini) * fps)),
              fps,
              config: {damping: 10, stiffness: 175},
            });
            const sUpdate = spring({
              frame: Math.max(0, Math.round((tAbs - item.updateIni) * fps)),
              fps,
              config: {damping: 9, stiffness: 185},
            });
            const emDestaqueAgora =
              (tAbs >= item.ini && tAbs < item.ini + 0.85) ||
              (tAbs >= item.updateIni && tAbs < item.updateIni + 0.85);
            const pulseCard = apareceu
              ? 1 +
                Math.sin((frame + idx * 11) * 0.22) * 0.018 +
                (atualizado ? (1 - sUpdate) * 0.04 : 0)
              : 0.96;

            return (
              <div
                key={item.canal}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: apareceu
                    ? 'rgba(30, 41, 59, 0.98)'
                    : 'rgba(30, 41, 59, 0.72)',
                  borderRadius: 24,
                  padding: '16px 22px',
                  borderLeft: `14px solid ${item.cor}`,
                  borderTop: `2px solid ${emDestaqueAgora ? '#FFFFFF' : 'rgba(255,255,255,0.18)'}`,
                  borderRight: `2px solid ${emDestaqueAgora ? '#FFFFFF' : 'rgba(255,255,255,0.18)'}`,
                  borderBottom: `2px solid ${emDestaqueAgora ? '#FFFFFF' : 'rgba(255,255,255,0.18)'}`,
                  transform: `translateX(${apareceu ? (1 - s) * -60 : 0}px) scale(${pulseCard})`,
                  opacity: apareceu ? 1 : 0.76,
                  boxShadow: emDestaqueAgora
                    ? '0 14px 30px rgba(91,108,255,0.42)'
                    : 'none',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
                  <div
                    style={{
                      width: 60,
                      height: 60,
                      borderRadius: 18,
                      background: item.cor,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {item.icon}
                  </div>
                  <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                    <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                      <span
                        style={{
                          fontSize: 36,
                          fontWeight: 900,
                          color: '#FFFFFF',
                        }}
                      >
                        {item.canal}
                      </span>
                      {apareceu && (
                        <span
                          style={{
                            background: atualizado ? COR_MARCA : item.cor,
                            color: '#FFFFFF',
                            padding: '4px 14px',
                            borderRadius: 999,
                            fontSize: 32,
                            fontWeight: 800,
                          }}
                        >
                          {atualizado ? item.badgeUpdate : item.badge}
                        </span>
                      )}
                    </div>
                    <span
                      style={{
                        fontSize: 34,
                        fontWeight: 700,
                        color: atualizado ? '#86EFAC' : '#F1F5F9',
                      }}
                    >
                      {atualizado ? item.msgAtualizada : item.msgInicial}
                    </span>
                  </div>
                </div>
                {apareceu && <IconCheck size={40} color="#FFFFFF" />}
              </div>
            );
          })}

          {/* Módulo de Pipeline Multi Atendimento + CRM com tipografia grande (34px) */}
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              background: mostrarCRM ? COR_MARCA : 'rgba(91, 108, 255, 0.28)',
              border: '3px solid #FFFFFF',
              borderRadius: 24,
              padding: '16px 22px',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
              transform: `scale(${mostrarCRM ? 0.96 + 0.04 * popCRM : 0.98})`,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                MULTI ATENDIMENTO + CRM
              </span>
              <span
                style={{
                  background: '#111827',
                  color: '#FFFFFF',
                  padding: '6px 18px',
                  borderRadius: 999,
                  fontSize: 32,
                  fontWeight: 800,
                }}
              >
                Integrado
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr 1fr',
                gap: 12,
              }}
            >
              {etapasCRM.map((et, i) => {
                const ativaEtapa = tAbs >= et.ini;
                return (
                  <div
                    key={et.nome}
                    style={{
                      background: ativaEtapa
                        ? '#111827'
                        : 'rgba(17, 24, 39, 0.55)',
                      color: '#FFFFFF',
                      borderRadius: 14,
                      padding: '10px 12px',
                      textAlign: 'center',
                      fontSize: 34,
                      fontWeight: 800,
                      border: ativaEtapa
                        ? '2px solid #FFFFFF'
                        : '2px solid rgba(255,255,255,0.28)',
                      transform: `scale(${ativaEtapa ? 1 + Math.sin((frame + i * 8) * 0.25) * 0.025 : 0.98})`,
                    }}
                  >
                    {et.nome}
                  </div>
                );
              })}
            </div>

            {mostrarCRM && (
              <div
                style={{
                  position: 'absolute',
                  top: -30,
                  left: shineCRM,
                  width: 110,
                  height: 210,
                  background:
                    'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.38) 50%, rgba(255,255,255,0) 100%)',
                  transform: 'rotate(22deg)',
                  pointerEvents: 'none',
                }}
              />
            )}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// CENA 3: 23.16s a 31.34s — Dono falando com corte de punch-in em 'vinte e quatro horas' + 1 único card limpo e elegante no topo (y=164..350), deixando ampla folga acima do cabelo do apresentador
const Cena3Resultado: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const iniS = 23.16;
  const durS = 31.34 - 23.16;
  const durFrames = Math.round(durS * fps);
  const tAbs = iniS + frame / fps;

  const sEntradaCena = spring({
    frame,
    fps,
    config: {damping: 13, stiffness: 165},
  });
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(tAbs, [30.92, 31.3], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const slideTransitionY = (1 - sEntradaCena) * -70;

  // Corte seco de punch-in digital em 'vinte e quatro horas' (tAbs >= 27.05s) + panY maior para garantir > 60px de respiro entre o card superior e o cabelo do dono
  const emPunchIn24h = tAbs >= 27.05;
  const zoomBase = interpolate(frame, [0, durFrames], [1.1, 1.15], {
    extrapolateRight: 'clamp',
  });
  const zoomVideo = emPunchIn24h ? zoomBase * 1.12 : zoomBase;
  const panVideoX = interpolate(frame, [0, durFrames], [-14, -24], {
    extrapolateRight: 'clamp',
  });
  const panVideoY = emPunchIn24h ? 195 : 155;

  const faseIA = tAbs >= 26.25;
  const fase24h = tAbs >= 27.05;
  const faseEquipe = tAbs >= 29.0;

  const popCard = spring({
    frame: Math.max(0, frame - 2),
    fps,
    config: {damping: 12, stiffness: 170},
  });
  const popStatus = spring({
    frame: Math.max(
      0,
      Math.round((tAbs - (faseEquipe ? 29.0 : fase24h ? 27.05 : 24.2)) * fps)
    ),
    fps,
    config: {damping: 10, stiffness: 185},
  });
  const floatCard = Math.sin(frame * 0.16) * 4;

  const statusEvolucao = faseEquipe
    ? 'IA 24h + Equipe ativa ✓'
    : fase24h
      ? 'IA 24h: Ativo agora ✓'
      : faseIA
        ? 'IA 24h respondendo...'
        : 'Canais Centralizados ✓';

  return (
    <AbsoluteFill
      style={{
        opacity: fadeIn * fadeOut,
        transform: `translateY(${slideTransitionY}px)`,
      }}
    >
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${zoomVideo}) translate(${panVideoX}px, ${panVideoY}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Topo limpo com 1 único card compacto (y=164..344), sem empilhar 3 pílulas + caixa, garantindo amplo respiro acima da cabeça do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 164,
          left: 60,
          right: 60,
          background: 'rgba(15, 23, 42, 0.95)',
          borderRadius: 26,
          border: `3px solid ${faseIA ? COR_WHATS : COR_MARCA}`,
          padding: '16px 24px',
          boxShadow: '0 18px 38px rgba(0,0,0,0.58)',
          transform: `translateY(${(1 - popCard) * -24 + floatCard}px)`,
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 14,
                background: faseIA ? COR_WHATS : COR_MARCA,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <IconWhats size={30} />
            </div>
            <span
              style={{
                fontSize: 35,
                fontWeight: 900,
                color: '#FFFFFF',
                whiteSpace: 'nowrap',
              }}
            >
              Atendimento IA 24h no WhatsApp
            </span>
          </div>
          <span
            style={{
              background: 'rgba(255,255,255,0.16)',
              color: '#FFFFFF',
              padding: '4px 16px',
              borderRadius: 999,
              fontSize: 32,
              fontWeight: 700,
              whiteSpace: 'nowrap',
            }}
          >
            Simulação
          </span>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 14,
          }}
        >
          <div
            style={{
              background: 'rgba(30, 41, 59, 0.96)',
              color: '#E2E8F0',
              padding: '8px 18px',
              borderRadius: 14,
              fontSize: 32,
              fontWeight: 700,
              border: '2px solid rgba(255,255,255,0.2)',
              whiteSpace: 'nowrap',
            }}
          >
            Cliente: Tem atendimento?
          </div>

          <div
            style={{
              flex: 1,
              background: faseIA ? COR_WHATS : COR_MARCA,
              color: '#FFFFFF',
              padding: '8px 18px',
              borderRadius: 14,
              fontSize: 33,
              fontWeight: 900,
              border: '2px solid #FFFFFF',
              textAlign: 'center',
              whiteSpace: 'nowrap',
              transform: `scale(${0.95 + 0.05 * popStatus})`,
            }}
          >
            {statusEvolucao}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// CENA 4: 30.99s a 34.94s — Cartão Final Flat/Clean Tech, Minimalista e com Movimento Contínuo Garantido até o último frame (q13, q14 e q15 visivelmente diferentes)
const Cena4Cartao: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((34.94 - 30.99) * fps);

  const fadeIn = interpolate(frame, [0, 9], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Movimento contínuo forte de fundo + anéis geométricos para garantir >8% de diferença entre q13, q14 e q15
  const zoomBg = interpolate(frame, [0, durFrames], [1.02, 1.28], {
    extrapolateRight: 'clamp',
  });
  const panBgX = interpolate(frame, [0, durFrames], [-60, 65], {
    extrapolateRight: 'clamp',
  });
  const panBgY = interpolate(frame, [0, durFrames], [-35, 40], {
    extrapolateRight: 'clamp',
  });

  const popLogo = spring({
    frame: Math.max(0, frame - 2),
    fps,
    config: {damping: 12, stiffness: 155},
  });

  const popBotao = spring({
    frame: Math.max(0, frame - 6),
    fps,
    config: {damping: 11, stiffness: 165},
  });

  // Pulso contínuo de 1.00 para 1.045 em loop + shimmer diagonal contínuo cruzando o botão a cada 32 frames
  const pulseBotao = 1.022 + Math.sin(frame * 0.34) * 0.024;
  const floatCard = Math.sin(frame * 0.24) * 14;
  const shineX = interpolate(frame % 32, [0, 32], [-220, 980]);
  const ringScale1 = 0.85 + ((frame * 0.018) % 0.65);
  const ringOpacity1 = interpolate((frame * 0.018) % 0.65, [0, 0.65], [0.42, 0]);

  return (
    <AbsoluteFill style={{opacity: fadeIn, backgroundColor: COR_ESCURA}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(8px)',
            transform: `scale(${zoomBg}) translate(${panBgX}px, ${panBgY}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Véu clean tech escuro da marca */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.78) 0%, rgba(15,23,42,0.86) 55%, rgba(17,24,39,0.92) 100%)',
        }}
      />

      {/* Onda concêntrica contínua atrás do CTA mantendo a tela viva até o último segundo */}
      <div
        style={{
          position: 'absolute',
          top: 660,
          left: 140,
          width: 800,
          height: 360,
          borderRadius: 999,
          border: `4px solid ${COR_MARCA}`,
          transform: `scale(${ringScale1})`,
          opacity: ringOpacity1,
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo Clean Tech centralizado verticalmente na Safe Zone (y=290..1470), sem ruído de 3 badges de redes acima do botão */}
      <div
        style={{
          position: 'absolute',
          top: 290,
          bottom: 450,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          textAlign: 'center',
        }}
      >
        {/* BLOCO 1 (Topo): Marca SuperChat IA + Proposta de valor limpa */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 22,
            transform: `translateY(${floatCard * 0.65}px) scale(${0.92 + 0.08 * popLogo})`,
          }}
        >
          <div
            style={{
              background: 'rgba(91, 108, 255, 0.22)',
              border: `2px solid ${COR_MARCA}`,
              color: '#FFFFFF',
              padding: '10px 28px',
              borderRadius: 999,
              fontSize: 33,
              fontWeight: 800,
              letterSpacing: 0.8,
            }}
          >
            PAINEL ÚNICO + IA
          </div>

          <div
            style={{
              fontSize: 94,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -1.5,
              lineHeight: 1.04,
            }}
          >
            SuperChat IA
          </div>

          <div
            style={{
              background: 'rgba(17, 24, 39, 0.90)',
              border: '2px solid rgba(255,255,255,0.2)',
              borderRadius: 24,
              padding: '18px 32px',
              fontSize: 38,
              fontWeight: 800,
              color: '#F8FAFC',
              lineHeight: 1.24,
              maxWidth: 880,
            }}
          >
            Multi atendimento com CRM e IA.
            <br />
            WhatsApp, Instagram e Telegram no mesmo painel.
          </div>
        </div>

        {/* BLOCO 2 (Centro): Botão Protagonista Clean Tech com pulso contínuo (1.00 -> 1.045) e sheen pass diagonal em loop */}
        <div
          style={{
            position: 'relative',
            overflow: 'hidden',
            background: COR_MARCA,
            color: '#FFFFFF',
            padding: '38px 80px',
            borderRadius: 999,
            fontSize: 54,
            fontWeight: 900,
            letterSpacing: 1.0,
            border: '4px solid #FFFFFF',
            boxShadow: '0 20px 44px rgba(91,108,255,0.55)',
            transform: `translateY(${floatCard * 0.5}px) scale(${popBotao * pulseBotao})`,
            display: 'flex',
            alignItems: 'center',
            gap: 18,
          }}
        >
          <IconInsta size={48} />
          <span>CHAME NO DIRECT</span>
          <div
            style={{
              position: 'absolute',
              top: -60,
              left: shineX,
              width: 110,
              height: 260,
              background:
                'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.38) 50%, rgba(255,255,255,0) 100%)',
              transform: 'rotate(24deg)',
              pointerEvents: 'none',
            }}
          />
        </div>

        {/* BLOCO 3 (Base dentro de y=1300..1470): @superchatia.ia */}
        <div
          style={{
            background: '#111827',
            border: `3px solid ${COR_MARCA}`,
            color: '#FFFFFF',
            padding: '18px 50px',
            borderRadius: 999,
            fontSize: 44,
            fontWeight: 900,
            boxShadow: '0 14px 32px rgba(0,0,0,0.55)',
            transform: `translateY(${-floatCard * 0.55}px)`,
          }}
        >
          {briefing.arroba}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;

  const progresso = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateRight: 'clamp',
  });

  // Palavras para o Karaokê (somente cenas 0 a 3; oculta no cartão final) com quebras sintáticas equilibradas sem palavras órfãs
  const indicesQuebraAntes = new Set([
    5, // "para responder WhatsApp"
    8, // "Instagram e Telegram"
    11, // "Eu ficava alternando..."
    16, // "para atender."
    18, // "Hoje recebo todas..."
    23, // "juntas num único painel."
    27, // "No SuperChat IA"
    30, // "as mensagens do WhatsApp"
    34, // "Instagram e Telegram"
    37, // "chegam juntas no painel"
    41, // "de multi atendimento com CRM"
    46, // "Além de centralizar esses canais,"
    51, // "conto com inteligência artificial"
    55, // "vinte e quatro horas no WhatsApp"
    61, // "para minha equipe."
  ]);
  const indicesQuebraLinha = new Set([
    3, // "Cansado de trocar / de tela"
    7, // "para responder / WhatsApp"
    14, // "Eu ficava alternando / entre celulares"
    21, // "Hoje recebo todas / as mensagens"
    25, // "juntas num / único painel."
    33, // "as mensagens do / WhatsApp"
    39, // "chegam juntas / no painel"
    44, // "de multi atendimento / com CRM"
    49, // "Além de centralizar / esses canais,"
    53, // "conto com / inteligência artificial"
    59, // "vinte e quatro horas / no WhatsApp"
  ]);

  const palavrasKaraoke: PalavraK[] = (briefing.palavras as Array<{
    p: string;
    ini: number;
    fim: number;
    cena: number;
  }>)
    .filter((w) => w.cena !== 4)
    .map((w, idx, arr) => ({
      p: w.p,
      ini: w.ini,
      fim: w.fim,
      quebraAntes:
        (idx > 0 && arr[idx - 1].cena !== w.cena) ||
        indicesQuebraAntes.has(idx),
      quebraLinha: indicesQuebraLinha.has(idx),
    }));

  const volTrilha = interpolate(
    frame,
    [0, 15, durationInFrames - 25, durationInFrames],
    [0, 0.1, 0.1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, fontFamily}}>
      {/* Áudio principal e trilha */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volTrilha} />

      {/* CENA 0: 0.00s - 5.89s */}
      <Sequence from={0} durationInFrames={Math.ceil(5.89 * fps)}>
        <Cena0Pergunta />
      </Sequence>

      {/* CENA 1: 5.54s - 13.72s */}
      <Sequence
        from={Math.round(5.54 * fps)}
        durationInFrames={Math.ceil((13.72 - 5.54) * fps)}
      >
        <Cena1Dono />
      </Sequence>

      {/* CENA 2: 13.37s - 23.51s */}
      <Sequence
        from={Math.round(13.37 * fps)}
        durationInFrames={Math.ceil((23.51 - 13.37) * fps)}
      >
        <Cena2ComoFunciona />
      </Sequence>

      {/* CENA 3: 23.16s - 31.34s */}
      <Sequence
        from={Math.round(23.16 * fps)}
        durationInFrames={Math.ceil((31.34 - 23.16) * fps)}
      >
        <Cena3Resultado />
      </Sequence>

      {/* CENA 4: 30.99s - 34.94s */}
      <Sequence
        from={Math.round(30.99 * fps)}
        durationInFrames={Math.ceil((34.94 - 30.99) * fps)}
      >
        <Cena4Cartao />
      </Sequence>

      {/* Barra de Progresso no topo dentro da Safe Zone (y=154, x=60..1020) */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          height: 8,
          borderRadius: 999,
          background: 'rgba(255,255,255,0.24)',
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            background: COR_MARCA,
            borderRadius: 999,
          }}
        />
      </div>

      {/*Legenda Karaokê oficial (oculta no cartão final t >= 30.95s)*/}
      {t < 30.95 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={COR_MARCA}
          textoDestaque="#FFFFFF"
          tamanho={46}
          base={360}
          maxLetras={42}
        />
      )}
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={VideoPrincipal}
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
