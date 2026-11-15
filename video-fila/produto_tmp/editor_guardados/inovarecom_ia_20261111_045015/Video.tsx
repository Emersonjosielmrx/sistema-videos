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
  marca: '#25D366',
  apoio: '#075E54',
  fundoEscuro: '#082E16',
  destaque: '#25D366',
  textoSobreMarca: '#121216',
  alerta: '#FF4D4D',
  amarelo: '#FACC15',
};

const PALAVRAS_K: PalavraK[] = [
  // Cena 0
  {p: 'Sua', ini: 0.317, fim: 0.588},
  {p: 'equipe', ini: 0.6, fim: 0.954},
  {p: 'perde', ini: 0.966, fim: 1.296},
  {p: 'vendas', ini: 1.308, fim: 1.685, quebraApos: true},
  {p: 'por', ini: 1.697, fim: 1.862},
  {p: 'falta', ini: 1.874, fim: 2.204},
  {p: 'de braço', ini: 2.216, fim: 2.711},
  {p: 'para', ini: 2.723, fim: 2.888},
  {p: 'ligar?', ini: 2.9, fim: 3.289, quebraApos: true},
  // Cena 1
  {p: 'Eu', ini: 4.388, fim: 4.728, quebraAntes: true},
  {p: 'achava', ini: 4.728, fim: 5.028},
  {p: 'complicado', ini: 5.028, fim: 5.748, quebraApos: true},
  {p: 'colocar', ini: 5.748, fim: 6.188},
  {p: 'robôs', ini: 6.188, fim: 6.828},
  {p: 'para discar,', ini: 6.828, fim: 7.848, quebraApos: true},
  {p: 'até', ini: 8.108, fim: 8.188},
  {p: 'centralizar', ini: 8.188, fim: 9.068},
  {p: 'todas', ini: 9.068, fim: 9.568, quebraApos: true},
  {p: 'as chamadas', ini: 9.568, fim: 10.208},
  {p: 'de vendas', ini: 10.208, fim: 11.008},
  {p: 'no WhatsApp.', ini: 11.008, fim: 11.748, quebraApos: true},
  // Cena 2
  {p: 'O Hermes Call', ini: 12.56, fim: 13.209, quebraAntes: true},
  {p: 'faz', ini: 13.221, fim: 13.433},
  {p: 'ligações', ini: 13.445, fim: 13.916},
  {p: 'em massa', ini: 13.928, fim: 14.412, quebraApos: true},
  {p: 'com voz', ini: 14.423, fim: 14.86},
  {p: 'real', ini: 14.872, fim: 15.166},
  {p: 'e clonada,', ini: 15.178, fim: 15.779, quebraApos: true},
  {p: 'oferecendo', ini: 15.921, fim: 16.463},
  {p: 'atendimento', ini: 16.475, fim: 17.018},
  {p: 'contínuo.', ini: 17.029, fim: 17.596, quebraApos: true},
  // Cena 3
  {p: 'Hoje', ini: 18.52, fim: 18.96, quebraAntes: true},
  {p: 'minha', ini: 19.06, fim: 19.12},
  {p: 'operação', ini: 19.12, fim: 19.84, quebraApos: true},
  {p: 'liga', ini: 19.84, fim: 20.36},
  {p: 'e vende', ini: 20.36, fim: 21.08},
  {p: 'sem parar', ini: 21.08, fim: 21.76, quebraApos: true},
  {p: 'com', ini: 21.76, fim: 22.22},
  {p: 'inteligência', ini: 22.22, fim: 22.78},
  {p: 'artificial,', ini: 22.78, fim: 23.38, quebraApos: true},
  {p: 'escalando', ini: 23.96, fim: 24.6},
  {p: 'no ritmo', ini: 24.6, fim: 25.18},
  {p: 'que preciso.', ini: 25.18, fim: 25.86, quebraApos: true},
  // Cena 4 (Cartão Final)
  {p: 'Chame', ini: 26.692, fim: 27.034, quebraAntes: true},
  {p: 'a gente', ini: 27.046, fim: 27.435},
  {p: 'no direct.', ini: 27.447, fim: 28.154, quebraApos: true},
];

// Ícone de Telefone + Ondas IA
const IconeTelefoneIA: React.FC<{cor?: string; tamanho?: number}> = ({
  cor = '#25D366',
  tamanho = 44,
}) => (
  <svg width={tamanho} height={tamanho} viewBox="0 0 48 48" fill="none">
    <path
      d="M13.2 8.5C14.1 8.5 15 9 15.5 9.8L18.4 15.1C18.9 16 18.7 17.1 18 17.8L15.2 20.6C17.1 24.5 20.3 27.7 24.2 29.6L27 26.8C27.7 26.1 28.8 25.9 29.7 26.4L35 29.3C35.8 29.8 36.3 30.7 36.3 31.6V36.2C36.3 37.9 34.8 39.3 33.1 39.1C19.4 37.6 8.4 26.6 6.9 12.9C6.7 11.2 8.1 9.7 9.8 9.7H13.2V8.5Z"
      fill={cor}
    />
    <path
      d="M28 11C32.4 11 36 14.6 36 19"
      stroke={cor}
      strokeWidth="3.5"
      strokeLinecap="round"
    />
    <path
      d="M28 5C35.7 5 42 11.3 42 19"
      stroke={cor}
      strokeWidth="3.5"
      strokeLinecap="round"
    />
  </svg>
);

// ============================================================================
// CENA 0: PERGUNTA (0.00s - 4.74s)
// "Sua equipe perde vendas por falta de braço para ligar?"
// ============================================================================
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const bgScale = interpolate(frame, [0, 45, 142], [1.0, 1.12, 1.24], {
    extrapolateRight: 'clamp',
  });
  const bgPanX = interpolate(frame, [0, 142], [0, -42], {
    extrapolateRight: 'clamp',
  });

  const exitOpacity = interpolate(t, [4.25, 4.42], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const badgeIn = spring({frame: frame - 1, fps, config: {damping: 11, stiffness: 160}});
  const title1In = spring({frame: frame - 3, fps, config: {damping: 11, stiffness: 160}});
  const title2In = spring({frame: Math.max(0, frame - 9), fps, config: {damping: 11, stiffness: 160}});
  const title3In = spring({frame: Math.max(0, frame - 15), fps, config: {damping: 11, stiffness: 160}});
  const cardIn = spring({frame: Math.max(0, frame - 5), fps, config: {damping: 12, stiffness: 150}});

  // Slow zoom-in contínuo (escala 1.0 para 1.07) + leve flutuação contínua sem parar
  const cardPushScale = interpolate(frame, [0, 142], [1.0, 1.07], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const rotY = interpolate(frame, [0, 142], [-14, 8]);
  const rotX = interpolate(frame, [0, 142], [6, -4]);
  const floatY = Math.sin(frame * 0.16) * 12;

  const alertaPulse = 0.5 + 0.5 * Math.sin(frame * 0.32);
  // Barra de progresso interna crescendo de 0% a 100% durante a pergunta inicial
  const sobrecargaPct = interpolate(frame, [8, 110], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: exitOpacity, fontFamily}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translateX(${bgPanX}px)`,
          }}
        />
        {/* Grid dinâmico e luz dramática */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 28%, rgba(255, 77, 77, 0.24) 0%, rgba(8, 46, 22, 0.90) 70%)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(37, 211, 102, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(37, 211, 102, 0.08) 1px, transparent 1px)',
            backgroundSize: '64px 64px',
            transform: `translateY(${(frame * 1.4) % 64}px)`,
          }}
        />
      </AbsoluteFill>

      {/* TOPO: Gancho da tela como selo + Pergunta falada em destaque */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 20,
        }}
      >
        {/* Selo gancho_tela */}
        <div
          style={{
            transform: `scale(${badgeIn})`,
            background: 'rgba(10, 22, 15, 0.92)',
            border: `2px solid ${CORES.marca}`,
            borderRadius: 999,
            padding: '10px 28px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            boxShadow: '0 8px 24px rgba(0,0,0,0.45)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: 7,
              background: CORES.marca,
              boxShadow: `0 0 12px ${CORES.marca}`,
            }}
          />
          <span
            style={{
              color: '#FFFFFF',
              fontSize: 33,
              fontWeight: 800,
              letterSpacing: 0.5,
              textTransform: 'uppercase',
            }}
          >
            Chamadas automáticas sem complicação
          </span>
        </div>

        {/* Pergunta principal sincronizada com a fala */}
        <div
          style={{
            width: '100%',
            background: 'rgba(8, 20, 14, 0.88)',
            border: '2px solid rgba(255,255,255,0.16)',
            borderRadius: 28,
            padding: '24px 30px',
            boxShadow: '0 18px 40px rgba(0,0,0,0.55)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <div
            style={{
              opacity: title1In,
              transform: `translateY(${(1 - title1In) * 20}px)`,
              fontSize: 52,
              fontWeight: 900,
              color: '#FFFFFF',
              textAlign: 'center',
              lineHeight: 1.15,
            }}
          >
            SUA EQUIPE{' '}
            <span
              style={{
                display: 'inline-block',
                background: CORES.alerta,
                color: '#FFFFFF',
                padding: '2px 16px',
                borderRadius: 12,
                transform: `scale(${0.92 + 0.08 * title2In})`,
              }}
            >
              PERDE VENDAS
            </span>
          </div>
          <div
            style={{
              opacity: title3In,
              transform: `translateY(${(1 - title3In) * 22}px)`,
              fontSize: 48,
              fontWeight: 800,
              color: CORES.amarelo,
              textAlign: 'center',
              lineHeight: 1.18,
              textWrap: 'balance',
            }}
          >
            POR FALTA DE BRAÇO PARA LIGAR?
          </div>
        </div>
      </div>

      {/* CENTRO NOBRE: Painel de Dor Visual Limpo e Direto (Sem excesso de microtextos) */}
      <div
        style={{
          position: 'absolute',
          top: 565,
          left: 70,
          right: 70,
          height: 600,
          perspective: 1200,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            width: 900,
            background: 'linear-gradient(165deg, rgba(16, 32, 24, 0.96), rgba(9, 18, 14, 0.98))',
            borderRadius: 34,
            border: '3px solid rgba(255, 77, 77, 0.65)',
            boxShadow: '0 28px 60px rgba(0,0,0,0.7)',
            padding: '30px 36px',
            transform: `scale(${cardIn * cardPushScale}) translateY(${floatY}px) rotateY(${rotY}deg) rotateX(${rotX}deg)`,
            display: 'flex',
            flexDirection: 'column',
            gap: 22,
          }}
        >
          {/* Cabeçalho de Alerta */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '2px solid rgba(255,255,255,0.12)',
              paddingBottom: 18,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: 11,
                  background: CORES.alerta,
                  boxShadow: `0 0 ${12 + 10 * alertaPulse}px ${CORES.alerta}`,
                }}
              />
              <span style={{color: '#FFFFFF', fontSize: 38, fontWeight: 900}}>
                SOBRECARGA DE VENDAS
              </span>
            </div>
            <div
              style={{
                background: 'rgba(255, 77, 77, 0.25)',
                border: `2px solid ${CORES.alerta}`,
                borderRadius: 14,
                padding: '8px 20px',
                color: '#FFD1D1',
                fontSize: 33,
                fontWeight: 900,
              }}
            >
              ALERTA CRÍTICO
            </div>
          </div>

          {/* Barra de Acúmulo de Chamadas de 0% a 100% com contagem dinâmica */}
          <div style={{display: 'flex', flexDirection: 'column', gap: 12}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <span style={{color: '#E2E8F0', fontSize: 34, fontWeight: 800}}>
                Chamadas acumulando no WhatsApp
              </span>
              <span style={{color: CORES.alerta, fontSize: 36, fontWeight: 900}}>
                {Math.round(sobrecargaPct)}%
              </span>
            </div>
            <div
              style={{
                width: '100%',
                height: 22,
                background: 'rgba(255,255,255,0.14)',
                borderRadius: 999,
                overflow: 'hidden',
                boxShadow: 'inset 0 2px 6px rgba(0,0,0,0.5)',
              }}
            >
              <div
                style={{
                  width: `${sobrecargaPct}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #FACC15 0%, #FF7875 50%, #FF4D4D 100%)',
                  borderRadius: 999,
                  boxShadow: `0 0 16px ${CORES.alerta}`,
                }}
              />
            </div>
          </div>

          {/* Card Único e Direto de Dor — Foco no problema sem microtextos dispersivos */}
          <div
            style={{
              background: 'rgba(255, 77, 77, 0.12)',
              border: `2px solid rgba(255, 77, 77, 0.55)`,
              borderRadius: 22,
              padding: '24px 28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 20,
            }}
          >
            <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
              <span style={{color: '#FFFFFF', fontSize: 40, fontWeight: 900}}>
                EQUIPE SEM TEMPO PARA LIGAR
              </span>
              <span style={{color: '#CBD5E1', fontSize: 34, fontWeight: 700}}>
                Vendas perdidas por falta de braço comercial
              </span>
            </div>
            <div
              style={{
                background: CORES.alerta,
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 900,
                padding: '10px 22px',
                borderRadius: 14,
                whiteSpace: 'nowrap',
                boxShadow: '0 6px 18px rgba(255, 77, 77, 0.45)',
              }}
            >
              TRAVADO
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 1: DONO — O DESAFIO E A VIRADA (4.39s - 12.42s)
// "Eu achava complicado colocar robôs para discar, até centralizar todas as chamadas de vendas no WhatsApp."
// ============================================================================
const Cena1Dono: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  // Cena começa em 4.39s (frame 131 global)
  const absTime = 4.39 + frame / fps;
  const durFrames = Math.round((12.42 - 4.39) * fps);
  const viradaFrame = Math.round((8.108 - 4.39) * fps); // 112 frames (8.108s)

  const enterOp = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitOp = interpolate(frame, [durFrames - 10, durFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const isSolucao = frame >= viradaFrame;

  // Punch-in de câmera (zoom rápido para 1.14x) no exato instante da 'Virada' (8.108s)
  const punchInSpring = spring({
    frame: Math.max(0, frame - viradaFrame),
    fps,
    config: {damping: 12, stiffness: 180},
  });

  // Enquadramento reposicionado 118px para baixo para garantir amplo respiro (headroom positivo) sobre o cabelo
  const videoScale = isSolucao
    ? 1.13 + 0.04 * punchInSpring
    : interpolate(frame, [0, viradaFrame], [1.01, 1.04], {extrapolateRight: 'clamp'});

  const videoTranslateY = isSolucao ? 122 : 118;

  // Flash suave e transição luminosa na virada
  const flashOpacity = interpolate(frame - viradaFrame, [-1, 2, 8], [0, 0.4, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Virada na palavra "até centralizar" (8.108s) com slide/fade lateral fluido
  const viradaProgress = spring({
    frame: Math.max(0, frame - viradaFrame),
    fps,
    config: {damping: 13, stiffness: 130},
  });
  const cardIn = spring({frame: frame - 3, fps, config: {damping: 13}});
  const whatsHighlight = spring({
    frame: Math.max(0, Math.round((absTime - 10.95) * fps)),
    fps,
    config: {damping: 12},
  });

  const iconPulse = isSolucao ? 1 + 0.08 * Math.sin(frame * 0.32) : 1;
  const shimmerCardX = interpolate((frame * 14) % 1050, [0, 1050], [-260, 980]);
  const slideX = isSolucao ? (1 - viradaProgress) * 70 : 0;

  return (
    <AbsoluteFill style={{opacity: enterOp * exitOp, fontFamily}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        {/* Fase 1: O Desafio (0s até 3.718s na cena = 4.39s até 8.108s) */}
        <Sequence from={0} durationInFrames={viradaFrame}>
          <OffthreadVideo
            src={staticFile('dono_1.mp4')}
            startFrom={5}
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transform: `translateY(${videoTranslateY}px) scale(${videoScale})`,
            }}
          />
        </Sequence>

        {/* Fase 2: A Virada com Punch-in e movimento contínuo da locução ativa */}
        <Sequence from={viradaFrame} durationInFrames={52}>
          <OffthreadVideo
            src={staticFile('dono_1.mp4')}
            startFrom={120}
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transform: `translateY(${videoTranslateY}px) scale(${videoScale})`,
            }}
          />
        </Sequence>

        {/* Fase 3: Conclusão da fala com movimento labial natural e sem still frame */}
        <Sequence from={viradaFrame + 52} durationInFrames={durFrames - (viradaFrame + 52)}>
          <OffthreadVideo
            src={staticFile('dono_1.mp4')}
            startFrom={15}
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transform: `translateY(${videoTranslateY}px) scale(${videoScale})`,
            }}
          />
        </Sequence>

        {/* Flash de corte na virada para dinamismo cênico */}
        {flashOpacity > 0 && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'radial-gradient(circle, rgba(37, 211, 102, 0.45) 0%, rgba(255,255,255,0.3) 100%)',
              opacity: flashOpacity,
              pointerEvents: 'none',
            }}
          />
        )}

        {/* Gradiente suave apenas no topo e na base para proteger leitura sem cobrir o rosto */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(6, 20, 12, 0.84) 0%, rgba(6, 20, 12, 0.0) 25%, rgba(6, 20, 12, 0.0) 68%, rgba(6, 20, 12, 0.78) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* FAIXA SUPERIOR (y: 152..345) — Rosto do apresentador com respiro garantido abaixo de y=380 */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          transform: `scale(${cardIn})`,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        {/* Linha de Rótulo + Status */}
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div
            style={{
              background: isSolucao ? CORES.marca : '#F59E0B',
              color: '#121216',
              padding: '6px 22px',
              borderRadius: 999,
              fontSize: 32,
              fontWeight: 900,
              textTransform: 'uppercase',
              boxShadow: '0 8px 20px rgba(0,0,0,0.45)',
              transform: `translateX(${slideX * 0.5}px)`,
            }}
          >
            {isSolucao ? 'A Virada no WhatsApp' : 'O Desafio'}
          </div>
          <div
            style={{
              background: 'rgba(10, 16, 13, 0.92)',
              border: `2px solid ${isSolucao ? CORES.marca : '#F59E0B'}`,
              color: '#FFFFFF',
              padding: '6px 20px',
              borderRadius: 999,
              fontSize: 32,
              fontWeight: 800,
            }}
          >
            {isSolucao ? 'Hermes Call' : 'Antes'}
          </div>
        </div>

        {/* Card dinâmico que alterna com slide lateral + shimmer contínuo na palavra "até centralizar" */}
        <div
          style={{
            position: 'relative',
            overflow: 'hidden',
            background: isSolucao ? 'rgba(8, 28, 18, 0.95)' : 'rgba(8, 22, 15, 0.92)',
            border: `3px solid ${isSolucao ? CORES.marca : '#F59E0B'}`,
            borderRadius: 22,
            padding: '14px 24px',
            boxShadow: isSolucao
              ? '0 16px 38px rgba(37, 211, 102, 0.35)'
              : '0 16px 36px rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 18,
            transform: `translateX(${slideX}px)`,
          }}
        >
          {isSolucao && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shimmerCardX,
                width: 140,
                background:
                  'linear-gradient(90deg, transparent, rgba(37, 211, 102, 0.25), transparent)',
                transform: 'skewX(-20deg)',
                pointerEvents: 'none',
              }}
            />
          )}
          <div style={{display: 'flex', flexDirection: 'column', gap: 4, flex: 1}}>
            <span
              style={{
                color: isSolucao ? CORES.marca : '#FCD34D',
                fontSize: 32,
                fontWeight: 800,
                textTransform: 'uppercase',
              }}
            >
              {isSolucao ? 'Tudo em um só lugar' : 'Sem estrutura certa'}
            </span>
            <span
              style={{
                color: '#FFFFFF',
                fontSize: 36,
                fontWeight: 900,
                lineHeight: 1.15,
                textWrap: 'balance',
              }}
            >
              {isSolucao
                ? 'Chamadas de vendas centralizadas no WhatsApp'
                : 'Colocar robôs para discar parecia complicado'}
            </span>
          </div>

          {/* Indicador lateral vivo com pulso contínuo e brilho no ícone de WhatsApp/Chamada */}
          <div
            style={{
              width: 78,
              height: 78,
              borderRadius: 20,
              background: isSolucao
                ? `rgba(37, 211, 102, ${0.24 + 0.25 * whatsHighlight})`
                : 'rgba(245, 158, 11, 0.2)',
              border: `3px solid ${isSolucao ? CORES.marca : '#F59E0B'}`,
              boxShadow: isSolucao
                ? `0 0 ${16 + 12 * Math.sin(frame * 0.32)}px rgba(37, 211, 102, 0.55)`
                : 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transform: `scale(${iconPulse * (isSolucao ? 1 + 0.06 * whatsHighlight : 1)})`,
            }}
          >
            <IconeTelefoneIA
              cor={isSolucao ? CORES.marca : '#F59E0B'}
              tamanho={42}
            />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 2: VEO — COMO FUNCIONA (12.07s - 18.87s)
// "O Hermes Call faz ligações em massa com voz real e clonada, oferecendo atendimento contínuo."
// ============================================================================
const Cena2Veo: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const absTime = 12.07 + frame / fps;
  const durFrames = Math.round((18.87 - 12.07) * fps);

  const enterOp = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitOp = interpolate(frame, [durFrames - 10, durFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const bgScale = interpolate(frame, [0, durFrames], [1.06, 1.18], {
    extrapolateRight: 'clamp',
  });

  const headerIn = spring({frame: frame - 2, fps, config: {damping: 13}});
  const panelIn = spring({frame: Math.max(0, frame - 5), fps, config: {damping: 13}});
  const callWavePulse = 1 + 0.07 * Math.sin(frame * 0.3);

  // 3 passos sincronizados com a locução:
  // 01: "ligações em massa" (13.445s)
  // 02: "voz real e clonada" (14.624s)
  // 03: "atendimento contínuo" (16.475s)
  const etapas = [
    {
      num: '01',
      titulo: 'Ligações em Massa',
      sub: 'Disparo automático no WhatsApp',
      ini: 13.35,
    },
    {
      num: '02',
      titulo: 'Voz Real e Clonada',
      sub: 'Tom natural na chamada',
      ini: 14.55,
    },
    {
      num: '03',
      titulo: 'Atendimento IA 24h',
      sub: 'Atendimento contínuo sem parar',
      ini: 16.35,
    },
  ];

  return (
    <AbsoluteFill style={{opacity: enterOp * exitOp, fontFamily}}>
      {/* Fundo de interface conceitual escura substituindo visualmente o b-roll genérico de escritório */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('video_2.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(16px) brightness(0.28) saturate(1.4)',
            transform: `scale(${bgScale})`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 38%, rgba(37, 211, 102, 0.24) 0%, rgba(6, 20, 12, 0.94) 72%)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(37, 211, 102, 0.09) 1px, transparent 1px), linear-gradient(90deg, rgba(37, 211, 102, 0.09) 1px, transparent 1px)',
            backgroundSize: '64px 64px',
            transform: `translateY(${(frame * 1.8) % 64}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Cabeçalho no topo (y: 155..295) */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          transform: `translateY(${(1 - headerIn) * -24}px)`,
          opacity: headerIn,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            background: CORES.marca,
            color: '#121216',
            padding: '8px 24px',
            borderRadius: 999,
            fontSize: 33,
            fontWeight: 900,
            textTransform: 'uppercase',
          }}
        >
          Como funciona
        </div>
        <div
          style={{
            background: 'rgba(8, 22, 15, 0.92)',
            border: `2px solid ${CORES.marca}`,
            borderRadius: 999,
            padding: '8px 24px',
            color: '#FFFFFF',
            fontSize: 34,
            fontWeight: 900,
          }}
        >
          Hermes Call no WhatsApp
        </div>
      </div>

      {/* Mockup de Smartphone / Painel de Chamada IA Ao Vivo no WhatsApp (y: 235..605) */}
      <div
        style={{
          position: 'absolute',
          top: 235,
          left: 60,
          right: 60,
          transform: `scale(${panelIn})`,
          background: 'linear-gradient(165deg, rgba(11, 34, 21, 0.96), rgba(6, 18, 12, 0.98))',
          border: `3px solid ${CORES.marca}`,
          borderRadius: 28,
          padding: '20px 28px',
          boxShadow: '0 22px 48px rgba(0,0,0,0.65)',
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <div
              style={{
                width: 68,
                height: 68,
                borderRadius: 20,
                background: 'rgba(37, 211, 102, 0.2)',
                border: `3px solid ${CORES.marca}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transform: `scale(${callWavePulse})`,
                boxShadow: '0 0 22px rgba(37, 211, 102, 0.45)',
              }}
            >
              <IconeTelefoneIA cor={CORES.marca} tamanho={40} />
            </div>
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <span style={{color: '#A7F3D0', fontSize: 32, fontWeight: 800}}>
                CHAMADA WHATSAPP IA ATIVA
              </span>
              <span style={{color: '#FFFFFF', fontSize: 38, fontWeight: 900}}>
                Disparador Hermes Call
              </span>
            </div>
          </div>
          <div
            style={{
              background: 'rgba(37, 211, 102, 0.22)',
              border: `2px solid ${CORES.marca}`,
              borderRadius: 14,
              padding: '8px 18px',
              color: '#FFFFFF',
              fontSize: 32,
              fontWeight: 900,
            }}
          >
            AO VIVO
          </div>
        </div>

        {/* Ondas sonoras de IA simulando voz real e clonada em tempo real */}
        <div
          style={{
            background: 'rgba(0, 0, 0, 0.42)',
            borderRadius: 20,
            padding: '14px 22px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 20,
          }}
        >
          <span style={{color: '#FFFFFF', fontSize: 33, fontWeight: 800}}>
            Voz Real e Clonada
          </span>
          <div style={{display: 'flex', alignItems: 'center', gap: 8, height: 42}}>
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((bar) => {
              const h = 12 + Math.abs(Math.sin(frame * 0.32 + bar * 0.75)) * 28;
              return (
                <div
                  key={bar}
                  style={{
                    width: 10,
                    height: h,
                    borderRadius: 999,
                    background: bar % 2 === 0 ? CORES.marca : '#A7F3D0',
                  }}
                />
              );
            })}
          </div>
        </div>
      </div>

      {/* Pilha de 3 Cards de largura total (x: 60..1020, y: 530..1180) — sem quebra órfã em "sem parar" */}
      <div
        style={{
          position: 'absolute',
          top: 535,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
        }}
      >
        {etapas.map((etapa, idx) => {
          const appeared = absTime >= etapa.ini - 0.15;
          const nextIni = idx + 1 < etapas.length ? etapas[idx + 1].ini : 999;
          const isCurrent = absTime >= etapa.ini - 0.1 && absTime < nextIni;
          const cardSpring = spring({
            frame: Math.max(0, Math.round((absTime - (etapa.ini - 0.15)) * fps)),
            fps,
            config: {damping: 13},
          });

          return (
            <div
              key={etapa.num}
              style={{
                opacity: appeared ? cardSpring : 0,
                transform: `translateX(${(1 - cardSpring) * -50}px) scale(${isCurrent ? 1.03 : 0.98})`,
                background: isCurrent
                  ? 'rgba(10, 38, 22, 0.96)'
                  : 'rgba(10, 20, 15, 0.88)',
                border: `3px solid ${isCurrent ? CORES.marca : 'rgba(255,255,255,0.22)'}`,
                borderRadius: 24,
                padding: '18px 26px',
                boxShadow: isCurrent
                  ? '0 16px 36px rgba(37, 211, 102, 0.32)'
                  : '0 10px 24px rgba(0,0,0,0.45)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 18,
              }}
            >
              <div style={{display: 'flex', flexDirection: 'column', gap: 6, flex: 1}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <span
                    style={{
                      background: isCurrent ? CORES.marca : 'rgba(255,255,255,0.16)',
                      color: isCurrent ? '#121216' : '#FFFFFF',
                      fontSize: 32,
                      fontWeight: 900,
                      padding: '4px 16px',
                      borderRadius: 12,
                    }}
                  >
                    {etapa.num}
                  </span>
                  <span
                    style={{
                      color: '#FFFFFF',
                      fontSize: 38,
                      fontWeight: 900,
                      lineHeight: 1.15,
                    }}
                  >
                    {etapa.titulo}
                  </span>
                </div>
                <span
                  style={{
                    color: isCurrent ? '#A7F3D0' : '#E2E8F0',
                    fontSize: 34,
                    fontWeight: 700,
                    lineHeight: 1.2,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {etapa.sub}
                </span>
              </div>

              {/* Indicador ativo à direita de cada card */}
              <div
                style={{
                  padding: '8px 18px',
                  borderRadius: 14,
                  background: isCurrent ? 'rgba(37, 211, 102, 0.22)' : 'rgba(255,255,255,0.08)',
                  border: `2px solid ${isCurrent ? CORES.marca : 'rgba(255,255,255,0.18)'}`,
                  color: isCurrent ? CORES.marca : '#CBD5E1',
                  fontSize: 32,
                  fontWeight: 900,
                }}
              >
                {isCurrent ? 'ATIVO' : 'OK'}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 3: DONO — O RESULTADO (18.52s - 26.55s)
// "Hoje minha operação liga e vende sem parar com inteligência artificial, escalando no ritmo que preciso."
// ============================================================================
const Cena3Dono: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const absTime = 18.52 + frame / fps;
  const durFrames = Math.round((26.55 - 18.52) * fps);

  const enterOp = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitOp = interpolate(frame, [durFrames - 10, durFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Punch-in digital de 15% (primeiro plano) com deslocamento de 65px para baixo para respiro dos cards
  const videoScale = interpolate(frame, [0, durFrames], [1.18, 1.25], {
    extrapolateRight: 'clamp',
  });

  // Três marcos sincronizados na faixa superior:
  // 1: "liga e vende sem parar" (início da cena / 19.84s)
  // 2: "inteligência artificial" (21.75s -> ativo em q11)
  // 3: "escalando no ritmo que preciso" (23.45s -> ativo em q12)
  const pilares = [
    {titulo: 'Liga e Vende', sub: 'Sem parar', ini: 18.6, fim: 21.75},
    {titulo: 'IA 24h Ativa', sub: 'Voz natural', ini: 21.75, fim: 23.45},
    {titulo: 'Escala Total', sub: 'No seu ritmo', ini: 23.45, fim: 27.0},
  ];

  return (
    <AbsoluteFill style={{opacity: enterOp * exitOp, fontFamily}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `translateY(68px) scale(${videoScale})`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(6, 22, 13, 0.84) 0%, rgba(6, 22, 13, 0.0) 28%, rgba(6, 22, 13, 0.0) 68%, rgba(6, 22, 13, 0.8) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* FAIXA SUPERIOR (y: 154..385) — Grid horizontal de 3 pilares com ativação 1.05x sincronizada */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div
            style={{
              background: CORES.marca,
              color: '#121216',
              padding: '7px 24px',
              borderRadius: 999,
              fontSize: 33,
              fontWeight: 900,
              textTransform: 'uppercase',
            }}
          >
            O Resultado
          </div>
          <div
            style={{
              background: 'rgba(8, 22, 15, 0.9)',
              border: `2px solid ${CORES.marca}`,
              color: '#FFFFFF',
              padding: '7px 22px',
              borderRadius: 999,
              fontSize: 32,
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: 7,
                background: CORES.marca,
              }}
            />
            Operação Hermes Call
          </div>
        </div>

        {/* 3 Cards horizontais com destaque individual em verde + escala 1.05x na palavra exata */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            gap: 14,
          }}
        >
          {pilares.map((p, idx) => {
            const isCurrent = absTime >= p.ini && absTime < p.fim;
            const jaPassou = absTime >= p.fim;
            const pop = spring({
              frame: Math.max(0, Math.round((absTime - p.ini) * fps)),
              fps,
              config: {damping: 11, stiffness: 150},
            });
            const pulseCard = isCurrent ? 1 + 0.015 * Math.sin(frame * 0.35) : 1;
            const scaleVal = isCurrent
              ? (0.95 + 0.1 * pop) * pulseCard
              : jaPassou
              ? 0.96
              : 0.93;

            return (
              <div
                key={idx}
                style={{
                  minWidth: 0,
                  background: isCurrent
                    ? 'rgba(10, 44, 24, 0.98)'
                    : jaPassou
                    ? 'rgba(10, 28, 18, 0.88)'
                    : 'rgba(10, 18, 14, 0.76)',
                  border: isCurrent
                    ? `4px solid ${CORES.marca}`
                    : jaPassou
                    ? '2px solid rgba(37, 211, 102, 0.45)'
                    : '2px solid rgba(255,255,255,0.18)',
                  borderRadius: 20,
                  padding: '12px 12px',
                  transform: `scale(${scaleVal})`,
                  boxShadow: isCurrent
                    ? '0 14px 32px rgba(37, 211, 102, 0.42)'
                    : '0 8px 18px rgba(0,0,0,0.4)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  textAlign: 'center',
                  gap: 4,
                }}
              >
                <span
                  style={{
                    color: isCurrent ? CORES.marca : jaPassou ? '#A7F3D0' : '#CBD5E1',
                    fontSize: 32,
                    fontWeight: 900,
                    lineHeight: 1.12,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {p.titulo}
                </span>
                <span
                  style={{
                    color: '#FFFFFF',
                    fontSize: 32,
                    fontWeight: 700,
                    lineHeight: 1.12,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {p.sub}
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
// CENA 4: CARTÃO FINAL / CTA (26.20s - 30.10s)
// "Chame a gente no direct."
// ============================================================================
const Cena4Cartao: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.ceil((30.1 - 26.2) * fps);

  const enterOp = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const bgScale = interpolate(frame, [0, durFrames], [1.0, 1.28]);
  const bgPanY = interpolate(frame, [0, durFrames], [-40, 40]);
  const ringRotate = frame * 4.8;

  // Entrada escalonada (stagger) sem perder legibilidade do @ desde o início
  const logoIn = spring({frame: frame - 1, fps, config: {damping: 11, stiffness: 150}});
  const cardIn = spring({frame: Math.max(0, frame - 6), fps, config: {damping: 12, stiffness: 140}});
  const btnIn = spring({frame: Math.max(0, frame - 11), fps, config: {damping: 10, stiffness: 150}});
  const handleSlide = spring({frame: Math.max(0, frame - 3), fps, config: {damping: 12, stiffness: 160}});

  // Pulso contínuo (heartbeat/glow) no botão e no ícone de WhatsApp/Chamada até o último frame
  const pulse = 1 + 0.075 * Math.sin(frame * 0.38);
  const iconHeartbeat = 1 + 0.1 * Math.cos(frame * 0.38);
  const cardFloatY = Math.sin(frame * 0.22) * 10;
  const floatY = interpolate(frame, [0, durFrames], [-18, 20]);
  const glowX = interpolate(frame, [0, durFrames], [20, 80]);
  const glowY = interpolate(frame, [0, durFrames], [25, 72]);
  const shimmerX = interpolate((frame * 18) % 1100, [0, 1100], [-300, 950]);

  return (
    <AbsoluteFill style={{opacity: enterOp, fontFamily}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(6px)',
            transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(circle at ${glowX}% ${glowY}%, rgba(37, 211, 102, 0.42) 0%, rgba(8, 46, 22, 0.92) 68%)`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(37, 211, 102, 0.12) 2px, transparent 2px), linear-gradient(90deg, rgba(37, 211, 102, 0.12) 2px, transparent 2px)',
            backgroundSize: '72px 72px',
            transform: `translate(${(frame * 2.6) % 72}px, ${(frame * 2.6) % 72}px)`,
          }}
        />

        {/* Feixe de radar girando + anéis de ondas sonoras em rotação contínua */}
        <div
          style={{
            position: 'absolute',
            top: '46%',
            left: '50%',
            width: 900,
            height: 900,
            marginLeft: -450,
            marginTop: -450,
            borderRadius: '50%',
            background:
              'conic-gradient(from 0deg, rgba(37, 211, 102, 0.28) 0deg, rgba(37, 211, 102, 0.0) 90deg, rgba(37, 211, 102, 0.18) 180deg, rgba(37, 211, 102, 0.0) 360deg)',
            border: '4px dashed rgba(37, 211, 102, 0.38)',
            transform: `rotate(${ringRotate}deg) scale(${pulse})`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: '46%',
            left: '50%',
            width: 650,
            height: 650,
            marginLeft: -325,
            marginTop: -325,
            borderRadius: '50%',
            border: '3px dashed rgba(167, 243, 208, 0.32)',
            transform: `rotate(${-ringRotate * 1.4}deg) scale(${iconHeartbeat})`,
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo Centralizado dentro da Safe Zone (y: 185..1510) */}
      <div
        style={{
          position: 'absolute',
          top: 185,
          left: 60,
          right: 60,
          bottom: 330,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Identidade da Marca com pulso contínuo no ícone */}
        <div
          style={{
            transform: `scale(${logoIn}) translateY(${floatY}px)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <div
            style={{
              width: 136,
              height: 136,
              borderRadius: 38,
              background: 'rgba(10, 30, 18, 0.96)',
              border: `4px solid ${CORES.marca}`,
              boxShadow: `0 0 ${30 + 18 * Math.sin(frame * 0.38)}px rgba(37, 211, 102, 0.65)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transform: `scale(${iconHeartbeat})`,
            }}
          >
            <IconeTelefoneIA cor={CORES.marca} tamanho={76} />
          </div>

          <div
            style={{
              fontSize: 76,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -1,
              whiteSpace: 'nowrap',
              textShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}
          >
            Hermes Call
          </div>

          <div
            style={{
              background: 'rgba(10, 32, 19, 0.92)',
              border: `2px solid ${CORES.marca}`,
              borderRadius: 999,
              padding: '10px 28px',
              color: '#A7F3D0',
              fontSize: 34,
              fontWeight: 800,
              textTransform: 'uppercase',
            }}
          >
            Ligações WhatsApp com IA 24h
          </div>
        </div>

        {/* Card de Resumo do Produto com flutuação contínua */}
        <div
          style={{
            transform: `scale(${cardIn}) translateY(${cardFloatY}px)`,
            opacity: cardIn,
            width: '100%',
            background: 'rgba(8, 24, 15, 0.92)',
            border: `2px solid rgba(37, 211, 102, 0.45)`,
            borderRadius: 28,
            padding: '26px 34px',
            textAlign: 'center',
            boxShadow: '0 20px 45px rgba(0,0,0,0.6)',
          }}
        >
          <div
            style={{
              color: '#FFFFFF',
              fontSize: 40,
              fontWeight: 800,
              lineHeight: 1.26,
              textWrap: 'balance',
            }}
          >
            Atenda, ligue e venda pelo WhatsApp sem parar com voz real e clonada.
          </div>
        </div>

        {/* Botão CTA Principal + @arroba com alta visibilidade e opacidade total desde a entrada */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 22,
            width: '100%',
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              transform: `scale(${btnIn * pulse})`,
              background: CORES.marca,
              color: CORES.textoSobreMarca,
              padding: '26px 52px',
              borderRadius: 999,
              fontSize: 48,
              fontWeight: 900,
              textTransform: 'uppercase',
              letterSpacing: 1,
              boxShadow: `0 0 ${36 + 20 * Math.sin(frame * 0.38)}px rgba(37, 211, 102, 0.75)`,
              display: 'flex',
              alignItems: 'center',
              gap: 18,
            }}
          >
            <IconeTelefoneIA cor={CORES.textoSobreMarca} tamanho={46} />
            <span>CHAME NO DIRECT</span>
            {/* Brilho passando continuamente */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shimmerX,
                width: 140,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent)',
                transform: 'skewX(-20deg)',
              }}
            />
          </div>

          {/* Handle @inovarecom.ia com opacidade 100% imediata, branco puro (#FFFFFF) e fonte grande (52px) */}
          <div
            style={{
              transform: `translateY(${(1 - handleSlide) * 18}px) scale(${0.96 + 0.04 * pulse})`,
              opacity: 1,
              background: '#06150C',
              border: `3px solid ${CORES.marca}`,
              borderRadius: 999,
              padding: '16px 48px',
              color: '#FFFFFF',
              fontSize: 52,
              fontWeight: 900,
              letterSpacing: 0.5,
              boxShadow: '0 14px 34px rgba(0,0,0,0.8)',
            }}
          >
            @inovarecom.ia
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
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;

  // Barra de progresso fina no topo dentro da safe zone (y = 150)
  const progressoPct = (frame / durationInFrames) * 100;

  // Volume da trilha: 0.10 com fala, fade in no começo e fade out no final
  const trilhaVolume = interpolate(
    frame,
    [0, 15, durationInFrames - 25, durationInFrames],
    [0, 0.1, 0.1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundoEscuro, fontFamily}}>
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Cena 0: 0.00s - 4.74s */}
      <Sequence from={0} durationInFrames={Math.ceil(4.74 * fps)}>
        <Cena0Pergunta />
      </Sequence>

      {/* Cena 1: 4.39s - 12.42s */}
      <Sequence
        from={Math.round(4.39 * fps)}
        durationInFrames={Math.ceil((12.42 - 4.39) * fps)}
      >
        <Cena1Dono />
      </Sequence>

      {/* Cena 2: 12.07s - 18.87s */}
      <Sequence
        from={Math.round(12.07 * fps)}
        durationInFrames={Math.ceil((18.87 - 12.07) * fps)}
      >
        <Cena2Veo />
      </Sequence>

      {/* Cena 3: 18.52s - 26.55s */}
      <Sequence
        from={Math.round(18.52 * fps)}
        durationInFrames={Math.ceil((26.55 - 18.52) * fps)}
      >
        <Cena3Dono />
      </Sequence>

      {/* Cena 4: 26.20s - 30.10s */}
      <Sequence
        from={Math.round(26.2 * fps)}
        durationInFrames={Math.ceil((30.1 - 26.2) * fps)}
      >
        <Cena4Cartao />
      </Sequence>

      {/* Barra de progresso fina no topo da safe zone (y = 150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          background: 'rgba(255,255,255,0.18)',
          borderRadius: 999,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progressoPct}%`,
            height: '100%',
            background: CORES.marca,
          }}
        />
      </div>

      {/* Legenda Karaokê (oculta no cartão final t >= 26.15s) */}
      {t < 26.15 && (
        <Karaoke
          palavras={PALAVRAS_K}
          fontFamily={fontFamily}
          destaque={CORES.destaque}
          textoDestaque={CORES.textoSobreMarca}
          tamanho={46}
          base={355}
          maxLetras={26}
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
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(30.1 * 30)}
    />
  );
};
