import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Img,
  OffthreadVideo,
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

const COR = {
  marca: '#8B5CF6',
  marcaBrilho: '#A78BFA',
  marcaEscura: '#5B21B6',
  apoio: '#1F2937',
  fundo: '#0F172A',
  card: 'rgba(17, 24, 39, 0.92)',
  cardForte: 'rgba(15, 23, 42, 0.96)',
  borda: 'rgba(139, 92, 246, 0.55)',
  texto: '#FFFFFF',
  textoSec: '#E2E8F0',
  alerta: '#EF4444',
  sucesso: '#10B981',
};

const PALAVRAS: PalavraK[] = [
  {p: 'Falta', ini: 0.318, fim: 0.727},
  {p: 'tempo', ini: 0.739, fim: 1.027},
  {p: 'na', ini: 1.039, fim: 1.135, quebraApos: true},
  {p: 'rotina', ini: 1.147, fim: 1.556},
  {p: 'corrida', ini: 1.568, fim: 1.989, quebraApos: true},
  {p: 'para', ini: 2.001, fim: 2.181},
  {p: 'gravar', ini: 2.193, fim: 2.554},
  {p: 'vídeos', ini: 2.566, fim: 2.986, quebraApos: true},
  {p: 'toda', ini: 2.998, fim: 3.263},
  {p: 'semana?', ini: 3.275, fim: 3.828, quebraApos: true},

  {p: 'A', ini: 5.433, fim: 5.517, quebraAntes: true},
  {p: 'rotina', ini: 5.529, fim: 5.926},
  {p: 'corrida', ini: 5.938, fim: 6.347, quebraApos: true},
  {p: 'da', ini: 6.359, fim: 6.443},
  {p: 'empresa', ini: 6.455, fim: 6.899, quebraApos: true},
  {p: 'me', ini: 6.911, fim: 6.984},
  {p: 'impedia', ini: 6.996, fim: 7.476},
  {p: 'de', ini: 7.488, fim: 7.585, quebraApos: true},
  {p: 'sentar', ini: 7.597, fim: 7.993},
  {p: 'e', ini: 8.005, fim: 8.053},
  {p: 'gravar', ini: 8.065, fim: 8.45, quebraApos: true},
  {p: 'conteúdo', ini: 8.474, fim: 9.039},
  {p: 'com', ini: 9.051, fim: 9.183},
  {p: 'frequência.', ini: 9.195, fim: 9.808, quebraApos: true},

  {p: 'A', ini: 11.237, fim: 11.345, quebraAntes: true},
  {p: 'tecnologia', ini: 11.357, fim: 12.054},
  {p: 'cria', ini: 12.066, fim: 12.331, quebraApos: true},
  {p: 'uma', ini: 12.343, fim: 12.499},
  {p: 'versão', ini: 12.511, fim: 12.908},
  {p: 'digital', ini: 12.92, fim: 13.364, quebraApos: true},
  {p: 'da', ini: 13.376, fim: 13.473},
  {p: 'pessoa,', ini: 13.485, fim: 13.953, quebraApos: true},
  {p: 'gerando', ini: 14.218, fim: 14.542},
  {p: 'posturas', ini: 14.554, fim: 14.951},
  {p: 'automáticas', ini: 14.963, fim: 15.732, quebraApos: true},
  {p: 'para', ini: 15.744, fim: 15.937},
  {p: 'falar', ini: 15.949, fim: 16.261},
  {p: 'em', ini: 16.273, fim: 16.357},
  {p: 'português.', ini: 16.369, fim: 17.03, quebraApos: true},

  {p: 'Hoje', ini: 18.457, fim: 18.77, quebraAntes: true},
  {p: 'coloco', ini: 18.782, fim: 19.19, quebraApos: true},
  {p: 'meu', ini: 19.202, fim: 19.347},
  {p: 'clone', ini: 19.359, fim: 19.659},
  {p: 'digital', ini: 19.671, fim: 20.116, quebraApos: true},
  {p: 'ativo', ini: 20.128, fim: 20.524},
  {p: 'nas', ini: 20.536, fim: 20.705},
  {p: 'redes', ini: 20.717, fim: 21.053, quebraApos: true},
  {p: 'todo', ini: 21.065, fim: 21.342},
  {p: 'dia,', ini: 21.354, fim: 21.69, quebraApos: true},
  {p: 'sem', ini: 21.75, fim: 21.979},
  {p: 'pausar', ini: 21.991, fim: 22.375},
  {p: 'o', ini: 22.387, fim: 22.411},
  {p: 'negócio.', ini: 22.423, fim: 23.0, quebraApos: true},

  {p: 'Chame', ini: 24.429, fim: 24.778, quebraAntes: true},
  {p: 'a', ini: 24.79, fim: 24.85},
  {p: 'gente', ini: 24.862, fim: 25.186},
  {p: 'no', ini: 25.198, fim: 25.294},
  {p: 'direct.', ini: 25.307, fim: 25.92, quebraApos: true},
];

// Fundo fotográfico com recorte seguro na zona arquitetônica superior (evita a parte inferior da mesa)
const FundoArquitetura: React.FC<{
  foto: string;
  progresso: number;
  zoomIni: number;
  zoomFim: number;
  panXIni: number;
  panXFim: number;
  panYIni: number;
  panYFim: number;
  escurecer?: number;
  usarCropSuperior?: boolean;
  espelhar?: boolean;
  focoX?: string;
  focoY?: string;
}> = ({
  foto,
  progresso,
  zoomIni,
  zoomFim,
  panXIni,
  panXFim,
  panYIni,
  panYFim,
  escurecer = 0.28,
  usarCropSuperior = true,
  espelhar = false,
  focoX = '50%',
  focoY,
}) => {
  const scale = interpolate(progresso, [0, 1], [zoomIni, zoomFim]);
  const tx = interpolate(progresso, [0, 1], [panXIni, panXFim]);
  const ty = interpolate(progresso, [0, 1], [panYIni, panYFim]);
  const posY = focoY ?? (usarCropSuperior ? '6%' : '45%');
  const sx = espelhar ? -scale : scale;

  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: COR.fundo}}>
      <Img
        src={staticFile(foto)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: `${focoX} ${posY}`,
          transform: `translate(${tx}px, ${ty}px) scale(${sx}, ${scale})`,
          transformOrigin: `${focoX} ${posY}`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, rgba(15,23,42,${escurecer + 0.14}) 0%, rgba(15,23,42,${escurecer * 0.65}) 48%, rgba(15,23,42,${escurecer + 0.22}) 100%)`,
        }}
      />
    </AbsoluteFill>
  );
};

// Cena 0: Pergunta (0.00s - 5.29s)
// Composição (a): B-roll com corte dinâmico de urgência + agenda de gravação sobrecarregada
const Cena0Pergunta: React.FC<{t: number}> = ({t}) => {
  const {fps} = useVideoConfig();
  const dur = 5.29;
  const prog = Math.min(1, Math.max(0, t / dur));
  const corteUrgencia = t >= 2.0;
  const progAto1 = Math.min(1, Math.max(0, t / 2.0));
  const progAto2 = Math.min(1, Math.max(0, (t - 2.0) / (dur - 2.0)));

  const enterGancho = spring({frame: Math.max(0, (t - 0.05) * fps), fps, config: {damping: 12}});
  const enterBloco1 = spring({frame: Math.max(0, (t - 0.22) * fps), fps, config: {damping: 13}});
  const enterBloco2 = spring({frame: Math.max(0, (t - 1.98) * fps), fps, config: {damping: 12}});
  const enterSemana = spring({frame: Math.max(0, (t - 2.95) * fps), fps, config: {damping: 13}});

  const exitOpacity = interpolate(t, [4.94, 5.29], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const exitSlide = interpolate(t, [4.94, 5.29], [0, -60], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const dias = ['SEG', 'TER', 'QUA', 'QUI', 'SEX'];
  const flashCorte = interpolate(t, [1.96, 2.02, 2.22], [0, 0.35, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{opacity: exitOpacity, transform: `translateY(${exitSlide}px)`}}>
      {/* Vídeo B-roll real acelerado de rotina corrida com movimento humano dinâmico nos primeiros segundos */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('broll_rotina.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(15,23,42,0.6) 0%, rgba(15,23,42,0.35) 45%, rgba(15,23,42,0.75) 100%)',
          }}
        />
      </AbsoluteFill>

      {flashCorte > 0 && (
        <AbsoluteFill style={{backgroundColor: `rgba(139, 92, 246, ${flashCorte})`, pointerEvents: 'none'}} />
      )}

      {/* Topo: Gancho da tela + marca na cor oficial da Inovare Clone (#8B5CF6) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          transform: `scale(${interpolate(enterGancho, [0, 1], [0.85, 1])})`,
          opacity: enterGancho,
        }}
      >
        <div
          style={{
            background: COR.marca,
            color: '#FFFFFF',
            padding: '14px 28px',
            borderRadius: 999,
            fontFamily,
            fontWeight: 800,
            fontSize: 34,
            boxShadow: '0 10px 28px rgba(139,92,246,0.5)',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
          }}
        >
          <span
            style={{
              width: 16,
              height: 16,
              borderRadius: '50%',
              background: '#FFFFFF',
              transform: `scale(${1 + 0.3 * Math.sin(t * 9)})`,
            }}
          />
          Sem tempo de gravar?
        </div>

        <div
          style={{
            background: COR.cardForte,
            border: `2px solid ${COR.borda}`,
            color: '#FFFFFF',
            padding: '12px 24px',
            borderRadius: 999,
            fontFamily,
            fontWeight: 700,
            fontSize: 32,
          }}
        >
          Inovare Clone
        </div>
      </div>

      {/* Bloco Central de Gancho: Pergunta cinética limpa sem redundância visual */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: 60,
          right: 60,
          background: COR.card,
          border: `2px solid ${COR.marca}`,
          borderRadius: 32,
          padding: '34px 36px',
          boxShadow: '0 22px 55px rgba(0,0,0,0.55)',
          transform: `translateY(${interpolate(enterBloco1, [0, 1], [40, 0])}px)`,
          opacity: enterBloco1,
        }}
      >
        <div
          style={{
            fontFamily,
            fontWeight: 900,
            fontSize: 50,
            lineHeight: 1.15,
            color: '#FFFFFF',
            textTransform: 'uppercase',
          }}
        >
          <div>Falta tempo na</div>
          <div style={{color: '#FDE047'}}>rotina corrida</div>
        </div>

        {/* Segunda + Terceira parte sincronizadas no corte rápido de 2.0s */}
        {t >= 1.95 && (
          <div
            style={{
              marginTop: 18,
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div
              style={{
                background: COR.marca,
                color: '#FFFFFF',
                padding: '10px 24px',
                borderRadius: 18,
                fontFamily,
                fontWeight: 900,
                fontSize: 44,
                lineHeight: 1.15,
                textTransform: 'uppercase',
                transform: `scale(${interpolate(enterBloco2, [0, 1], [0.85, 1])})`,
                opacity: enterBloco2,
              }}
            >
              para gravar vídeos
            </div>
            {t >= 2.9 && (
              <div
                style={{
                  fontFamily,
                  fontWeight: 900,
                  fontSize: 46,
                  lineHeight: 1.15,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  transform: `translateX(${interpolate(enterSemana, [0, 1], [-30, 0])}px)`,
                  opacity: enterSemana,
                }}
              >
                toda semana?
              </div>
            )}
          </div>
        )}

        {/* Barra de dias da semana preenchendo ao longo da cena */}
        <div
          style={{
            marginTop: 22,
            display: 'flex',
            gap: 14,
            justifyContent: 'space-between',
          }}
        >
          {dias.map((dia, idx) => {
            const tAtiva = 0.65 + idx * 0.78;
            const ativo = t >= tAtiva;
            const popDia = spring({
              frame: Math.max(0, (t - tAtiva) * fps),
              fps,
              config: {damping: 12},
            });
            return (
              <div
                key={dia}
                style={{
                  flex: 1,
                  padding: '14px 8px',
                  borderRadius: 16,
                  background: ativo ? COR.marca : 'rgba(31, 41, 55, 0.9)',
                  border: `2px solid ${ativo ? '#FFFFFF' : 'rgba(255,255,255,0.2)'}`,
                  textAlign: 'center',
                  transform: `scale(${ativo ? interpolate(popDia, [0, 1], [0.9, 1.05]) : 1})`,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontWeight: 800,
                    fontSize: 32,
                    color: '#FFFFFF',
                  }}
                >
                  {dia}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Cena 1: O Problema (4.94s - 11.09s)
// Composição (c): Mensagem única condensada com dois cards de alturas iguais em entrada escalonada (stagger)
const Cena1Problema: React.FC<{t: number}> = ({t}) => {
  const {fps} = useVideoConfig();
  const rel = t - 4.94;
  const dur = 11.09 - 4.94;
  const prog = Math.min(1, Math.max(0, rel / dur));

  const enterCena = spring({frame: Math.max(0, rel * fps), fps, config: {damping: 14}});
  const enterCol1 = spring({frame: Math.max(0, (t - 5.4) * fps), fps, config: {damping: 13}});
  const enterCol2 = spring({frame: Math.max(0, (t - 6.95) * fps), fps, config: {damping: 13}});
  const enterGrav = spring({frame: Math.max(0, (t - 8.0) * fps), fps, config: {damping: 13}});
  const enterFreq = spring({frame: Math.max(0, (t - 9.05) * fps), fps, config: {damping: 12}});

  // Barra de progresso sincronizada com as palavras faladas (evolui continuamente de 5.4s a 10.5s)
  const progBarra = interpolate(t, [5.4, 6.95, 8.05, 9.15, 10.6], [18, 48, 72, 94, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const exitOpacity = interpolate(t, [10.74, 11.09], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{opacity: exitOpacity}}>
      {/* Imagem de fundo com Ken Burns contínuo e visível (zoom e pan dinâmicos na arquitetura de escritório) */}
      <FundoArquitetura
        foto="img_1.jpg"
        progresso={prog}
        zoomIni={1.12}
        zoomFim={1.25}
        panXIni={-40}
        panXFim={40}
        panYIni={0}
        panYFim={-25}
        escurecer={0.3}
        usarCropSuperior={true}
        focoX="50%"
        focoY="18%"
      />

      {/* Topo: Rótulo "O problema" */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          opacity: enterCena,
          transform: `translateY(${interpolate(enterCena, [0, 1], [-25, 0])}px)`,
        }}
      >
        <div
          style={{
            background: COR.cardForte,
            border: `2px solid ${COR.marca}`,
            color: '#FFFFFF',
            padding: '14px 30px',
            borderRadius: 999,
            fontFamily,
            fontWeight: 800,
            fontSize: 36,
            textTransform: 'uppercase',
          }}
        >
          O problema
        </div>
        <div
          style={{
            background: COR.marca,
            color: '#FFFFFF',
            padding: '12px 26px',
            borderRadius: 999,
            fontFamily,
            fontWeight: 800,
            fontSize: 34,
          }}
        >
          Avatar IA
        </div>
      </div>

      {/* Painel Unificado com 2 Cards de Mesma Altura (440px) e Entrada Escalonada (Stagger) */}
      <div
        style={{
          position: 'absolute',
          top: 285,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 22,
        }}
      >
        <div
          style={{
            display: 'flex',
            gap: 24,
            height: 430,
            alignItems: 'stretch',
          }}
        >
          {/* Card 1: Entra em 5.40s ("A rotina corrida da empresa") com microinteração viva */}
          <div
            style={{
              flex: 1,
              height: 430,
              background: COR.cardForte,
              border: `3px solid ${COR.marcaBrilho}`,
              borderRadius: 30,
              padding: '30px 28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transform: `translateY(${interpolate(enterCol1, [0, 1], [55, 0]) + Math.sin(rel * 2.5) * 5}px) scale(${interpolate(enterCol1, [0, 1], [0.92, 1])})`,
              opacity: enterCol1,
              boxShadow: '0 20px 45px rgba(0,0,0,0.55)',
            }}
          >
            <div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 10,
                  background: 'rgba(167, 139, 250, 0.25)',
                  border: '2px solid #DDD6FE',
                  color: '#FFFFFF',
                  padding: '8px 20px',
                  borderRadius: 999,
                  fontFamily,
                  fontWeight: 800,
                  fontSize: 32,
                  textTransform: 'uppercase',
                }}
              >
                <span>Cenário</span>
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: '#FDE047',
                    transform: `scale(${1 + 0.25 * Math.sin(rel * 5)})`,
                  }}
                />
              </div>
              <div
                style={{
                  marginTop: 22,
                  fontFamily,
                  fontWeight: 900,
                  fontSize: 42,
                  lineHeight: 1.18,
                  color: '#FFFFFF',
                }}
              >
                A rotina corrida da empresa
              </div>
            </div>

            <div
              style={{
                background: 'rgba(255,255,255,0.1)',
                border: '2px solid rgba(253, 224, 71, 0.6)',
                padding: '14px 20px',
                borderRadius: 20,
                textAlign: 'center',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontWeight: 800,
                  fontSize: 34,
                  color: '#FDE047',
                }}
              >
                Falta de tempo
              </span>
            </div>
          </div>

          {/* Card 2: Entra escalonado em 6.95s ("me impedia de sentar e gravar") e acende em 9.05s ("com frequência") */}
          <div
            style={{
              flex: 1,
              height: 430,
              background: t >= 9.05 ? 'rgba(91, 33, 182, 0.94)' : COR.cardForte,
              border: `3px solid ${t >= 9.05 ? '#FDE047' : t >= 6.95 ? COR.marca : 'rgba(255,255,255,0.22)'}`,
              borderRadius: 30,
              padding: '30px 28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transform: `translateY(${interpolate(enterCol2, [0, 1], [65, 0]) - Math.sin(rel * 2.5) * 5}px) scale(${interpolate(enterCol2, [0, 1], [0.88, 1])})`,
              opacity: interpolate(enterCol2, [0, 1], [0, 1]),
              boxShadow: t >= 9.05 ? '0 22px 55px rgba(139,92,246,0.55)' : '0 20px 50px rgba(0,0,0,0.55)',
            }}
          >
            <div>
              <div
                style={{
                  display: 'inline-block',
                  background: t >= 8.0 ? COR.marca : 'rgba(139, 92, 246, 0.3)',
                  border: '2px solid #FFFFFF',
                  color: '#FFFFFF',
                  padding: '8px 20px',
                  borderRadius: 999,
                  fontFamily,
                  fontWeight: 800,
                  fontSize: 32,
                  textTransform: 'uppercase',
                  transform: `scale(${t >= 8.0 ? interpolate(enterGrav, [0, 1], [0.92, 1.03]) : 1})`,
                }}
              >
                Impacto
              </div>
              <div
                style={{
                  marginTop: 22,
                  fontFamily,
                  fontWeight: 900,
                  fontSize: 42,
                  lineHeight: 1.18,
                  color: '#FFFFFF',
                }}
              >
                Impedia de sentar e gravar
              </div>
            </div>

            {/* Pílula que muda de cor exatamente em "com frequência" (9.05s) */}
            <div
              style={{
                background: t >= 9.05 ? COR.alerta : 'rgba(255,255,255,0.14)',
                border: `2px solid ${t >= 9.05 ? '#FFFFFF' : 'rgba(255,255,255,0.28)'}`,
                padding: '14px 20px',
                borderRadius: 20,
                textAlign: 'center',
                transform: `scale(${t >= 9.05 ? interpolate(enterFreq, [0, 1], [0.9, 1.05]) : 1})`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontWeight: 800,
                  fontSize: 34,
                  color: '#FFFFFF',
                }}
              >
                Sem frequência
              </span>
            </div>
          </div>
        </div>

        {/* Barra de progresso unificada sincronizada com cada etapa da frase */}
        <div
          style={{
            background: COR.cardForte,
            border: `2px solid ${COR.borda}`,
            borderRadius: 24,
            padding: '18px 28px',
            display: 'flex',
            alignItems: 'center',
            gap: 22,
            boxShadow: '0 14px 35px rgba(0,0,0,0.45)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontWeight: 800,
              fontSize: 32,
              color: '#FFFFFF',
              whiteSpace: 'nowrap',
            }}
          >
            {t >= 9.05 ? 'Sem frequência' : t >= 6.95 ? 'Impedia de gravar' : 'Rotina corrida'}
          </span>
          <div
            style={{
              flex: 1,
              height: 24,
              borderRadius: 999,
              background: 'rgba(255,255,255,0.15)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${progBarra}%`,
                height: '100%',
                background: t >= 9.05 ? `linear-gradient(90deg, ${COR.marca}, ${COR.alerta})` : `linear-gradient(90deg, ${COR.marca}, #FDE047)`,
                borderRadius: 999,
              }}
            />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Cena 2: Como Funciona (10.74s - 18.31s)
// Composição (b): Mockup de celular em 3D + 3 etapas sincronizadas na hora da fala
const Cena2ComoFunciona: React.FC<{t: number}> = ({t}) => {
  const {fps} = useVideoConfig();
  const rel = t - 10.74;
  const dur = 18.31 - 10.74;
  const prog = Math.min(1, Math.max(0, rel / dur));

  const enterTopo = spring({frame: Math.max(0, rel * fps), fps, config: {damping: 14}});
  const enterPhone = spring({frame: Math.max(0, (rel - 0.15) * fps), fps, config: {damping: 13}});

  // As 3 ideias exatas faladas na Cena 2:
  // 1) 12.51s: "versão digital da pessoa"
  // 2) 14.55s: "posturas automáticas"
  // 3) 15.94s: "falar em português"
  const etapas = [
    {num: '1', titulo: 'Versão digital da pessoa', tempo: 12.35},
    {num: '2', titulo: 'Posturas automáticas', tempo: 14.45},
    {num: '3', titulo: 'Fala em português', tempo: 15.9},
  ];

  const exitOpacity = interpolate(t, [17.96, 18.31], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  // Rotação 3D com microinterações e overshoot conforme cada funcionalidade é anunciada
  const rotY = interpolate(t, [10.74, 12.35, 14.45, 15.9, 18.0], [18, 10, 16, 9, 14], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const floatY = Math.sin(t * 3.5) * 10;

  return (
    <AbsoluteFill style={{opacity: exitOpacity}}>
      <FundoArquitetura
        foto="img_2.jpg"
        progresso={prog}
        zoomIni={1.12}
        zoomFim={1.26}
        panXIni={-35}
        panXFim={35}
        panYIni={0}
        panYFim={-20}
        escurecer={0.28}
        usarCropSuperior={true}
        focoX="48%"
        focoY="15%"
      />

      {/* Topo: Rótulo Como funciona */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          opacity: enterTopo,
          transform: `translateY(${interpolate(enterTopo, [0, 1], [-25, 0])}px)`,
        }}
      >
        <div
          style={{
            background: COR.marca,
            color: '#FFFFFF',
            padding: '14px 30px',
            borderRadius: 999,
            fontFamily,
            fontWeight: 900,
            fontSize: 36,
            textTransform: 'uppercase',
            boxShadow: '0 10px 28px rgba(139,92,246,0.5)',
          }}
        >
          Como funciona
        </div>
        <div
          style={{
            background: COR.cardForte,
            border: `2px solid ${COR.borda}`,
            color: '#FFFFFF',
            padding: '12px 26px',
            borderRadius: 999,
            fontFamily,
            fontWeight: 800,
            fontSize: 34,
          }}
        >
          Avatar IA
        </div>
      </div>

      {/* Layout Lado a Lado: Celular 3D com Avatar Fotorrealista à esquerda + 3 etapas sincronizadas à direita */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: 60,
          right: 60,
          height: 880,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 28,
          perspective: 1200,
        }}
      >
        {/* Smartphone 3D grande (840px de altura) com microinteração viva */}
        <div
          style={{
            width: 430,
            height: 840,
            borderRadius: 46,
            background: '#0F172A',
            border: `5px solid ${COR.marcaBrilho}`,
            boxShadow: '0 30px 70px rgba(0,0,0,0.65)',
            padding: '20px 20px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            transform: `rotateY(${rotY}deg) translateY(${floatY}px) scale(${interpolate(enterPhone, [0, 1], [0.88, 1])})`,
            opacity: enterPhone,
          }}
        >
          {/* Barra de estúdio no topo do celular */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '6px 10px',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  background: '#EF4444',
                  transform: `scale(${Math.sin(t * 8) > 0 ? 1.2 : 0.8})`,
                  boxShadow: '0 0 10px #EF4444',
                }}
              />
              <span style={{fontFamily, fontWeight: 800, fontSize: 24, color: '#FFFFFF'}}>
                REC IA
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontWeight: 800,
                fontSize: 22,
                color: '#34D399',
                background: 'rgba(52, 211, 153, 0.15)',
                padding: '4px 12px',
                borderRadius: 999,
                border: '1px solid #34D399',
              }}
            >
              HD 60fps
            </span>
          </div>

          {/* Visualizador do Avatar IA Humano Fotorrealista (Show, Don't Tell) */}
          <div
            style={{
              width: '100%',
              height: 520,
              borderRadius: 28,
              border: `2px solid ${COR.marcaBrilho}`,
              position: 'relative',
              overflow: 'hidden',
              boxShadow: '0 12px 30px rgba(0,0,0,0.6)',
            }}
          >
            <Img
              src={staticFile('avatar_fala.png')}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                objectPosition: 'center 18%',
                transform: `scale(${1.03 + 0.02 * Math.sin(t * 3)})`,
                opacity: t < 14.45 ? 1 : interpolate(t, [14.45, 14.7], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
              }}
            />
            {t >= 14.45 && (
              <Img
                src={staticFile('avatar_gesto.png')}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  objectPosition: 'center 18%',
                  transform: `scale(${1.04 + 0.02 * Math.sin(t * 3)})`,
                  opacity: interpolate(t, [14.45, 14.7], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
                }}
              />
            )}
            {/* Vinheta sutil e selo de tecnologia Inovare */}
            <div
              style={{
                position: 'absolute',
                bottom: 12,
                left: 12,
                right: 12,
                background: 'rgba(15,23,42,0.85)',
                backdropFilter: 'blur(10px)',
                borderRadius: 16,
                padding: '8px 14px',
                border: '1.5px solid rgba(139,92,246,0.6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{fontFamily, fontWeight: 800, fontSize: 24, color: '#A78BFA'}}>
                {t >= 15.9 ? 'Fala em português' : t >= 14.45 ? 'Posturas automáticas' : 'Versão digital da pessoa'}
              </span>
              <span style={{width: 10, height: 10, borderRadius: '50%', background: '#10B981'}} />
            </div>
          </div>

          {/* Selo ativo com fonte ampliada e legível (fontSize: 34px) */}
          <div
            style={{
              background: `linear-gradient(90deg, ${COR.marcaEscura} 0%, ${COR.marca} 100%)`,
              border: `2px solid #FFFFFF`,
              borderRadius: 20,
              padding: '14px 18px',
              textAlign: 'center',
              boxShadow: '0 8px 24px rgba(139,92,246,0.5)',
              transform: `scale(${1 + 0.02 * Math.sin(t * 6)})`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontWeight: 900,
                fontSize: 34,
                color: '#FFFFFF',
                textTransform: 'uppercase',
              }}
            >
              {t >= 15.9 ? 'Fala em português' : t >= 14.45 ? 'Posturas automáticas' : 'Versão digital'}
            </span>
          </div>

          {/* Ondas de voz animadas continuamente com amplitude e pulso ativo */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 9,
              height: 48,
            }}
          >
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((b) => {
              const h = 16 + Math.abs(Math.sin(t * 12 + b * 0.75)) * 30;
              return (
                <div
                  key={b}
                  style={{
                    width: 9,
                    height: h,
                    borderRadius: 99,
                    background: b % 2 === 0 ? COR.marcaBrilho : '#34D399',
                    boxShadow: b % 2 === 0 ? '0 0 8px rgba(167,139,250,0.6)' : '0 0 8px rgba(52,211,153,0.6)',
                  }}
                />
              );
            })}
          </div>
        </div>

        {/* Coluna Direita: As 3 Etapas em entrada sequencial escalonada (stagger) sincronizadas com a fala */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            gap: 24,
          }}
        >
          {etapas.map((et) => {
            const visivel = t >= et.tempo;
            const enterEtapa = spring({
              frame: Math.max(0, (t - et.tempo) * fps),
              fps,
              config: {damping: 12, mass: 0.8},
            });
            const slideX = interpolate(enterEtapa, [0, 1], [90, 0]);
            const op = interpolate(enterEtapa, [0, 1], [0, 1]);
            const scale = interpolate(enterEtapa, [0, 1], [0.9, 1]);

            if (!visivel) {
              return null;
            }

            return (
              <div
                key={et.num}
                style={{
                  background: COR.cardForte,
                  border: `3px solid ${COR.marca}`,
                  borderRadius: 26,
                  padding: '28px 26px',
                  transform: `translateX(${slideX}px) scale(${scale})`,
                  opacity: op,
                  boxShadow: '0 18px 45px rgba(139,92,246,0.45)',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
                  <div
                    style={{
                      width: 56,
                      height: 56,
                      borderRadius: 18,
                      background: COR.marca,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontFamily,
                      fontWeight: 900,
                      fontSize: 34,
                      color: '#FFFFFF',
                      flexShrink: 0,
                      boxShadow: '0 6px 18px rgba(139,92,246,0.6)',
                    }}
                  >
                    {et.num}
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontWeight: 800,
                      fontSize: 36,
                      lineHeight: 1.18,
                      color: '#FFFFFF',
                    }}
                  >
                    {et.titulo}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Cena 3: O Resultado (17.96s - 24.29s)
// Simulação visual dinâmica da interface do Instagram com grade de Reels diários do Avatar IA
const Cena3Resultado: React.FC<{t: number}> = ({t}) => {
  const {fps} = useVideoConfig();
  const rel = t - 17.96;
  const dur = 24.29 - 17.96;
  const prog = Math.min(1, Math.max(0, rel / dur));

  const enterTopo = spring({frame: Math.max(0, rel * fps), fps, config: {damping: 14}});
  const enterSemPausar = spring({frame: Math.max(0, (t - 21.75) * fps), fps, config: {damping: 11, mass: 0.7}});
  const checkPop = spring({frame: Math.max(0, (t - 21.8) * fps), fps, config: {damping: 9, mass: 0.6}});
  const exitOpacity = interpolate(t, [23.94, 24.29], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const postsFeed = [
    {rotulo: 'Versão digital', status: 'Postado', tempo: 18.85, foto: 'avatar_fala.png'},
    {rotulo: 'Posturas automáticas', status: 'Postado', tempo: 19.75, foto: 'avatar_gesto.png'},
    {rotulo: 'Fala em português', status: 'No ar', tempo: 20.65, foto: 'avatar_fala.png'},
  ];

  return (
    <AbsoluteFill style={{opacity: exitOpacity}}>
      {/* Fotografia da recepção moderna em movimento contínuo de Ken Burns */}
      <FundoArquitetura
        foto="img_3.jpg"
        progresso={prog}
        zoomIni={1.06}
        zoomFim={1.22}
        panXIni={30}
        panXFim={-30}
        panYIni={0}
        panYFim={-20}
        escurecer={0.25}
        usarCropSuperior={false}
      />

      {/* Bloco Visual Único no Topo: Título + Feed de Reels Publicados em Cascata com Miniaturas Reais */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          background: COR.cardForte,
          border: `2px solid ${COR.marca}`,
          borderRadius: 32,
          padding: '26px 30px',
          boxShadow: '0 24px 60px rgba(0,0,0,0.6)',
          transform: `translateY(${interpolate(enterTopo, [0, 1], [-40, 0])}px)`,
          opacity: enterTopo,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <span
            style={{
              background: COR.marca,
              color: '#FFFFFF',
              padding: '8px 22px',
              borderRadius: 999,
              fontFamily,
              fontWeight: 800,
              fontSize: 32,
              textTransform: 'uppercase',
            }}
          >
            O resultado
          </span>
          <span
            style={{
              fontFamily,
              fontWeight: 800,
              fontSize: 32,
              color: '#10B981',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span style={{width: 12, height: 12, borderRadius: '50%', background: '#10B981'}} />
            Todo dia nas redes
          </span>
        </div>

        <div
          style={{
            marginTop: 14,
            fontFamily,
            fontWeight: 900,
            fontSize: 46,
            lineHeight: 1.15,
            color: '#FFFFFF',
            textTransform: 'uppercase',
          }}
        >
          Clone digital ativo todo dia
        </div>

        {/* Grade de Feed de Reels publicando sequencialmente em cascata com miniaturas do avatar real */}
        <div
          style={{
            marginTop: 20,
            display: 'flex',
            gap: 18,
            justifyContent: 'space-between',
          }}
        >
          {postsFeed.map((post, i) => {
            const ativo = t >= post.tempo;
            const popPost = spring({
              frame: Math.max(0, (t - post.tempo) * fps),
              fps,
              config: {damping: 12},
            });
            return (
              <div
                key={post.rotulo}
                style={{
                  flex: 1,
                  background: ativo
                    ? 'linear-gradient(180deg, rgba(139,92,246,0.38) 0%, rgba(30,27,75,0.95) 100%)'
                    : 'rgba(31,41,55,0.75)',
                  border: `2.5px solid ${ativo ? '#10B981' : 'rgba(255,255,255,0.2)'}`,
                  borderRadius: 22,
                  padding: '14px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  height: 310,
                  transform: `translateY(${ativo ? interpolate(popPost, [0, 1], [28, 0]) : 12}px) scale(${ativo ? interpolate(popPost, [0, 1], [0.9, 1]) : 0.95})`,
                  opacity: ativo ? 1 : 0.75,
                  boxShadow: ativo ? '0 16px 36px rgba(16,185,129,0.35)' : 'none',
                }}
              >
                {/* Miniatura do Reel com o Avatar Real em ação */}
                <div
                  style={{
                    width: '100%',
                    height: 110,
                    borderRadius: 16,
                    position: 'relative',
                    overflow: 'hidden',
                    border: `2px solid ${ativo ? '#10B981' : 'rgba(255,255,255,0.2)'}`,
                  }}
                >
                  <Img
                    src={staticFile(post.foto)}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      objectPosition: 'center 15%',
                      transform: `scale(${ativo ? 1.05 + 0.02 * Math.sin(t * 4 + i) : 1.0})`,
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      top: 6,
                      left: 6,
                      background: 'rgba(0,0,0,0.65)',
                      padding: '3px 8px',
                      borderRadius: 8,
                      fontFamily,
                      fontWeight: 800,
                      fontSize: 18,
                      color: '#FFFFFF',
                    }}
                  >
                    ▶ Reel
                  </div>
                  {ativo && (
                    <div
                      style={{
                        position: 'absolute',
                        bottom: 6,
                        right: 6,
                        width: 26,
                        height: 26,
                        borderRadius: '50%',
                        background: '#10B981',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontFamily,
                        fontWeight: 900,
                        fontSize: 18,
                        color: '#FFFFFF',
                        boxShadow: '0 0 10px #10B981',
                      }}
                    >
                      ✓
                    </div>
                  )}
                </div>

                <div
                  style={{
                    fontFamily,
                    fontWeight: 800,
                    fontSize: 32,
                    lineHeight: 1.15,
                    color: '#FFFFFF',
                    textAlign: 'center',
                    margin: '6px 0',
                  }}
                >
                  {post.rotulo}
                </div>

                {/* Botão de status com alto contraste no estado 'Fila' (#E2E8F0 com borda sutil) */}
                <div
                  style={{
                    width: '100%',
                    background: ativo ? '#10B981' : 'rgba(30, 41, 59, 0.95)',
                    border: `2px solid ${ativo ? '#FFFFFF' : 'rgba(226, 232, 240, 0.45)'}`,
                    borderRadius: 14,
                    padding: '8px 10px',
                    textAlign: 'center',
                    fontFamily,
                    fontWeight: 800,
                    fontSize: 32,
                    color: ativo ? '#FFFFFF' : '#E2E8F0',
                    transform: `scale(${ativo ? 1 + 0.03 * Math.sin(t * 6 + i) : 1})`,
                  }}
                >
                  {ativo ? `✓ ${post.status}` : 'Fila'}
                </div>
              </div>
            );
          })}
        </div>

        {/* Pílula com slide-up enérgico e check animado saltando às 21.75s: "sem pausar o negócio" */}
        <div
          style={{
            marginTop: 20,
            background: t >= 21.75 ? 'rgba(16, 185, 129, 0.35)' : 'rgba(255,255,255,0.1)',
            border: `3px solid ${t >= 21.75 ? '#10B981' : 'rgba(255,255,255,0.22)'}`,
            borderRadius: 22,
            padding: '16px 24px',
            textAlign: 'center',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 14,
            transform: `translateY(${t >= 21.75 ? interpolate(enterSemPausar, [0, 1], [35, 0]) : 0}px) scale(${t >= 21.75 ? interpolate(enterSemPausar, [0, 1], [0.92, 1.02]) : 0.98})`,
            boxShadow: t >= 21.75 ? '0 12px 35px rgba(16,185,129,0.45)' : 'none',
          }}
        >
          {t >= 21.75 && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 42,
                height: 42,
                borderRadius: '50%',
                background: '#10B981',
                color: '#FFFFFF',
                fontFamily,
                fontWeight: 900,
                fontSize: 26,
                transform: `scale(${interpolate(checkPop, [0, 1], [0, 1.25])})`,
                boxShadow: '0 0 12px #10B981',
              }}
            >
              ✓
            </span>
          )}
          <span
            style={{
              fontFamily,
              fontWeight: 900,
              fontSize: 38,
              color: '#FFFFFF',
              textTransform: 'uppercase',
            }}
          >
            Sem pausar o negócio
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Cena 4: Cartão Final CTA (23.94s - 27.88s)
// Fundo escuro com motion graphics da marca + card centralizado e enxuto + botão com pulsar heartbeat
const Cena4Cartao: React.FC<{t: number}> = ({t}) => {
  const {fps} = useVideoConfig();
  const rel = t - 23.94;
  const dur = 27.88 - 23.94;
  const prog = Math.min(1, Math.max(0, rel / dur));

  const enterCard = spring({frame: Math.max(0, rel * fps), fps, config: {damping: 11, mass: 0.8}});
  const flashEntrada = interpolate(rel, [0, 0.08, 0.35], [0, 0.45, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Efeito heartbeat contínuo no botão de CTA (dois pulsos rápidos a cada batimento)
  const cycle = (rel * 2.2) % 1;
  const heartbeat =
    cycle < 0.16
      ? 1 + 0.08 * Math.sin((cycle / 0.16) * Math.PI)
      : cycle < 0.32
      ? 1 + 0.05 * Math.sin(((cycle - 0.16) / 0.16) * Math.PI)
      : 1;

  const floatCardY = Math.sin(rel * 3.5) * 8;
  const rotCard = interpolate(prog, [0, 1], [-1, 1]);
  const shimmerX = ((rel * 450) % 1100) - 250;

  return (
    <AbsoluteFill>
      {/* Background escuro premium da marca com motion graphics fluidos (elimina repetição estática da recepção) */}
      <AbsoluteFill
        style={{
          background: 'radial-gradient(circle at 50% 45%, #2E1065 0%, #0F172A 65%, #030712 100%)',
          overflow: 'hidden',
        }}
      >
        {/* Halo luminoso dinâmico pulsando em escala contínua */}
        <div
          style={{
            position: 'absolute',
            top: '40%',
            left: '50%',
            width: 750,
            height: 750,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(139,92,246,0.35) 0%, rgba(139,92,246,0) 70%)',
            transform: `translate(-50%, -50%) scale(${1 + 0.15 * Math.sin(rel * 3)})`,
            pointerEvents: 'none',
          }}
        />
        {/* Anel tecnológico em rotação contínua */}
        <div
          style={{
            position: 'absolute',
            top: '45%',
            left: '50%',
            width: 580,
            height: 580,
            borderRadius: '50%',
            border: '2px dashed rgba(167, 139, 250, 0.3)',
            transform: `translate(-50%, -50%) rotate(${rel * 25}deg)`,
            pointerEvents: 'none',
          }}
        />
      </AbsoluteFill>

      {flashEntrada > 0 && (
        <AbsoluteFill style={{backgroundColor: `rgba(139, 92, 246, ${flashEntrada})`, pointerEvents: 'none'}} />
      )}

      {/* Card Principal Enxuto e Centralizado Verticalmente (y=560 a 1220, centro em y=890) */}
      <div
        style={{
          position: 'absolute',
          top: 540,
          left: 60,
          right: 60,
          background: COR.cardForte,
          border: `3px solid ${COR.marca}`,
          borderRadius: 36,
          padding: '44px 40px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          boxShadow: '0 30px 80px rgba(0,0,0,0.75)',
          transform: `translateY(${floatCardY}px) rotate(${rotCard}deg) scale(${interpolate(enterCard, [0, 1], [0.85, 1])})`,
          opacity: enterCard,
        }}
      >
        <div
          style={{
            background: 'rgba(139,92,246,0.25)',
            border: `2px solid ${COR.marcaBrilho}`,
            color: '#FFFFFF',
            padding: '10px 26px',
            borderRadius: 999,
            fontFamily,
            fontWeight: 800,
            fontSize: 32,
            textTransform: 'uppercase',
          }}
        >
          Avatar IA
        </div>

        <div
          style={{
            marginTop: 20,
            fontFamily,
            fontWeight: 900,
            fontSize: 66,
            lineHeight: 1.1,
            color: '#FFFFFF',
            textTransform: 'uppercase',
            letterSpacing: 2,
          }}
        >
          Inovare Clone
        </div>

        {/* Botão CTA Pulsante com efeito Heartbeat e Shimmer varrendo continuamente */}
        <div
          style={{
            marginTop: 34,
            width: '100%',
            background: `linear-gradient(90deg, ${COR.marcaEscura} 0%, ${COR.marca} 50%, ${COR.marcaBrilho} 100%)`,
            border: '3px solid #FFFFFF',
            borderRadius: 26,
            padding: '26px 32px',
            transform: `scale(${heartbeat})`,
            boxShadow: '0 20px 55px rgba(139,92,246,0.75)',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Faixa de brilho Shimmer atravessando o botão continuamente */}
          <div
            style={{
              position: 'absolute',
              top: -40,
              bottom: -40,
              left: shimmerX,
              width: 180,
              background: 'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.65) 50%, rgba(255,255,255,0) 100%)',
              transform: 'skewX(-25deg)',
              pointerEvents: 'none',
            }}
          />
          <div
            style={{
              position: 'relative',
              fontFamily,
              fontWeight: 900,
              fontSize: 48,
              color: '#FFFFFF',
              textTransform: 'uppercase',
            }}
          >
            CHAME NO DIRECT
          </div>
        </div>

        {/* @arroba oficial em alto contraste */}
        <div
          style={{
            marginTop: 26,
            fontFamily,
            fontWeight: 800,
            fontSize: 38,
            color: '#FFFFFF',
            background: 'rgba(255,255,255,0.12)',
            border: '2px solid rgba(255,255,255,0.25)',
            padding: '10px 32px',
            borderRadius: 999,
          }}
        >
          @inovareclone
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;

  const progressoTotal = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateRight: 'clamp',
  });

  const volTrilha = interpolate(
    frame,
    [0, 15, durationInFrames - 25, durationInFrames],
    [0, 0.1, 0.1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: COR.fundo, fontFamily}}>
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volTrilha} />

      {t < 5.29 && <Cena0Pergunta t={t} />}
      {t >= 4.94 && t < 11.09 && <Cena1Problema t={t} />}
      {t >= 10.74 && t < 18.31 && <Cena2ComoFunciona t={t} />}
      {t >= 17.96 && t < 24.29 && <Cena3Resultado t={t} />}
      {t >= 23.94 && <Cena4Cartao t={t} />}

      {/* Barra de progresso na zona segura (y=152) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 8,
          backgroundColor: 'rgba(255,255,255,0.2)',
          borderRadius: 99,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progressoTotal}%`,
            height: '100%',
            backgroundColor: COR.marca,
          }}
        />
      </div>

      {/* Legenda Karaokê contínua em todo o vídeo inclusive na Cena 4 */}
      <Karaoke
        palavras={PALAVRAS}
        fontFamily={fontFamily}
        destaque={COR.marca}
        textoDestaque="#FFFFFF"
        tamanho={44}
        base={340}
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
      durationInFrames={Math.ceil(27.88 * 30)}
    />
  );
};
