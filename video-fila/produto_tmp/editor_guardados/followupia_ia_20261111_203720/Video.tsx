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
  marca: '#4ECDC4',
  apoio: '#111827',
  fundoEscuro: '#111827',
  destaque: '#4ECDC4',
  textoSobreMarca: '#121216',
  alerta: '#FF5A5F',
  verdeWhats: '#25D366',
};

const DURACAO_S = 33.41;
const FPS = 30;
const DURATION_FRAMES = Math.ceil(DURACAO_S * FPS);

const PALAVRAS: PalavraK[] = [
  {p: 'Esquece', ini: 0.15, fim: 0.75},
  {p: 'de', ini: 0.75, fim: 0.85},
  {p: 'cobrar', ini: 0.85, fim: 1.40},
  {p: 'quem', ini: 1.45, fim: 1.72, quebraAntes: true},
  {p: 'pediu', ini: 1.72, fim: 2.10},
  {p: 'orçamento', ini: 2.10, fim: 2.75},
  {p: 'e', ini: 2.80, fim: 3.05, quebraAntes: true},
  {p: 'não', ini: 3.05, fim: 3.50},
  {p: 'respondeu?', ini: 3.50, fim: 4.35, quebraApos: true},

  {p: 'Eu', ini: 4.388, fim: 4.828, quebraAntes: true},
  {p: 'atendia', ini: 4.828, fim: 5.348},
  {p: 'tantos', ini: 5.348, fim: 5.848},
  {p: 'clientes', ini: 5.848, fim: 6.568, quebraApos: true},
  {p: 'que', ini: 6.568, fim: 6.848},
  {p: 'esquecia', ini: 6.848, fim: 7.508},
  {p: 'de', ini: 7.508, fim: 7.748},
  {p: 'cobrar', ini: 7.748, fim: 8.148, quebraApos: true},
  {p: 'quem', ini: 8.148, fim: 8.388},
  {p: 'sumia,', ini: 8.388, fim: 9.188, quebraApos: true},
  {p: 'perdendo', ini: 9.548, fim: 9.868},
  {p: 'vendas', ini: 9.868, fim: 10.628},
  {p: 'todo', ini: 10.628, fim: 11.068},
  {p: 'dia.', ini: 11.068, fim: 11.348, quebraApos: true},

  {p: 'Com', ini: 12.549, fim: 12.705, quebraAntes: true},
  {p: 'o', ini: 12.717, fim: 12.741},
  {p: 'Follow-up', ini: 12.753, fim: 13.595},
  {p: 'IA,', ini: 13.607, fim: 14.953, quebraApos: true},
  {p: 'a', ini: 15.001, fim: 15.073},
  {p: 'inteligência', ini: 15.085, fim: 15.794},
  {p: 'faz', ini: 15.806, fim: 15.999, quebraApos: true},
  {p: 'o', ini: 16.011, fim: 16.131},
  {p: 'acompanhamento', ini: 16.143, fim: 16.84},
  {p: 'automático', ini: 16.852, fim: 17.525},
  {p: 'no', ini: 17.537, fim: 17.621},
  {p: 'WhatsApp,', ini: 17.633, fim: 18.27, quebraApos: true},
  {p: 'recupera', ini: 18.511, fim: 18.955},
  {p: 'leads', ini: 18.967, fim: 19.256},
  {p: 'inativos', ini: 19.268, fim: 19.857},
  {p: 'sozinha', ini: 19.869, fim: 20.41, quebraApos: true},
  {p: 'e', ini: 20.458, fim: 20.542},
  {p: 'nunca', ini: 20.554, fim: 20.842},
  {p: 'desiste.', ini: 20.854, fim: 21.431, quebraApos: true},

  {p: 'Hoje', ini: 21.876, fim: 22.656, quebraAntes: true},
  {p: 'eu', ini: 22.656, fim: 22.876},
  {p: 'não', ini: 22.876, fim: 23.176},
  {p: 'perco', ini: 23.176, fim: 23.536},
  {p: 'vendas', ini: 23.536, fim: 23.956, quebraApos: true},
  {p: 'por', ini: 23.956, fim: 24.236},
  {p: 'esquecimento', ini: 24.236, fim: 24.956, quebraApos: true},
  {p: 'e', ini: 24.956, fim: 25.536},
  {p: 'converto', ini: 25.536, fim: 26.096},
  {p: 'pelo', ini: 26.096, fim: 26.276},
  {p: 'WhatsApp', ini: 26.276, fim: 27.216, quebraApos: true},
  {p: 'sem', ini: 27.216, fim: 27.636},
  {p: 'depender', ini: 27.636, fim: 28.256},
  {p: 'de', ini: 28.256, fim: 28.436},
  {p: 'lembretes.', ini: 28.436, fim: 29.156, quebraApos: true},
];

// ============================================================================
// CENA 0 — PERGUNTA (0.00s -> 4.74s)
// Composição (a): Dono em câmera viva no gancho + Pergunta cinética + Card WhatsApp entrando aos 1.2s
// ============================================================================
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  // Ken Burns e movimento contínuo forte no fundo e no apresentador (>4% entre 20% e 80%)
  const bgScale = interpolate(frame, [0, 142], [1.0, 1.18], {extrapolateRight: 'clamp'});
  const bgX = interpolate(frame, [0, 142], [0, -55], {extrapolateRight: 'clamp'});
  const bgY = interpolate(frame, [0, 142], [0, -35], {extrapolateRight: 'clamp'});

  // Dono aparece já nos primeiros segundos olhando para a câmera com zoom ativo e headroom amplo
  const donoScale = interpolate(frame, [0, 142], [1.01, 1.08], {extrapolateRight: 'clamp'});
  const donoPanX = interpolate(frame, [0, 142], [18, -22], {extrapolateRight: 'clamp'});
  const donoPanY = interpolate(frame, [0, 142], [88, 76], {extrapolateRight: 'clamp'});

  const popHook = spring({frame, fps, config: {damping: 12, stiffness: 180}});
  const w1 = spring({frame, fps, config: {damping: 12, stiffness: 190}});
  const w2 = spring({frame: frame - Math.round(1.05 * fps), fps, config: {damping: 12, stiffness: 175}});
  const w3 = spring({frame: frame - Math.round(2.15 * fps), fps, config: {damping: 11, stiffness: 185}});

  // Card do WhatsApp surge dinamicamente em 1.2s (frame 36) para guiar o olhar e gerar movimento contínuo
  const cardWhatsIn = spring({
    frame: frame - Math.round(1.15 * fps),
    fps,
    config: {damping: 12, stiffness: 165},
  });
  const statusAlertIn = spring({
    frame: frame - Math.round(2.45 * fps),
    fps,
    config: {damping: 11, stiffness: 180},
  });

  const floatY = Math.sin(frame * 0.22) * 12;
  const floatX = Math.cos(frame * 0.18) * 8;
  const pulseAlert = 1 + Math.sin(frame * 0.30) * 0.045;
  const glowSweep = interpolate(frame, [0, 142], [-200, 1100]);

  // Transição rápida com zoom-in no corte final para a Cena 1
  const exitProgress = interpolate(frame, [130, 142], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const exitOpacity = 1 - exitProgress;
  const exitScale = 1 + exitProgress * 0.08;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: CORES.fundoEscuro,
        opacity: exitOpacity,
        transform: `scale(${exitScale})`,
      }}
    >
      {/* Fundo em movimento contínuo */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translate(${bgX}px, ${bgY}px)`,
            filter: 'blur(8px) brightness(0.32) contrast(1.15)',
          }}
        />
      </AbsoluteFill>

      {/* Vídeo do dono da empresa olhando para a câmera desde o frame 0 (com headroom amplo no topo) */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          startFrom={Math.round(3.2 * fps)}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transformOrigin: '50% 0%',
            transform: `translate(${donoPanX}px, ${donoPanY}px) scale(${donoScale})`,
            filter: 'contrast(1.06) saturate(1.05)',
          }}
        />
      </AbsoluteFill>

      {/* Vinheta superior e inferior para leitura perfeita sem cobrir o rosto do dono */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.82) 0%, rgba(17,24,39,0.18) 22%, rgba(17,24,39,0.05) 48%, rgba(17,24,39,0.78) 76%, rgba(17,24,39,0.94) 100%)',
        }}
      />

      {/* Pílula compacta + Pergunta Cinética no Topo (y=154..284) deixando 80px de headroom acima do cabelo */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          padding: '14px 24px',
          borderRadius: 24,
          backgroundColor: 'rgba(17, 24, 39, 0.90)',
          border: `2px solid ${t >= 2.35 ? CORES.alerta : CORES.marca}`,
          boxShadow: '0 16px 36px rgba(0,0,0,0.58)',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          transform: `translateY(${interpolate(popHook, [0, 1], [-24, 0])}px)`,
          overflow: 'hidden',
        }}
      >
        {/* Brilho dinâmico cruzando o card do topo */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            left: glowSweep,
            width: 180,
            background:
              'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(78,205,196,0.22) 50%, rgba(255,255,255,0) 100%)',
            transform: 'skewX(-20deg)',
            pointerEvents: 'none',
          }}
        />

        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: 999,
                backgroundColor: t >= 2.35 ? CORES.alerta : CORES.marca,
                transform: `scale(${pulseAlert})`,
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: t >= 2.35 ? '#FCA5A5' : CORES.marca,
              }}
            >
              {t >= 2.35 ? 'Esquece de cobrar quem pediu orçamento' : 'Vendas perdidas por esquecimento?'}
            </span>
          </div>
        </div>

        {/* Linha cinética principal (sempre 1 linha forte para nunca invadir o topo da cabeça) */}
        {t < 1.15 ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              transform: `scale(${interpolate(w1, [0, 1], [0.92, 1])})`,
            }}
          >
            <span style={{fontFamily, fontSize: 40, fontWeight: 900, color: '#FFFFFF', lineHeight: 1.1}}>
              Esquece de
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 40,
                fontWeight: 900,
                color: CORES.textoSobreMarca,
                backgroundColor: CORES.marca,
                padding: '2px 14px',
                borderRadius: 10,
                transform: `scale(${pulseAlert})`,
              }}
            >
              COBRAR?
            </span>
          </div>
        ) : t < 2.35 ? (
          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.1,
              transform: `translateX(${interpolate(w2, [0, 1], [20, 0])}px)`,
            }}
          >
            Quem pediu <span style={{color: CORES.marca, textDecoration: 'underline'}}>orçamento</span>
          </div>
        ) : (
          <div
            style={{
              display: 'inline-flex',
              alignSelf: 'flex-start',
              backgroundColor: CORES.alerta,
              padding: '3px 18px',
              borderRadius: 12,
              transform: `scale(${interpolate(w3, [0, 1], [0.9, 1]) * pulseAlert})`,
              boxShadow: '0 8px 20px rgba(255, 90, 95, 0.45)',
            }}
          >
            <span style={{fontFamily, fontSize: 38, fontWeight: 900, color: '#FFFFFF', lineHeight: 1.1}}>
              E NÃO RESPONDEU?
            </span>
          </div>
        )}
      </div>

      {/* Card do WhatsApp surgindo de forma dinâmica aos 1.2s na metade inferior (y=980..1310, abaixo do rosto) */}
      {t >= 1.15 && (
        <div
          style={{
            position: 'absolute',
            top: 985,
            left: 60,
            right: 60,
            transform: `translate(${floatX}px, ${interpolate(cardWhatsIn, [0, 1], [70, 0]) + floatY}px) scale(${interpolate(cardWhatsIn, [0, 1], [0.88, 1])})`,
            opacity: cardWhatsIn,
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 28,
            padding: '22px 28px',
            border: `2.5px solid ${t >= 2.45 ? CORES.alerta : CORES.marca}`,
            boxShadow: '0 22px 50px rgba(0,0,0,0.72)',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 26,
                  backgroundColor: CORES.verdeWhats,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#052E16',
                }}
              >
                W
              </div>
              <div>
                <div style={{fontFamily, fontSize: 38, fontWeight: 900, color: '#FFFFFF', lineHeight: 1.1}}>
                  Cliente · WhatsApp
                </div>
                <div style={{fontFamily, fontSize: 34, fontWeight: 700, color: '#CBD5E1', lineHeight: 1.15}}>
                  Simulação de orçamento
                </div>
              </div>
            </div>
            <div
              style={{
                backgroundColor: t >= 2.45 ? CORES.alerta : 'rgba(78, 205, 196, 0.22)',
                border: `2px solid ${t >= 2.45 ? '#FF9497' : CORES.marca}`,
                padding: '8px 20px',
                borderRadius: 999,
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                transform: `scale(${t >= 2.45 ? pulseAlert : 1})`,
              }}
            >
              {t >= 2.45 ? 'Vácuo!' : 'Enviado'}
            </div>
          </div>

          {/* Linha da Proposta com tipografia grande (>=36px) para leitura mobile imediata */}
          <div
            style={{
              backgroundColor: '#1E293B',
              borderRadius: 18,
              padding: '16px 22px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderLeft: `6px solid ${t >= 2.45 ? CORES.alerta : CORES.marca}`,
              transform: `scale(${1 + statusAlertIn * 0.015})`,
            }}
          >
            <span style={{fontFamily, fontSize: 36, fontWeight: 800, color: '#FFFFFF'}}>
              📄 Orçamento enviado
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 35,
                fontWeight: 900,
                color: t >= 2.45 ? '#FF9497' : '#38BDF8',
              }}
            >
              {t >= 2.45 ? 'Sem resposta' : '✓✓ Visualizado'}
            </span>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 1 — DONO: O PROBLEMA (4.39s -> 12.41s | duração 8.02s = 241 frames)
// Composição (h): Vídeo cheio dono_1.mp4 em plano médio com headroom amplo abaixo do card
// Card no topo (y=154..282) e topo do cabelo do apresentador em y>=355 (75px+ de respiro)
// ============================================================================
const Cena1DonoProblema: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tAbs = 4.39 + frame / fps;

  const enterOp = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
  // Whip-pan / zoom de saída nos últimos 10 frames para suavizar corte com a Cena 2
  const exitProgress = interpolate(frame, [230, 241], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const exitOp = 1 - exitProgress;
  const exitSlideX = interpolate(exitProgress, [0, 1], [0, -140]);
  const exitZoom = interpolate(exitProgress, [0, 1], [1, 1.12]);

  // 3 fases sincronizadas com a fala:
  // Fase 1 (4.39s - 6.84s): "Eu atendia tantos clientes"
  // Fase 2 (6.84s - 9.54s): "que esquecia de cobrar quem sumia,"
  // Fase 3 (9.54s - 12.41s): "perdendo vendas todo dia."
  const fase = tAbs < 6.84 ? 1 : tAbs < 9.54 ? 2 : 3;

  // Enquadramento em plano médio (1.0 -> 1.05) com transformOrigin no topo e offsetY +86px
  // Isso mantém o topo do cabelo em y ~ 358px, deixando ~78px de headroom abaixo do card (y=154..280)
  const zoomDono = interpolate(frame, [0, 241], [1.0, 1.05], {extrapolateRight: 'clamp'});
  const panXDono = interpolate(frame, [0, 241], [0, -16], {extrapolateRight: 'clamp'});
  const offsetYDono = 86;

  const popFase1 = spring({frame, fps, config: {damping: 14, stiffness: 150}});
  const popFase2 = spring({frame: frame - Math.round((6.84 - 4.39) * fps), fps, config: {damping: 14, stiffness: 160}});
  const popFase3 = spring({frame: frame - Math.round((9.54 - 4.39) * fps), fps, config: {damping: 13, stiffness: 170}});

  const activePop = fase === 1 ? popFase1 : fase === 2 ? popFase2 : popFase3;
  const pulse = 1 + Math.sin(frame * 0.22) * 0.022;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: CORES.fundoEscuro,
        opacity: enterOp * exitOp,
        transform: `translateX(${exitSlideX}px) scale(${exitZoom})`,
      }}
    >
      {/* Camada de preenchimento de teto desfocada para cobrir o offset superior sem borda preta */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: 'scale(1.2)',
            filter: 'blur(18px) brightness(0.75)',
          }}
        />
      </AbsoluteFill>

      {/* Vídeo principal do apresentador deslocado 86px para baixo com origem no topo */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transformOrigin: '50% 0%',
            transform: `translate(${panXDono}px, ${offsetYDono}px) scale(${zoomDono})`,
          }}
        />
      </AbsoluteFill>

      {/* Sombra suave apenas no topo e na base para leitura sem cobrir o rosto */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.78) 0%, rgba(17,24,39,0.12) 20%, rgba(17,24,39,0.0) 55%, rgba(17,24,39,0.65) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Card superior compacto (y=154..280) garantindo amplo headroom antes do topo da cabeça (y>=356) */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          backgroundColor: 'rgba(17, 24, 39, 0.90)',
          borderRadius: 24,
          padding: '14px 24px',
          border: `2px solid ${fase === 3 ? CORES.alerta : CORES.marca}`,
          boxShadow: '0 14px 32px rgba(0,0,0,0.52)',
          transform: `translateY(${interpolate(activePop, [0, 1], [-18, 0])}px) scale(${pulse})`,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              color: CORES.textoSobreMarca,
              backgroundColor: fase === 3 ? CORES.alerta : CORES.marca,
              padding: '3px 16px',
              borderRadius: 999,
              textTransform: 'uppercase',
            }}
          >
            O problema
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#CBD5E1',
            }}
          >
            {fase === 1 ? 'Rotina cheia' : fase === 2 ? 'Cliente sumia' : 'Impacto no caixa'}
          </span>
        </div>

        {fase === 1 && (
          <div style={{fontFamily, fontSize: 38, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.12}}>
            Tantos clientes que <span style={{color: CORES.marca}}>acumulava</span>
          </div>
        )}

        {fase === 2 && (
          <div style={{fontFamily, fontSize: 38, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.12}}>
            Esquecia de cobrar <span style={{color: '#FBBF24'}}>quem sumia</span>
          </div>
        )}

        {fase === 3 && (
          <div style={{fontFamily, fontSize: 40, fontWeight: 900, color: '#FFFFFF', lineHeight: 1.12}}>
            Perdendo vendas <span style={{color: '#FF7A7E', textDecoration: 'underline'}}>todo dia</span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 2 — VEO: COMO FUNCIONA (12.06s -> 22.15s | duração 10.09s = 303 frames)
// Composição (b) + (g): Smartphone realista com punch-in contínuo de câmera (14%) +
// transição direcional suave e conversa dinâmica com etapas sincronizadas
// ============================================================================
const Cena2ComoFunciona: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tAbs = 12.06 + frame / fps;

  // Transição direcional rápida (whip-pan + zoom-in + flash suave) na entrada da Cena 2
  const enterProgress = spring({frame, fps, config: {damping: 14, stiffness: 170}});
  const enterOp = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
  const whipSlideX = interpolate(enterProgress, [0, 1], [160, 0]);
  const whipBlurFlash = interpolate(frame, [0, 12], [0.45, 0], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(frame, [288, 303], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Vídeo de fundo mais claro e com movimento forte para não parecer estático
  const bgScale = interpolate(frame, [0, 303], [1.24, 1.44], {extrapolateRight: 'clamp'});
  const bgX = interpolate(frame, [0, 303], [150, 70], {extrapolateRight: 'clamp'});
  const bgY = interpolate(frame, [0, 303], [-140, -195], {extrapolateRight: 'clamp'});

  // Movimento de câmera contínuo (punch-in/zoom digital suave de 14% em direção à conversa)
  const cameraPunchIn = interpolate(frame, [0, 303], [0.95, 1.09], {extrapolateRight: 'clamp'});
  const cameraTiltY = interpolate(frame, [0, 303], [-6, 3], {extrapolateRight: 'clamp'});
  const cameraTiltX = interpolate(frame, [0, 303], [4, -1], {extrapolateRight: 'clamp'});
  const cameraPanY = interpolate(frame, [0, 303], [18, -22], {extrapolateRight: 'clamp'});

  const phoneIn = spring({frame: frame - 2, fps, config: {damping: 13, stiffness: 145}});
  const msgIaIn = spring({
    frame: frame - Math.round((15.05 - 12.06) * fps),
    fps,
    config: {damping: 12, stiffness: 165},
  });
  const msgLeadIn = spring({
    frame: frame - Math.round((18.45 - 12.06) * fps),
    fps,
    config: {damping: 12, stiffness: 165},
  });

  const step1 = tAbs >= 16.0;
  const step2 = tAbs >= 18.45;
  const step3 = tAbs >= 20.4;

  const s1Pop = spring({frame: frame - Math.round((16.0 - 12.06) * fps), fps, config: {damping: 13, stiffness: 165}});
  const s2Pop = spring({frame: frame - Math.round((18.45 - 12.06) * fps), fps, config: {damping: 13, stiffness: 165}});
  const s3Pop = spring({frame: frame - Math.round((20.4 - 12.06) * fps), fps, config: {damping: 13, stiffness: 165}});

  const floatPhone = Math.sin(frame * 0.16) * 6;
  const pulseCheck = 1 + Math.sin(frame * 0.28) * 0.05;
  const dot1 = 0.4 + Math.abs(Math.sin(frame * 0.35)) * 0.6;
  const dot2 = 0.4 + Math.abs(Math.sin(frame * 0.35 - 1.0)) * 0.6;
  const dot3 = 0.4 + Math.abs(Math.sin(frame * 0.35 - 2.0)) * 0.6;

  const etapas = [
    {ativo: step1, pop: s1Pop, texto: 'Acompanhamento automático no WhatsApp'},
    {ativo: step2, pop: s2Pop, texto: 'Recupera leads inativos sozinha'},
    {ativo: step3, pop: s3Pop, texto: 'Nunca desiste · A partir de R$ 199'},
  ];

  return (
    <AbsoluteFill
      style={{
        backgroundColor: CORES.fundoEscuro,
        opacity: enterOp * exitOp,
        transform: `translateX(${whipSlideX}px)`,
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
            transform: `scale(${bgScale}) translate(${bgX}px, ${bgY}px)`,
            filter: 'brightness(0.56) contrast(1.12)',
          }}
        />
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.82) 0%, rgba(17,24,39,0.40) 50%, rgba(17,24,39,0.85) 100%)',
        }}
      />

      {/* Flash luminoso suave de transição direcional para suavizar o contraste com a Cena 1 */}
      {whipBlurFlash > 0.01 && (
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(90deg, rgba(78,205,196,0.55) 0%, rgba(255,255,255,0.35) 50%, rgba(17,24,39,0) 100%)',
            opacity: whipBlurFlash,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Cabeçalho Como Funciona (y=158) */}
      <div
        style={{
          position: 'absolute',
          top: 158,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            backgroundColor: CORES.marca,
            color: CORES.textoSobreMarca,
            fontFamily,
            fontSize: 34,
            fontWeight: 900,
            padding: '8px 24px',
            borderRadius: 999,
            textTransform: 'uppercase',
          }}
        >
          Como funciona
        </div>
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: `2px solid ${CORES.marca}`,
            color: '#FFFFFF',
            fontFamily,
            fontSize: 34,
            fontWeight: 800,
            padding: '8px 22px',
            borderRadius: 999,
          }}
        >
          Follow-up IA
        </div>
      </div>

      {/* Mockup Realista de Smartphone com Punch-In Contínuo de Câmera (y=242..1290) */}
      <div
        style={{
          position: 'absolute',
          top: 242,
          left: 66,
          right: 66,
          backgroundColor: '#0B141A',
          borderRadius: 46,
          border: '6px solid #334155',
          boxShadow: '0 30px 70px rgba(0,0,0,0.78), 0 0 0 2px rgba(78,205,196,0.45)',
          padding: '18px 24px 24px 24px',
          transform: `translateY(${interpolate(phoneIn, [0, 1], [55, 0]) + cameraPanY + floatPhone}px) scale(${cameraPunchIn}) perspective(1000px) rotateY(${cameraTiltY}deg) rotateX(${cameraTiltX}deg)`,
          opacity: phoneIn,
          display: 'flex',
          flexDirection: 'column',
          gap: 15,
        }}
      >
        {/* Dynamic Island / Speaker do Smartphone */}
        <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', paddingBottom: 2}}>
          <div
            style={{
              width: 136,
              height: 16,
              borderRadius: 999,
              backgroundColor: '#020617',
              border: '1px solid rgba(255,255,255,0.12)',
            }}
          />
        </div>

        {/* Barra de Topo Nativa do WhatsApp */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#1F2C34',
            padding: '14px 20px',
            borderRadius: 24,
            borderBottom: `2px solid ${CORES.marca}`,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 50,
                height: 50,
                borderRadius: 25,
                backgroundColor: CORES.verdeWhats,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: '#052E16',
              }}
            >
              W
            </div>
            <div>
              <div style={{fontFamily, fontSize: 35, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.1}}>
                WhatsApp · Follow-up IA
              </div>
              <div style={{fontFamily, fontSize: 32, fontWeight: 700, color: CORES.marca, lineHeight: 1.15}}>
                ● IA ativa · Automático
              </div>
            </div>
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#E2E8F0',
              backgroundColor: 'rgba(255,255,255,0.12)',
              padding: '6px 16px',
              borderRadius: 12,
            }}
          >
            Simulação
          </span>
        </div>

        {/* Mensagem Anterior: Orçamento enviado */}
        <div
          style={{
            alignSelf: 'flex-start',
            backgroundColor: '#1E293B',
            borderLeft: `6px solid ${CORES.marca}`,
            borderRadius: 16,
            padding: '10px 18px',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
          }}
        >
          <span style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#E2E8F0'}}>
            📄 Orçamento enviado · Lead inativo
          </span>
        </div>

        {/* Mensagem 1: IA digitando de forma fluida e enviando follow-up automático */}
        <div
          style={{
            alignSelf: 'flex-start',
            maxWidth: '94%',
            backgroundColor: '#1F2C34',
            border: `2px solid ${CORES.marca}`,
            borderRadius: '22px 22px 22px 6px',
            padding: '16px 20px',
            transform: `scale(${tAbs >= 15.0 ? interpolate(msgIaIn, [0, 1], [0.92, 1]) : 1})`,
            boxShadow: '0 10px 25px rgba(0,0,0,0.45)',
          }}
        >
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6}}>
            <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: CORES.marca}}>
              Follow-up IA · Automático
            </span>
            {tAbs < 15.0 && (
              <div style={{display: 'flex', gap: 6, alignItems: 'center'}}>
                <div style={{width: 10, height: 10, borderRadius: 5, backgroundColor: CORES.marca, opacity: dot1}} />
                <div style={{width: 10, height: 10, borderRadius: 5, backgroundColor: CORES.marca, opacity: dot2}} />
                <div style={{width: 10, height: 10, borderRadius: 5, backgroundColor: CORES.marca, opacity: dot3}} />
              </div>
            )}
          </div>
          <div style={{fontFamily, fontSize: 34, fontWeight: 700, color: '#FFFFFF', lineHeight: 1.2}}>
            {tAbs < 15.0
              ? 'Digitando acompanhamento no WhatsApp...'
              : 'Oi! Conseguiu ver o orçamento? Posso te ajudar a fechar hoje?'}
          </div>
        </div>

        {/* Mensagem 2: Cliente recuperado (direita) */}
        {tAbs >= 18.2 && (
          <div
            style={{
              alignSelf: 'flex-end',
              maxWidth: '92%',
              backgroundColor: '#005C4B',
              border: '2px solid #34D399',
              borderRadius: '22px 22px 6px 22px',
              padding: '14px 20px',
              transform: `translateY(${interpolate(msgLeadIn, [0, 1], [22, 0])}px) scale(${interpolate(msgLeadIn, [0, 1], [0.88, 1])})`,
              opacity: msgLeadIn,
              boxShadow: '0 10px 24px rgba(0,0,0,0.45)',
            }}
          >
            <div style={{fontFamily, fontSize: 34, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.18}}>
              Oi! Estava na correria, vamos fechar sim! ✅
            </div>
          </div>
        )}

        {/* Tópicos entrando escalonados exatamente quando mencionados pela locução */}
        {step1 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
              paddingTop: 8,
              borderTop: '2px solid rgba(255,255,255,0.12)',
            }}
          >
            {etapas.map((item, idx) => {
              if (!item.ativo) return null;
              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    backgroundColor: 'rgba(17, 24, 39, 0.94)',
                    border: `2px solid ${CORES.marca}`,
                    borderRadius: 16,
                    padding: '10px 18px',
                    transform: `translateX(${interpolate(item.pop, [0, 1], [-40, 0])}px) scale(${interpolate(item.pop, [0, 1], [0.92, 1])})`,
                    opacity: item.pop,
                    boxShadow: '0 8px 20px rgba(0,0,0,0.4)',
                  }}
                >
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 20,
                      backgroundColor: CORES.marca,
                      color: CORES.textoSobreMarca,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 900,
                      flexShrink: 0,
                      transform: `scale(${pulseCheck})`,
                    }}
                  >
                    ✓
                  </div>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 33,
                      fontWeight: 800,
                      color: '#FFFFFF',
                      lineHeight: 1.12,
                    }}
                  >
                    {item.texto}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 3 — DONO: O RESULTADO (21.80s -> 29.81s | duração 8.01s = 240 frames)
// Composição (h): Reenquadramento com Punch-In Close-up (1.16x -> 1.22x) para diferenciar
// da Cena 1 + Offset vertical padronizado com amplo headroom abaixo do card superior
// ============================================================================
const Cena3DonoResultado: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tAbs = 21.8 + frame / fps;

  const enterOp = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(frame, [226, 240], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // 3 fases sincronizadas com a voz:
  // Fase 1 (21.80s - 25.50s): "Hoje eu não perco vendas por esquecimento"
  // Fase 2 (25.50s - 27.20s): "e converto pelo WhatsApp"
  // Fase 3 (27.20s - 29.81s): "sem depender de lembretes."
  const fase = tAbs < 25.5 ? 1 : tAbs < 27.2 ? 2 : 3;

  // Punch-in digital de 1.16x -> 1.22x (16% a 22% mais fechado que o plano médio 1.0x da Cena 1)
  // Com transformOrigin '50% 0%' e offsetY = 46px:
  // O topo do cabelo (y_raw=268) fica em y = 46 + 268*1.17 = 360px (80px abaixo do card superior que termina em y=280!)
  const baseZoom = fase === 1 ? 1.16 : fase === 2 ? 1.19 : 1.22;
  const driftZoom = interpolate(frame, [0, 240], [0, 0.03], {extrapolateRight: 'clamp'});
  const zoomDono = baseZoom + driftZoom;
  const panXDono = interpolate(frame, [0, 240], [-14, 14], {extrapolateRight: 'clamp'});
  const offsetYDono = 46;

  const pop1 = spring({frame, fps, config: {damping: 14, stiffness: 150}});
  const pop2 = spring({frame: frame - Math.round((25.5 - 21.8) * fps), fps, config: {damping: 14, stiffness: 160}});
  const pop3 = spring({frame: frame - Math.round((27.2 - 21.8) * fps), fps, config: {damping: 14, stiffness: 160}});

  const activePop = fase === 1 ? pop1 : fase === 2 ? pop2 : pop3;
  const pulse = 1 + Math.sin(frame * 0.24) * 0.022;
  const badgePulse = 1 + Math.sin(frame * 0.32) * 0.05;

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundoEscuro, opacity: enterOp * exitOp}}>
      {/* Preenchimento superior desfocado para evitar borda escura no topo */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: 'scale(1.2)',
            filter: 'blur(18px) brightness(0.75)',
          }}
        />
      </AbsoluteFill>

      {/* Vídeo do dono em Close-Up Punch-In (1.16x-1.25x) com headroom garantido em toda a Cena 3 */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transformOrigin: '50% 0%',
            transform: `translate(${panXDono}px, ${offsetYDono}px) scale(${zoomDono})`,
          }}
        />
      </AbsoluteFill>

      {/* Vinheta só nas extremidades para leitura limpa */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.78) 0%, rgba(17,24,39,0.12) 20%, rgba(17,24,39,0.0) 56%, rgba(17,24,39,0.68) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Card superior compacto (y=154..280) deixando 80px de margem livre acima do cabelo (y>=360) */}
      <div
        style={{
          position: 'absolute',
          top: 154,
          left: 60,
          right: 60,
          backgroundColor: 'rgba(17, 24, 39, 0.90)',
          borderRadius: 24,
          padding: '14px 24px',
          border: `2px solid ${CORES.marca}`,
          boxShadow: '0 14px 32px rgba(0,0,0,0.55)',
          transform: `translateY(${interpolate(activePop, [0, 1], [-18, 0])}px) scale(${pulse})`,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              color: CORES.textoSobreMarca,
              backgroundColor: CORES.marca,
              padding: '3px 16px',
              borderRadius: 999,
              textTransform: 'uppercase',
            }}
          >
            O resultado
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: CORES.marca,
              backgroundColor: 'rgba(78, 205, 196, 0.16)',
              border: `2px solid ${CORES.marca}`,
              padding: '3px 16px',
              borderRadius: 999,
              display: 'inline-block',
              transform: `scale(${badgePulse})`,
            }}
          >
            ✓ Follow-up IA ativo
          </span>
        </div>

        {fase === 1 && (
          <div style={{fontFamily, fontSize: 38, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.12}}>
            Não perco vendas por <span style={{color: CORES.marca}}>esquecimento</span>
          </div>
        )}

        {fase === 2 && (
          <div style={{fontFamily, fontSize: 38, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.12}}>
            Converto clientes pelo <span style={{color: CORES.verdeWhats}}>WhatsApp</span>
          </div>
        )}

        {fase === 3 && (
          <div style={{fontFamily, fontSize: 38, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.12}}>
            Sem depender de <span style={{color: CORES.marca}}>lembretes</span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 4 — CARTÃO FINAL (29.46s -> 33.41s | duração 3.95s = 119 frames)
// Composição (f): Cartão final com Ken Burns contínuo no card, pulso forte (1.0 -> 1.05),
// shimmer sweep gradient visível em loop e fundo dinâmico para zero frames congelados
// ============================================================================
const Cena4CartaoFinal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const enterOp = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const bgScale = interpolate(frame, [0, 119], [1.02, 1.24], {extrapolateRight: 'clamp'});
  const bgPanX = interpolate(frame, [0, 119], [35, -45], {extrapolateRight: 'clamp'});
  const bgPanY = interpolate(frame, [0, 119], [20, -25], {extrapolateRight: 'clamp'});

  const cardPop = spring({frame: frame - 2, fps, config: {damping: 13, stiffness: 150}});
  // Ken Burns contínuo e pronunciado no card principal até o último frame
  const cardKenBurns = interpolate(frame, [0, 119], [0.93, 1.06], {extrapolateRight: 'clamp'});
  const cardTiltY = interpolate(frame, [0, 119], [-4, 4], {extrapolateRight: 'clamp'});
  const cardShimmerX = interpolate((frame * 22) % 1100, [0, 1100], [-250, 980]);

  const btnPop = spring({frame: frame - 8, fps, config: {damping: 11, stiffness: 160}});
  // Pulso contínuo de escala (1.00 a 1.05) com frequência que muda claramente a cada segundo
  const btnPulse = 1.025 + Math.sin(frame * 0.21) * 0.035;
  const floatBadge = Math.sin(frame * 0.19) * 12;
  const arrowBounce = Math.sin(frame * 0.27) * 10;
  // Shimmer sweep gradient correndo em loop contínuo sobre o botão CHAME NO DIRECT
  const shineX = interpolate((frame * 26) % 1050, [0, 1050], [-220, 960]);
  const glowX = interpolate(frame, [0, 119], [25, 75], {extrapolateRight: 'clamp'});
  const glowY = interpolate(frame, [0, 119], [25, 65], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundoEscuro, opacity: enterOp}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translate(${bgPanX}px, ${bgPanY}px)`,
            filter: 'blur(8px) brightness(0.46) contrast(1.12)',
          }}
        />
      </AbsoluteFill>

      {/* Véu escuro da marca com foco luminoso em movimento contínuo */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${glowX}% ${glowY}%, rgba(78, 205, 196, 0.34) 0%, rgba(17, 24, 39, 0.88) 72%)`,
        }}
      />

      {/* Conteúdo centralizado dentro da Safe Zone (y=255..1440) */}
      <div
        style={{
          position: 'absolute',
          top: 255,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 34,
          transform: `translateY(${interpolate(cardPop, [0, 1], [40, 0])}px)`,
          opacity: cardPop,
        }}
      >
        {/* Pílula superior flutuante */}
        <div
          style={{
            backgroundColor: 'rgba(78, 205, 196, 0.20)',
            border: `2px solid ${CORES.marca}`,
            borderRadius: 999,
            padding: '10px 28px',
            transform: `translateY(${floatBadge}px) scale(${1 + Math.cos(frame * 0.19) * 0.025})`,
            boxShadow: '0 10px 26px rgba(0,0,0,0.45)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: CORES.marca,
              textTransform: 'uppercase',
              letterSpacing: 0.8,
            }}
          >
            Follow-up automático que vende
          </span>
        </div>

        {/* Card da Marca com Ken Burns contínuo e brilho diagonal */}
        <div
          style={{
            width: '100%',
            backgroundColor: 'rgba(17, 24, 39, 0.90)',
            border: `2.5px solid ${CORES.marca}`,
            borderRadius: 34,
            padding: '38px 34px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 20,
            transform: `scale(${interpolate(cardPop, [0, 1], [0.9, 1]) * cardKenBurns}) perspective(900px) rotateY(${cardTiltY}deg)`,
            boxShadow: '0 24px 60px rgba(0,0,0,0.65)',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Brilho sutil varrendo o card principal */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: cardShimmerX,
              width: 220,
              background:
                'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(78,205,196,0.18) 50%, rgba(255,255,255,0) 100%)',
              transform: 'skewX(-22deg)',
              pointerEvents: 'none',
            }}
          />

          <div
            style={{
              fontFamily,
              fontSize: 72,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.05,
              letterSpacing: -1,
            }}
          >
            Follow-up <span style={{color: CORES.marca}}>IA</span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 700,
              color: '#F1F5F9',
              lineHeight: 1.25,
              maxWidth: 820,
            }}
          >
            Recupera leads inativos e converte no WhatsApp sozinha.
          </div>

          <div
            style={{
              backgroundColor: 'rgba(78, 205, 196, 0.18)',
              border: `2px solid ${CORES.marca}`,
              borderRadius: 18,
              padding: '12px 26px',
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            A partir de R$ 199 · Nunca desiste
          </div>
        </div>

        {/* Botão CTA Principal Pulsante com Shimmer Sweep Contínuo (y ~ 940..1100) */}
        <div
          style={{
            marginTop: 18,
            width: '100%',
            backgroundColor: CORES.marca,
            borderRadius: 999,
            padding: '28px 36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            transform: `scale(${interpolate(btnPop, [0, 1], [0.85, 1]) * btnPulse})`,
            boxShadow: '0 22px 55px rgba(78, 205, 196, 0.55)',
            border: '3px solid #FFFFFF',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Shimmer sweep gradient intenso correndo em loop no botão */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: shineX,
              width: 260,
              background:
                'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.78) 50%, rgba(255,255,255,0) 100%)',
              transform: 'skewX(-20deg)',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              color: CORES.textoSobreMarca,
              letterSpacing: 0.8,
              textTransform: 'uppercase',
              position: 'relative',
            }}
          >
            CHAME NO DIRECT
          </span>
        </div>

        {/* @arroba com apontamento visual ativo dentro da safe zone (y ~ 1200) */}
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: `2px solid ${CORES.marca}`,
            borderRadius: 999,
            padding: '12px 36px',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            transform: `translateY(${arrowBounce}px) scale(${1 + Math.sin(frame * 0.27) * 0.025})`,
            boxShadow: '0 12px 30px rgba(78, 205, 196, 0.32)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 36,
              fontWeight: 900,
              color: CORES.marca,
            }}
          >
            👉
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            @followupia.ia
          </span>
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

  const progresso = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateRight: 'clamp',
  });

  const volumeTrilha = interpolate(
    frame,
    [0, 15, durationInFrames - 30, durationInFrames],
    [0.02, 0.1, 0.12, 0.02],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundoEscuro, fontFamily}}>
      {/* Áudio da narração completa e música de fundo */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volumeTrilha} />

      {/* CENA 0: 0.00s -> 4.74s */}
      <Sequence from={0} durationInFrames={Math.ceil(4.74 * fps)}>
        <Cena0Pergunta />
      </Sequence>

      {/* CENA 1: 4.39s -> 12.41s */}
      <Sequence
        from={Math.round(4.39 * fps)}
        durationInFrames={Math.ceil((12.41 - 4.39) * fps)}
      >
        <Cena1DonoProblema />
      </Sequence>

      {/* CENA 2: 12.06s -> 22.15s */}
      <Sequence
        from={Math.round(12.06 * fps)}
        durationInFrames={Math.ceil((22.15 - 12.06) * fps)}
      >
        <Cena2ComoFunciona />
      </Sequence>

      {/* CENA 3: 21.80s -> 29.81s */}
      <Sequence
        from={Math.round(21.8 * fps)}
        durationInFrames={Math.ceil((29.81 - 21.8) * fps)}
      >
        <Cena3DonoResultado />
      </Sequence>

      {/* CENA 4: 29.46s -> 33.41s */}
      <Sequence
        from={Math.round(29.46 * fps)}
        durationInFrames={durationInFrames - Math.round(29.46 * fps)}
      >
        <Cena4CartaoFinal />
      </Sequence>

      {/* Barra de progresso fina no topo da Safe Zone (y=150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          backgroundColor: 'rgba(255,255,255,0.18)',
          borderRadius: 999,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            backgroundColor: CORES.marca,
            borderRadius: 999,
          }}
        />
      </div>

      {/* Legenda Karaokê pronta (oculta no cartão final t >= 29.46s) */}
      {t < 29.46 && (
        <Karaoke
          palavras={PALAVRAS}
          fontFamily={fontFamily}
          destaque={CORES.destaque}
          textoDestaque={CORES.textoSobreMarca}
          tamanho={44}
          base={360}
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
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={DURATION_FRAMES}
    />
  );
};
