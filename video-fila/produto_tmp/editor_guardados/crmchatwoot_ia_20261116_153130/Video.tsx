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
  marca: '#1F93FF',
  marcaEscura: '#0B6bcb',
  apoio: '#111827',
  fundoEscuro: '#0B1120',
  destaque: '#1F93FF',
  texto: '#FFFFFF',
  alerta: '#EF4444',
  alertaBg: 'rgba(127, 29, 29, 0.94)',
  sucesso: '#10B981',
  cardEscuro: 'rgba(17, 24, 39, 0.94)',
};

const DURACAO_S = 30.88;
const FPS = 30;
const DURATION_FRAMES = Math.ceil(DURACAO_S * FPS);

const PALAVRAS_K: PalavraK[] = [
  // Cena 0 (0.00 - 4.83)
  {p: 'Sua', ini: 0.318, fim: 0.595, quebraAntes: true},
  {p: 'equipe', ini: 0.607, fim: 0.907},
  {p: 'atende', ini: 0.919, fim: 1.292},
  {p: 'sem', ini: 1.304, fim: 1.52, quebraLinha: true},
  {p: 'saber', ini: 1.532, fim: 1.917, quebraApos: true},
  {p: 'se', ini: 1.929, fim: 2.049, quebraAntes: true},
  {p: 'a', ini: 2.061, fim: 2.109},
  {p: 'pessoa', ini: 2.121, fim: 2.494},
  {p: 'já', ini: 2.506, fim: 2.674, quebraLinha: true},
  {p: 'é', ini: 2.686, fim: 2.746},
  {p: 'cliente?', ini: 2.758, fim: 3.359, quebraApos: true},

  // Cena 1 (4.48 - 12.20)
  {p: 'Minha', ini: 4.564, fim: 5.184, quebraAntes: true},
  {p: 'equipe', ini: 5.184, fim: 5.524},
  {p: 'atendia', ini: 5.524, fim: 5.924, quebraLinha: true},
  {p: 'no', ini: 5.924, fim: 6.144},
  {p: 'escuro,', ini: 6.144, fim: 6.924, quebraApos: true},
  {p: 'sem', ini: 7.304, fim: 7.444, quebraAntes: true},
  {p: 'saber', ini: 7.444, fim: 7.744},
  {p: 'se', ini: 7.744, fim: 7.884},
  {p: 'a', ini: 7.884, fim: 8.004},
  {p: 'pessoa', ini: 8.004, fim: 8.224, quebraLinha: true},
  {p: 'era', ini: 8.224, fim: 8.424},
  {p: 'cliente', ini: 8.424, fim: 8.924},
  {p: 'antiga,', ini: 8.924, fim: 9.624, quebraApos: true},
  {p: 'mas', ini: 10.064, fim: 10.444, quebraAntes: true},
  {p: 'resolvemos', ini: 10.444, fim: 11.144},
  {p: 'isso.', ini: 11.144, fim: 11.404, quebraApos: true},

  // Cena 2 (11.85 - 19.45)
  {p: 'Nosso', ini: 12.347, fim: 12.648, quebraAntes: true},
  {p: 'CRM', ini: 12.66, fim: 13.273},
  {p: 'feito', ini: 13.285, fim: 13.621, quebraLinha: true},
  {p: 'a', ini: 13.633, fim: 13.669},
  {p: 'partir', ini: 13.681, fim: 14.03},
  {p: 'do', ini: 14.042, fim: 14.138},
  {p: 'Chatwoot', ini: 14.15, fim: 14.739, quebraApos: true},
  {p: 'reúne', ini: 14.751, fim: 15.136, quebraAntes: true},
  {p: 'o', ini: 15.148, fim: 15.196},
  {p: 'histórico', ini: 15.208, fim: 15.821},
  {p: 'e', ini: 15.857, fim: 15.929, quebraLinha: true},
  {p: 'os', ini: 15.941, fim: 16.061},
  {p: 'tickets', ini: 16.073, fim: 16.47},
  {p: 'anteriores', ini: 16.482, fim: 17.143, quebraApos: true},
  {p: 'junto', ini: 17.155, fim: 17.407, quebraAntes: true},
  {p: 'da', ini: 17.419, fim: 17.527},
  {p: 'conversa.', ini: 17.539, fim: 18.164, quebraApos: true},

  // Cena 3 (19.10 - 27.28)
  {p: 'Hoje', ini: 19.918, fim: 20.558, quebraAntes: true},
  {p: 'eu', ini: 20.558, fim: 20.778},
  {p: 'vejo', ini: 20.778, fim: 21.038},
  {p: 'quem', ini: 21.038, fim: 21.198, quebraLinha: true},
  {p: 'já', ini: 21.198, fim: 21.398},
  {p: 'é', ini: 21.398, fim: 21.538},
  {p: 'cliente', ini: 21.538, fim: 21.898},
  {p: 'na', ini: 21.898, fim: 22.158},
  {p: 'hora,', ini: 22.158, fim: 22.458, quebraApos: true},
  {p: 'com', ini: 22.938, fim: 23.158, quebraAntes: true},
  {p: 'dados', ini: 23.158, fim: 23.618},
  {p: 'e', ini: 23.618, fim: 24.018},
  {p: 'chamados', ini: 24.018, fim: 24.358, quebraLinha: true},
  {p: 'centralizados', ini: 24.358, fim: 25.698, quebraApos: true},
  {p: 'para', ini: 25.698, fim: 26.218, quebraAntes: true},
  {p: 'atender', ini: 26.218, fim: 26.558},
  {p: 'melhor.', ini: 26.558, fim: 26.858, quebraApos: true},
];

// ============================================================================
// CENA 0 — PERGUNTA / GANCHO (0.00s -> 4.83s)
// "Sua equipe atende sem saber se a pessoa já é cliente?"
// ============================================================================
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  // Movimento contínuo de câmera no fundo (1.0 -> 1.10)
  const bgScale = interpolate(frame, [0, 145], [1.0, 1.1], {extrapolateRight: 'clamp'});
  const bgX = interpolate(frame, [0, 145], [0, -24], {extrapolateRight: 'clamp'});
  const bgY = interpolate(frame, [0, 145], [0, -18], {extrapolateRight: 'clamp'});

  // Saída suave no final da cena (4.48s a 4.83s)
  const exitOpacity = interpolate(t, [4.48, 4.8], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitScale = interpolate(t, [4.48, 4.8], [1, 0.94], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Entradas sincronizadas com a voz
  const spTopo = spring({frame: frame - 2, fps, config: {damping: 14, stiffness: 160}});
  const spL1 = spring({frame: frame - Math.round(0.25 * fps), fps, config: {damping: 13, stiffness: 170}});
  const spL2 = spring({frame: frame - Math.round(1.25 * fps), fps, config: {damping: 12, stiffness: 180}});
  const spL3 = spring({frame: frame - Math.round(2.1 * fps), fps, config: {damping: 13, stiffness: 170}});

  // Card de dor no centro (entra em 0.35s e evolui ao longo da fala)
  const spCard = spring({frame: frame - Math.round(0.35 * fps), fps, config: {damping: 14, stiffness: 150}});
  const spTag1 = spring({frame: frame - Math.round(1.3 * fps), fps, config: {damping: 14, stiffness: 160}});
  const spTag2 = spring({frame: frame - Math.round(2.45 * fps), fps, config: {damping: 14, stiffness: 160}});

  const floatY = Math.sin(frame * 0.12) * 8;
  const pulseAlert = 1 + Math.sin(frame * 0.22) * 0.03;

  return (
    <AbsoluteFill style={{opacity: exitOpacity, backgroundColor: CORES.fundoEscuro}}>
      {/* Foto de fundo em movimento contínuo */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translate(${bgX}px, ${bgY}px)`,
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.45) contrast(1.12)',
          }}
        />
      </AbsoluteFill>

      {/* Gradiente de proteção de leitura no topo e na base */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(11,17,32,0.92) 0%, rgba(11,17,32,0.55) 45%, rgba(11,17,32,0.88) 100%)',
        }}
      />

      <AbsoluteFill
        style={{
          transform: `scale(${exitScale})`,
          fontFamily,
        }}
      >
        {/* ZONA TOPO (y=175..520): Gancho + Pergunta Cinética Sincronizada */}
        <div
          style={{
            position: 'absolute',
            top: 175,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 18,
          }}
        >
          {/* Selo Gancho da Tela */}
          <div
            style={{
              transform: `scale(${spTopo})`,
              background: CORES.alertaBg,
              border: '2px solid #F87171',
              borderRadius: 999,
              padding: '10px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              boxShadow: '0 10px 25px rgba(239,68,68,0.35)',
            }}
          >
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: 99,
                background: '#F87171',
                transform: `scale(${pulseAlert})`,
              }}
            />
            <span
              style={{
                color: '#FFFFFF',
                fontSize: 34,
                fontWeight: 800,
                letterSpacing: 0.5,
                textTransform: 'uppercase',
              }}
            >
              Quem é esse cliente?
            </span>
          </div>

          {/* Título Principal = A própria pergunta da fala */}
          <div
            style={{
              background: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid rgba(255,255,255,0.16)',
              borderRadius: 28,
              padding: '24px 32px',
              width: '100%',
              boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <div
              style={{
                opacity: spL1,
                transform: `translateY(${interpolate(spL1, [0, 1], [24, 0])}px)`,
                color: '#FFFFFF',
                fontSize: 50,
                fontWeight: 900,
                lineHeight: 1.15,
                textAlign: 'center',
                textTransform: 'uppercase',
              }}
            >
              Sua equipe atende
            </div>

            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                alignItems: 'center',
                gap: 14,
              }}
            >
              <span
                style={{
                  opacity: spL2,
                  transform: `scale(${interpolate(spL2, [0, 1], [0.8, 1])})`,
                  background: '#EF4444',
                  color: '#FFFFFF',
                  fontSize: 52,
                  fontWeight: 900,
                  padding: '4px 20px',
                  borderRadius: 14,
                  textTransform: 'uppercase',
                }}
              >
                sem saber
              </span>
              <span
                style={{
                  opacity: spL3,
                  transform: `translateY(${interpolate(spL3, [0, 1], [20, 0])}px)`,
                  color: '#93C5FD',
                  fontSize: 50,
                  fontWeight: 900,
                  textTransform: 'uppercase',
                }}
              >
                se já é cliente?
              </span>
            </div>
          </div>
        </div>

        {/* ZONA CENTRAL (y=680..1240): Simulador Visual de Atendimento às Cegas */}
        <div
          style={{
            position: 'absolute',
            top: 700,
            left: 70,
            right: 70,
            transform: `translateY(${floatY}px) scale(${spCard})`,
            opacity: spCard,
            background: 'rgba(15, 23, 42, 0.95)',
            border: '3px solid rgba(239, 68, 68, 0.7)',
            borderRadius: 32,
            padding: '30px 34px',
            boxShadow: '0 28px 60px rgba(0,0,0,0.65)',
            display: 'flex',
            flexDirection: 'column',
            gap: 24,
          }}
        >
          {/* Cabeçalho do chamado sem dados */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(255,255,255,0.12)',
              paddingBottom: 20,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
              <div
                style={{
                  width: 84,
                  height: 84,
                  borderRadius: 42,
                  background: 'rgba(239, 68, 68, 0.22)',
                  border: '3px solid #EF4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FCA5A5',
                  fontSize: 48,
                  fontWeight: 900,
                  transform: `scale(${pulseAlert})`,
                }}
              >
                ?
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
                <span style={{color: '#FFFFFF', fontSize: 38, fontWeight: 800}}>
                  Novo Contato Recebido
                </span>
                <span style={{color: '#FCA5A5', fontSize: 33, fontWeight: 700}}>
                  Histórico oculto no atendimento
                </span>
              </div>
            </div>
          </div>

          {/* Pílulas de dúvida que acendem com a fala */}
          <div style={{display: 'flex', flexDirection: 'column', gap: 16}}>
            <div
              style={{
                opacity: spTag1,
                transform: `translateX(${interpolate(spTag1, [0, 1], [-40, 0])}px)`,
                background: 'rgba(239, 68, 68, 0.18)',
                border: '2px solid rgba(248, 113, 113, 0.5)',
                borderRadius: 20,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{color: '#E2E8F0', fontSize: 34, fontWeight: 700}}>
                Cadastro no CRM:
              </span>
              <span
                style={{
                  background: '#EF4444',
                  color: '#FFFFFF',
                  fontSize: 33,
                  fontWeight: 800,
                  padding: '6px 18px',
                  borderRadius: 12,
                }}
              >
                SEM INFORMAÇÃO
              </span>
            </div>

            <div
              style={{
                opacity: spTag2,
                transform: `translateX(${interpolate(spTag2, [0, 1], [40, 0])}px)`,
                background: 'rgba(31, 147, 255, 0.16)',
                border: '2px solid rgba(31, 147, 255, 0.55)',
                borderRadius: 20,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{color: '#E2E8F0', fontSize: 34, fontWeight: 700}}>
                Já é cliente ou novo?
              </span>
              <span
                style={{
                  background: CORES.marca,
                  color: '#FFFFFF',
                  fontSize: 33,
                  fontWeight: 800,
                  padding: '6px 18px',
                  borderRadius: 12,
                }}
              >
                NÃO IDENTIFICADO
              </span>
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 1 — DONO 1: O PROBLEMA E A VIRADA (4.48s -> 12.20s)
// "Minha equipe atendia no escuro, sem saber se a pessoa era cliente antiga, mas resolvemos isso."
// ============================================================================
const Cena1DonoProblema: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((12.2 - 4.48) * fps);
  const tAbs = 4.48 + frame / fps;

  // Transição de entrada e saída
  const enterOp = interpolate(frame, [0, 9], [0, 1], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(frame, [durFrames - 9, durFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Zoom suave contínuo no vídeo do dono (1.0 -> 1.06)
  const videoScale = interpolate(frame, [0, durFrames], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Momento da virada positiva: "mas resolvemos isso" começa em tAbs = 10.064s
  const viradaFrame = Math.round((10.064 - 4.48) * fps);
  const dorExit = interpolate(frame, [viradaFrame - 4, viradaFrame + 2], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const solucaoEnter = spring({
    frame: frame - viradaFrame,
    fps,
    config: {damping: 13, stiffness: 170},
  });

  // Entradas das frases de dor no topo
  const spDor1 = spring({
    frame: frame - Math.round((4.56 - 4.48) * fps),
    fps,
    config: {damping: 14, stiffness: 160},
  });
  const spDor2 = spring({
    frame: frame - Math.round((7.3 - 4.48) * fps),
    fps,
    config: {damping: 14, stiffness: 160},
  });

  const floatY = Math.sin(frame * 0.1) * 5;

  return (
    <AbsoluteFill style={{opacity: enterOp * exitOp, backgroundColor: '#000'}}>
      <AbsoluteFill style={{transform: `scale(${videoScale})`}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Vinheta suave APENAS no topo e na base para não escurecer o rosto do dono */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(11,17,32,0.82) 0%, rgba(11,17,32,0.0) 26%, rgba(11,17,32,0.0) 70%, rgba(11,17,32,0.85) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* ZONA TOPO (y=165..425) — Rosto do dono livre abaixo de y=430 */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          fontFamily,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* BLOCO DE DOR (4.48s até 10.06s) — desmonta imediatamente na palavra "mas" */}
        {tAbs < 10.15 && (
          <div
            style={{
              opacity: dorExit * spDor1,
              transform: `scale(${interpolate(dorExit, [0, 1], [0.9, 1])})`,
              background: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid #EF4444',
              borderRadius: 26,
              padding: '20px 28px',
              boxShadow: '0 18px 40px rgba(0,0,0,0.55)',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
              <span
                style={{
                  background: '#EF4444',
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 800,
                  padding: '5px 18px',
                  borderRadius: 999,
                  textTransform: 'uppercase',
                }}
              >
                O problema
              </span>
              <span style={{color: '#FCA5A5', fontSize: 34, fontWeight: 800}}>
                Atendimento no escuro
              </span>
            </div>

            <div
              style={{
                color: '#FFFFFF',
                fontSize: 40,
                fontWeight: 900,
                lineHeight: 1.18,
              }}
            >
              {tAbs < 7.3
                ? 'Equipe atendia sem visibilidade'
                : 'Sem saber se era cliente antiga'}
            </div>

            {tAbs >= 7.25 && (
              <div
                style={{
                  opacity: spDor2,
                  transform: `translateY(${interpolate(spDor2, [0, 1], [12, 0])}px)`,
                  background: 'rgba(239, 68, 68, 0.2)',
                  borderRadius: 14,
                  padding: '8px 18px',
                  color: '#FECACA',
                  fontSize: 32,
                  fontWeight: 700,
                }}
              >
                Histórico desconectado do atendimento
              </div>
            )}
          </div>
        )}

        {/* BLOCO DE VIRADA POSITIVA (10.06s até 12.20s): "mas resolvemos isso" */}
        {tAbs >= 10.02 && (
          <div
            style={{
              opacity: solucaoEnter,
              transform: `scale(${interpolate(solucaoEnter, [0, 1], [0.88, 1])})`,
              background: 'rgba(15, 23, 42, 0.95)',
              border: `3px solid ${CORES.marca}`,
              borderRadius: 26,
              padding: '22px 30px',
              boxShadow: '0 18px 45px rgba(31, 147, 255, 0.35)',
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span
                style={{
                  background: CORES.marca,
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 800,
                  padding: '6px 20px',
                  borderRadius: 999,
                  textTransform: 'uppercase',
                }}
              >
                Solução
              </span>
              <span style={{color: '#93C5FD', fontSize: 34, fontWeight: 800}}>
                CRM Chatwoot IA
              </span>
            </div>
            <div
              style={{
                color: '#FFFFFF',
                fontSize: 44,
                fontWeight: 900,
                lineHeight: 1.15,
              }}
            >
              Resolvemos isso no atendimento!
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 2 — COMO FUNCIONA / CONVERSA + CRM (11.85s -> 19.45s)
// "Nosso CRM feito a partir do Chatwoot reúne o histórico e os tickets anteriores junto da conversa."
// ============================================================================
const Cena2ConversaCRM: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((19.45 - 11.85) * fps);
  const tAbs = 11.85 + frame / fps;

  const enterOp = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(frame, [durFrames - 10, durFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Fundo img_2.jpg em movimento contínuo
  const bgScale = interpolate(frame, [0, durFrames], [1.02, 1.12], {extrapolateRight: 'clamp'});
  const bgX = interpolate(frame, [0, durFrames], [0, 22], {extrapolateRight: 'clamp'});

  // Entrada sincronizada do cabeçalho e do container junto com a 1ª mensagem (sem caixa vazia)
  const spHeader = spring({frame: frame - 3, fps, config: {damping: 14, stiffness: 160}});
  const spMockup = spring({frame: frame - 6, fps, config: {damping: 14, stiffness: 150}});

  // Mensagens entrando uma a uma ao longo da cena
  const spMsg1 = spring({
    frame: frame - Math.round((12.35 - 11.85) * fps),
    fps,
    config: {damping: 14, stiffness: 170},
  });
  const spMsg2 = spring({
    frame: frame - Math.round((14.15 - 11.85) * fps),
    fps,
    config: {damping: 14, stiffness: 170},
  });
  const spHistorico = spring({
    frame: frame - Math.round((15.2 - 11.85) * fps),
    fps,
    config: {damping: 13, stiffness: 180},
  });
  const spMsg3 = spring({
    frame: frame - Math.round((15.85 - 11.85) * fps),
    fps,
    config: {damping: 14, stiffness: 170},
  });
  const spTickets = spring({
    frame: frame - Math.round((16.07 - 11.85) * fps),
    fps,
    config: {damping: 13, stiffness: 180},
  });
  const spMsg4 = spring({
    frame: frame - Math.round((17.15 - 11.85) * fps),
    fps,
    config: {damping: 14, stiffness: 170},
  });

  // Movimento contínuo de inclinação leve e flutuação
  const floatY = Math.sin(frame * 0.1) * 6;
  const tiltY = Math.sin(frame * 0.07) * 2.2;

  // Scroll suave quando a 4ª mensagem entra para manter tudo legível e com itens inteiros
  const chatScrollY = interpolate(
    frame,
    [Math.round((16.8 - 11.85) * fps), Math.round((17.5 - 11.85) * fps)],
    [0, -135],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{opacity: enterOp * exitOp, backgroundColor: CORES.fundoEscuro}}>
      <AbsoluteFill style={{transform: `scale(${bgScale}) translateX(${bgX}px)`}}>
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.32) blur(4px)',
          }}
        />
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(11,17,32,0.92) 0%, rgba(11,17,32,0.72) 50%, rgba(11,17,32,0.94) 100%)',
        }}
      />

      <AbsoluteFill style={{fontFamily}}>
        {/* TOPO (y=165..345): Rótulo Como Funciona + Título + Selo Simulação */}
        <div
          style={{
            position: 'absolute',
            top: 165,
            left: 60,
            right: 60,
            opacity: spHeader,
            transform: `translateY(${interpolate(spHeader, [0, 1], [-20, 0])}px)`,
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
            <span
              style={{
                background: CORES.marca,
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                padding: '6px 22px',
                borderRadius: 999,
                textTransform: 'uppercase',
              }}
            >
              Como funciona
            </span>
            <span
              style={{
                background: 'rgba(17, 24, 39, 0.9)',
                border: '2px solid rgba(255,255,255,0.22)',
                color: '#E2E8F0',
                fontSize: 32,
                fontWeight: 700,
                padding: '6px 20px',
                borderRadius: 999,
              }}
            >
              Simulação
            </span>
          </div>

          <div
            style={{
              color: '#FFFFFF',
              fontSize: 44,
              fontWeight: 900,
              lineHeight: 1.15,
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
            }}
          >
            CRM a partir do Chatwoot
          </div>
        </div>

        {/* MOCKUP INTEGRADO CRM + CONVERSA (y=360..1260, altura 900px >= 820px) */}
        <div
          style={{
            position: 'absolute',
            top: 360,
            left: 60,
            right: 60,
            height: 900,
            opacity: spMockup,
            transform: `perspective(1200px) rotateY(${tiltY}deg) translateY(${floatY}px) scale(${interpolate(
              spMockup,
              [0, 1],
              [0.92, 1]
            )})`,
            background: '#0F172A',
            border: `3px solid ${CORES.marca}`,
            borderRadius: 34,
            overflow: 'hidden',
            boxShadow: '0 30px 70px rgba(0,0,0,0.75)',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Barra Superior do CRM Chatwoot */}
          <div
            style={{
              background: '#1E293B',
              padding: '20px 28px',
              borderBottom: '2px solid rgba(255,255,255,0.1)',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: 28,
                    background: CORES.marca,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontSize: 32,
                    fontWeight: 900,
                  }}
                >
                  C
                </div>
                <div>
                  <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 800}}>
                    Cliente Identificado
                  </div>
                  <div style={{color: '#93C5FD', fontSize: 32, fontWeight: 700}}>
                    CRM Chatwoot IA
                  </div>
                </div>
              </div>
            </div>

            {/* Pílulas de Histórico e Tickets Anteriores que acendem na palavra exata */}
            <div style={{display: 'flex', gap: 14, flexWrap: 'wrap'}}>
              <div
                style={{
                  background: tAbs >= 15.2 ? CORES.marca : 'rgba(255,255,255,0.08)',
                  border: `2px solid ${tAbs >= 15.2 ? '#60A5FA' : 'rgba(255,255,255,0.18)'}`,
                  borderRadius: 14,
                  padding: '8px 18px',
                  transform: `scale(${tAbs >= 15.2 ? interpolate(spHistorico, [0, 1], [0.9, 1]) : 1})`,
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 800,
                }}
              >
                ✓ Histórico do cliente
              </div>
              <div
                style={{
                  background: tAbs >= 16.07 ? '#10B981' : 'rgba(255,255,255,0.08)',
                  border: `2px solid ${tAbs >= 16.07 ? '#34D399' : 'rgba(255,255,255,0.18)'}`,
                  borderRadius: 14,
                  padding: '8px 18px',
                  transform: `scale(${tAbs >= 16.07 ? interpolate(spTickets, [0, 1], [0.9, 1]) : 1})`,
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 800,
                }}
              >
                ✓ Tickets anteriores
              </div>
            </div>
          </div>

          {/* Área de Mensagens da Conversa */}
          <div
            style={{
              flex: 1,
              padding: '24px 26px',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 18,
                transform: `translateY(${chatScrollY}px)`,
              }}
            >
              {/* Msg 1: Cliente */}
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '86%',
                  opacity: spMsg1,
                  transform: `translateY(${interpolate(spMsg1, [0, 1], [24, 0])}px)`,
                  background: '#1E293B',
                  border: '2px solid rgba(255,255,255,0.15)',
                  borderRadius: '24px 24px 24px 6px',
                  padding: '16px 22px',
                  color: '#FFFFFF',
                  fontSize: 33,
                  fontWeight: 700,
                  lineHeight: 1.25,
                }}
              >
                Olá, preciso revisar meu último chamado.
              </div>

              {/* Digitando antes da Msg 2 */}
              {tAbs >= 13.4 && tAbs < 14.15 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    background: 'rgba(31, 147, 255, 0.25)',
                    border: `2px solid ${CORES.marca}`,
                    borderRadius: 20,
                    padding: '10px 22px',
                    color: '#93C5FD',
                    fontSize: 32,
                    fontWeight: 700,
                  }}
                >
                  digitando...
                </div>
              )}

              {/* Msg 2: Empresa */}
              {tAbs >= 14.15 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '88%',
                    opacity: spMsg2,
                    transform: `translateY(${interpolate(spMsg2, [0, 1], [24, 0])}px)`,
                    background: CORES.marcaEscura,
                    border: '2px solid #60A5FA',
                    borderRadius: '24px 24px 6px 24px',
                    padding: '16px 22px',
                    color: '#FFFFFF',
                    fontSize: 33,
                    fontWeight: 700,
                    lineHeight: 1.25,
                  }}
                >
                  Olá! Já vi no seu histórico que você é nosso cliente e localizei seu ticket.
                </div>
              )}

              {/* Msg 3: Cliente */}
              {tAbs >= 15.85 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '86%',
                    opacity: spMsg3,
                    transform: `translateY(${interpolate(spMsg3, [0, 1], [24, 0])}px)`,
                    background: '#1E293B',
                    border: '2px solid rgba(255,255,255,0.15)',
                    borderRadius: '24px 24px 24px 6px',
                    padding: '16px 22px',
                    color: '#FFFFFF',
                    fontSize: 33,
                    fontWeight: 700,
                    lineHeight: 1.25,
                  }}
                >
                  Ótimo, não preciso explicar tudo de novo.
                </div>
              )}

              {/* Msg 4: Empresa */}
              {tAbs >= 17.15 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '88%',
                    opacity: spMsg4,
                    transform: `translateY(${interpolate(spMsg4, [0, 1], [24, 0])}px)`,
                    background: CORES.marcaEscura,
                    border: '2px solid #60A5FA',
                    borderRadius: '24px 24px 6px 24px',
                    padding: '16px 22px',
                    color: '#FFFFFF',
                    fontSize: 33,
                    fontWeight: 700,
                    lineHeight: 1.25,
                  }}
                >
                  Aqui temos todo o seu atendimento registrado em um só lugar. Vamos resolver.
                </div>
              )}
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 3 — DONO 3: O RESULTADO (19.10s -> 27.28s)
// "Hoje eu vejo quem já é cliente na hora, com dados e chamados centralizados para atender melhor."
// ============================================================================
const Cena3DonoResultado: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((27.28 - 19.1) * fps);
  const tAbs = 19.1 + frame / fps;

  const enterOp = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(frame, [durFrames - 10, durFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Zoom suave contínuo no vídeo dono_3.mp4 (1.0 -> 1.06)
  const videoScale = interpolate(frame, [0, durFrames], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  const spCard = spring({frame: frame - 4, fps, config: {damping: 14, stiffness: 160}});
  const spFase2 = spring({
    frame: frame - Math.round((23.15 - 19.1) * fps),
    fps,
    config: {damping: 14, stiffness: 170},
  });
  const spFase3 = spring({
    frame: frame - Math.round((25.7 - 19.1) * fps),
    fps,
    config: {damping: 14, stiffness: 170},
  });

  const floatY = Math.sin(frame * 0.11) * 5;

  return (
    <AbsoluteFill style={{opacity: enterOp * exitOp, backgroundColor: '#000'}}>
      <AbsoluteFill style={{transform: `scale(${videoScale})`}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Gradiente exclusivo no topo e base — rosto do dono 100% livre e com iluminação natural */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(11,17,32,0.84) 0%, rgba(11,17,32,0.0) 27%, rgba(11,17,32,0.0) 70%, rgba(11,17,32,0.85) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* ZONA TOPO (y=165..430) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          fontFamily,
          opacity: spCard,
          transform: `translateY(${floatY}px) scale(${interpolate(spCard, [0, 1], [0.92, 1])})`,
          background: 'rgba(15, 23, 42, 0.94)',
          border: `3px solid ${CORES.marca}`,
          borderRadius: 28,
          padding: '20px 28px',
          boxShadow: '0 20px 45px rgba(0,0,0,0.6)',
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
          <span
            style={{
              background: '#10B981',
              color: '#052E16',
              fontSize: 32,
              fontWeight: 900,
              padding: '5px 20px',
              borderRadius: 999,
              textTransform: 'uppercase',
            }}
          >
            O resultado
          </span>
          <span style={{color: '#93C5FD', fontSize: 33, fontWeight: 800}}>
            CRM + Helpdesk Chatwoot
          </span>
        </div>

        {/* Frase principal que evolui sincronizada com a fala */}
        <div
          style={{
            color: '#FFFFFF',
            fontSize: 40,
            fontWeight: 900,
            lineHeight: 1.16,
          }}
        >
          {tAbs < 23.15
            ? 'Identifico quem já é cliente na hora'
            : tAbs < 25.7
            ? 'Dados e chamados centralizados'
            : 'Histórico completo para atender melhor'}
        </div>

        {/* Pílulas dinâmicas sem numeração que acendem na voz */}
        <div style={{display: 'flex', gap: 12, flexWrap: 'wrap'}}>
          <span
            style={{
              background: CORES.marca,
              color: '#FFFFFF',
              fontSize: 32,
              fontWeight: 800,
              padding: '6px 18px',
              borderRadius: 12,
            }}
          >
            Cliente na hora
          </span>
          {tAbs >= 23.15 && (
            <span
              style={{
                opacity: spFase2,
                transform: `scale(${spFase2})`,
                background: '#10B981',
                color: '#052E16',
                fontSize: 32,
                fontWeight: 900,
                padding: '6px 18px',
                borderRadius: 12,
              }}
            >
              Dados + Chamados
            </span>
          )}
          {tAbs >= 25.7 && (
            <span
              style={{
                opacity: spFase3,
                transform: `scale(${spFase3})`,
                background: '#3B82F6',
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                padding: '6px 18px',
                borderRadius: 12,
              }}
            >
              Atendimento com IA
            </span>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 4 — CARTÃO FINAL / CTA (26.93s -> 30.88s)
// "Chame a gente no direct."
// ============================================================================
const Cena4CartaoFinal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.ceil((30.88 - 26.93) * fps);

  const enterOp = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});

  // Movimento contínuo até o último frame no fundo e nos elementos
  const bgScale = interpolate(frame, [0, durFrames], [1.0, 1.1], {extrapolateRight: 'clamp'});
  const spCard = spring({frame: frame - 2, fps, config: {damping: 13, stiffness: 150}});
  const spBtn = spring({frame: frame - 10, fps, config: {damping: 12, stiffness: 160}});

  // Pulso contínuo no card e no botão até o último frame (1.0 a 1.06)
  const btnPulse = 1.03 + Math.sin(frame * 0.24) * 0.03;
  const cardFloat = Math.sin(frame * 0.14) * 8;
  const shineX = interpolate(frame % 55, [0, 55], [-400, 1100]);

  return (
    <AbsoluteFill style={{opacity: enterOp, backgroundColor: CORES.fundoEscuro, fontFamily}}>
      {/* Foto de fundo desfocada com zoom contínuo */}
      <AbsoluteFill style={{transform: `scale(${bgScale})`}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(14px) brightness(0.32)',
          }}
        />
      </AbsoluteFill>

      {/* Véu escuro da marca */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle at 50% 42%, rgba(31,147,255,0.28) 0%, rgba(17,24,39,0.94) 75%)',
        }}
      />

      {/* Conteúdo Centralizado dentro da Safe Zone (y=210..1520) */}
      <div
        style={{
          position: 'absolute',
          top: 210,
          bottom: 360,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          transform: `translateY(${cardFloat}px) scale(${interpolate(spCard, [0, 1], [0.9, 1])})`,
        }}
      >
        {/* Card Principal da Marca (Nome da marca exibido uma única vez) */}
        <div
          style={{
            width: '100%',
            background: 'rgba(15, 23, 42, 0.95)',
            border: `3px solid ${CORES.marca}`,
            borderRadius: 36,
            padding: '38px 36px',
            boxShadow: '0 28px 65px rgba(0,0,0,0.7)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24,
            textAlign: 'center',
          }}
        >
          {/* Ícone / Emblema Vivo */}
          <div
            style={{
              width: 104,
              height: 104,
              borderRadius: 30,
              background: `linear-gradient(135deg, ${CORES.marca} 0%, #0284C7 100%)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 14px 35px rgba(31,147,255,0.45)',
              transform: `scale(${btnPulse})`,
            }}
          >
            <span style={{color: '#FFFFFF', fontSize: 54, fontWeight: 900}}>IA</span>
          </div>

          {/* Nome da Marca em Branco Legível */}
          <div
            style={{
              color: '#FFFFFF',
              fontSize: 60,
              fontWeight: 900,
              lineHeight: 1.1,
              letterSpacing: -0.5,
            }}
          >
            CRM Chatwoot IA
          </div>

          {/* Frase oficial dos fatos do briefing */}
          <div
            style={{
              color: '#E2E8F0',
              fontSize: 36,
              fontWeight: 700,
              lineHeight: 1.32,
              maxWidth: 860,
            }}
          >
            Um CRM feito para o seu negócio a partir do Chatwoot, com atendimento, tickets e
            histórico de cada cliente em um só lugar.
          </div>

          {/* Pílulas dos serviços do briefing */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'center',
              gap: 16,
              marginTop: 6,
            }}
          >
            <span
              style={{
                background: 'rgba(31, 147, 255, 0.22)',
                border: `2px solid ${CORES.marca}`,
                color: '#FFFFFF',
                fontSize: 33,
                fontWeight: 800,
                padding: '10px 22px',
                borderRadius: 16,
              }}
            >
              Integração CRM + Helpdesk/Tickets
            </span>
            <span
              style={{
                background: 'rgba(16, 185, 129, 0.22)',
                border: '2px solid #10B981',
                color: '#FFFFFF',
                fontSize: 33,
                fontWeight: 800,
                padding: '10px 22px',
                borderRadius: 16,
              }}
            >
              Personalizado com IA
            </span>
          </div>
        </div>

        {/* Botão CTA Pulsante + Arroba */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 22,
            transform: `scale(${interpolate(spBtn, [0, 1], [0.85, 1])})`,
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              width: '100%',
              background: `linear-gradient(90deg, ${CORES.marca} 0%, #0284C7 100%)`,
              border: '3px solid #93C5FD',
              borderRadius: 999,
              padding: '28px 36px',
              transform: `scale(${btnPulse})`,
              boxShadow: '0 22px 55px rgba(31, 147, 255, 0.55)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {/* Brilho passando no botão */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shineX,
                width: 180,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.38), transparent)',
                transform: 'skewX(-20deg)',
              }}
            />
            <span
              style={{
                color: '#FFFFFF',
                fontSize: 46,
                fontWeight: 900,
                letterSpacing: 1,
                textTransform: 'uppercase',
              }}
            >
              CHAME A GENTE NO DIRECT
            </span>
          </div>

          <div
            style={{
              background: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid rgba(255,255,255,0.28)',
              borderRadius: 999,
              padding: '12px 36px',
              color: '#FFFFFF',
              fontSize: 38,
              fontWeight: 800,
            }}
          >
            @crmchatwoot.ia
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

  const progresso = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundoEscuro, fontFamily}}>
      {/* Áudios Oficiais */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          const sec = f / fps;
          if (sec < 0.5) return interpolate(sec, [0, 0.5], [0, 0.1]);
          if (sec > DURACAO_S - 1.0) return interpolate(sec, [DURACAO_S - 1.0, DURACAO_S], [0.1, 0]);
          return 0.1;
        }}
      />

      {/* CENA 0: 0.00s -> 4.83s */}
      <Sequence from={0} durationInFrames={Math.ceil(4.83 * fps)}>
        <Cena0Pergunta />
      </Sequence>

      {/* CENA 1: 4.48s -> 12.20s */}
      <Sequence
        from={Math.round(4.48 * fps)}
        durationInFrames={Math.ceil((12.2 - 4.48) * fps)}
      >
        <Cena1DonoProblema />
      </Sequence>

      {/* CENA 2: 11.85s -> 19.45s */}
      <Sequence
        from={Math.round(11.85 * fps)}
        durationInFrames={Math.ceil((19.45 - 11.85) * fps)}
      >
        <Cena2ConversaCRM />
      </Sequence>

      {/* CENA 3: 19.10s -> 27.28s */}
      <Sequence
        from={Math.round(19.1 * fps)}
        durationInFrames={Math.ceil((27.28 - 19.1) * fps)}
      >
        <Cena3DonoResultado />
      </Sequence>

      {/* CENA 4: 26.93s -> 30.88s */}
      <Sequence
        from={Math.round(26.93 * fps)}
        durationInFrames={Math.ceil((30.88 - 26.93) * fps)}
      >
        <Cena4CartaoFinal />
      </Sequence>

      {/* Legenda Karaokê (somente nas cenas 0 a 3, oculta no cartão final >= 26.93s) */}
      {t < 26.93 && (
        <Karaoke
          palavras={PALAVRAS_K}
          fontFamily={fontFamily}
          destaque={CORES.destaque}
          textoDestaque="#FFFFFF"
          tamanho={44}
          base={360}
          maxLetras={26}
        />
      )}

      {/* Barra de Progresso na Safe Zone (y=152, x=60..1020) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 8,
          backgroundColor: 'rgba(255, 255, 255, 0.22)',
          borderRadius: 99,
          overflow: 'hidden',
          zIndex: 100,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            backgroundColor: CORES.marca,
            borderRadius: 99,
          }}
        />
      </div>
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
