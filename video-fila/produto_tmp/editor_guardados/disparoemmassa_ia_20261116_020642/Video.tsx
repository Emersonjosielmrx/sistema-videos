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

export const COR = {
  marca: '#22C55E',
  apoio: '#111827',
  fundo: '#111827',
  destaque: '#22C55E',
  textoMarca: '#121216',
  branco: '#FFFFFF',
  cinzaClaro: '#E2E8F0',
  alerta: '#F59E0B',
};

export const DURACAO_S = 32.82;
export const FPS = 30;
export const TOTAL_FRAMES = Math.ceil(DURACAO_S * FPS); // 985

export const PALAVRAS_K: PalavraK[] = [
  // Cena 0 (0.00 - 5.17)
  {p: 'Sua', ini: 0.318, fim: 0.595, quebraAntes: true},
  {p: 'lista', ini: 0.607, fim: 0.919},
  {p: 'cresceu', ini: 0.931, fim: 1.376, quebraApos: true},
  {p: 'e', ini: 1.388, fim: 1.424},
  {p: 'ficou', ini: 1.436, fim: 1.712},
  {p: 'difícil', ini: 1.724, fim: 2.181, quebraLinha: true},
  {p: 'avisar', ini: 2.193, fim: 2.578},
  {p: 'todos', ini: 2.65, fim: 2.902, quebraAntes: true},
  {p: 'os', ini: 2.914, fim: 3.07},
  {p: 'clientes?', ini: 3.082, fim: 3.707, quebraApos: true},

  // Cena 1 (4.82 - 13.00)
  {p: 'Quando', ini: 5.57, fim: 6.13, quebraAntes: true},
  {p: 'a', ini: 6.13, fim: 6.31},
  {p: 'minha', ini: 6.31, fim: 6.41, quebraLinha: true},
  {p: 'base', ini: 6.41, fim: 6.65},
  {p: 'cresceu,', ini: 6.65, fim: 7.49, quebraApos: true},
  {p: 'não', ini: 7.49, fim: 7.95},
  {p: 'dava', ini: 7.95, fim: 8.23},
  {p: 'mais', ini: 8.23, fim: 8.43, quebraLinha: true},
  {p: 'para', ini: 8.43, fim: 8.61},
  {p: 'avisar', ini: 8.61, fim: 8.93, quebraApos: true},
  {p: 'todo', ini: 8.93, fim: 9.13},
  {p: 'mundo', ini: 9.13, fim: 9.35, quebraLinha: true},
  {p: 'no', ini: 9.35, fim: 9.45},
  {p: 'WhatsApp', ini: 9.45, fim: 10.19, quebraApos: true},
  {p: 'sem', ini: 10.19, fim: 10.63},
  {p: 'travar', ini: 10.63, fim: 10.99, quebraLinha: true},
  {p: 'a', ini: 10.99, fim: 11.47},
  {p: 'operação.', ini: 11.47, fim: 11.99, quebraApos: true},

  // Cena 2 (12.65 - 21.54)
  {p: 'Para', ini: 13.146, fim: 13.302, quebraAntes: true},
  {p: 'listas', ini: 13.314, fim: 13.711},
  {p: 'grandes,', ini: 13.723, fim: 14.192, quebraApos: true},
  {p: 'o', ini: 14.288, fim: 14.348},
  {p: 'Disparo', ini: 14.36, fim: 14.817},
  {p: 'em', ini: 14.829, fim: 14.901},
  {p: 'Massa', ini: 14.913, fim: 15.225},
  {p: 'IA', ini: 15.237, fim: 16.463, quebraApos: true},
  {p: 'alterna', ini: 16.487, fim: 16.944},
  {p: 'seus', ini: 16.956, fim: 17.197},
  {p: 'números', ini: 17.209, fim: 17.545, quebraApos: true},
  {p: 'e', ini: 17.557, fim: 17.677},
  {p: 'entrega', ini: 17.701, fim: 18.206, quebraLinha: true},
  {p: 'cada', ini: 18.23, fim: 18.483},
  {p: 'aviso', ini: 18.495, fim: 18.831, quebraApos: true},
  {p: 'personalizado', ini: 18.843, fim: 19.673},
  {p: 'sozinho.', ini: 19.685, fim: 20.249, quebraApos: true},

  // Cena 3 (21.19 - 29.22)
  {p: 'Agora', ini: 21.193, fim: 21.833, quebraAntes: true},
  {p: 'eu', ini: 21.833, fim: 22.153},
  {p: 'alcanço', ini: 22.153, fim: 22.733, quebraLinha: true},
  {p: 'toda', ini: 22.733, fim: 23.013},
  {p: 'a', ini: 23.013, fim: 23.213},
  {p: 'minha', ini: 23.213, fim: 23.313, quebraApos: true},
  {p: 'carteira', ini: 23.313, fim: 23.693},
  {p: 'de', ini: 23.693, fim: 23.933},
  {p: 'clientes', ini: 23.933, fim: 24.553, quebraApos: true},
  {p: 'com', ini: 24.553, fim: 24.813},
  {p: 'campanhas', ini: 24.813, fim: 25.433, quebraLinha: true},
  {p: 'organizadas', ini: 25.433, fim: 26.293, quebraApos: true},
  {p: 'e', ini: 26.293, fim: 26.633},
  {p: 'atendimento', ini: 26.633, fim: 27.353},
  {p: 'muito', ini: 27.353, fim: 27.733, quebraLinha: true},
  {p: 'mais', ini: 27.733, fim: 28.073},
  {p: 'ágil.', ini: 28.073, fim: 28.333, quebraApos: true},
];

// Fundo Dinâmico com Foto + Grade + Feixes em movimento constante
const FundoVivo: React.FC<{foto: string; t: number; variante?: number}> = ({
  foto,
  t,
  variante = 0,
}) => {
  const scale = 1.04 + 0.08 * Math.sin(t * 0.45 + variante);
  const panX = Math.cos(t * 0.55 + variante) * 28;
  const panY = Math.sin(t * 0.4 + variante) * 24;
  const gridOffset = (t * 42) % 80;

  return (
    <AbsoluteFill style={{backgroundColor: COR.fundo, overflow: 'hidden'}}>
      <Img
        src={staticFile(foto)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${scale.toFixed(4)}) translate(${panX.toFixed(1)}px, ${panY.toFixed(1)}px)`,
          filter: 'brightness(0.75) contrast(1.15)',
        }}
      />
      {/* Malha Tecnológica em Movimento */}
      <div
        style={{
          position: 'absolute',
          inset: -120,
          backgroundImage:
            'linear-gradient(rgba(34,197,94,0.10) 2px, transparent 2px), linear-gradient(90deg, rgba(34,197,94,0.10) 2px, transparent 2px)',
          backgroundSize: '80px 80px',
          transform: `translate(${gridOffset.toFixed(1)}px, ${(gridOffset * 0.7).toFixed(1)}px) rotate(${(variante * 8 - 4).toFixed(1)}deg)`,
        }}
      />
      {/* Orbes luminosos em movimento contínuo */}
      <div
        style={{
          position: 'absolute',
          width: 760,
          height: 760,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(34,197,94,0.28) 0%, rgba(34,197,94,0) 70%)',
          top: 220 + Math.sin(t * 0.9 + variante) * 140,
          left: 140 + Math.cos(t * 0.7 + variante) * 160,
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 680,
          height: 680,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(16,185,129,0.22) 0%, rgba(16,185,129,0) 70%)',
          bottom: 240 + Math.cos(t * 0.85 + variante) * 130,
          right: 80 + Math.sin(t * 0.65 + variante) * 140,
        }}
      />
      {/* Vinheta suave preservando centro vivo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.72) 0%, rgba(17,24,39,0.32) 45%, rgba(17,24,39,0.82) 100%)',
        }}
      />
    </AbsoluteFill>
  );
};

// CENA 0: PERGUNTA (0.00s - 5.17s)
// Composição: Apresentador no segundo zero para retenção imediata + PiP dinâmico + Painel CRM de Disparo
const Cena0Pergunta: React.FC<{t: number}> = ({t}) => {
  const {fps} = useVideoConfig();
  const localFrame = Math.max(0, Math.round(t * fps));

  const entradaTopo = spring({
    frame: localFrame,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  const fadeSaida = interpolate(t, [4.85, 5.15], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Transição do apresentador para PiP a partir de 1.35s (fala "e ficou difícil avisar")
  const pipSpring = spring({
    frame: Math.max(0, Math.round((t - 1.35) * fps)),
    fps,
    config: {damping: 15, stiffness: 120},
  });

  // Entrada do Card CRM subindo dinamicamente aos 1.45s
  const crmSpring = spring({
    frame: Math.max(0, Math.round((t - 1.45) * fps)),
    fps,
    config: {damping: 14, stiffness: 125},
  });

  const contatos = [
    {nome: 'Mariana Costa', servico: 'Campanha especial', tAtivo: 0.2, cor: '#22C55E'},
    {nome: 'Carlos Mendes', servico: 'Base de clientes', tAtivo: 1.0, cor: '#10B981'},
    {nome: 'Fernanda Lima', servico: 'Cartão aniversário', tAtivo: 1.8, cor: '#34D399'},
    {nome: 'Roberto Alves', servico: 'Envio de Pix', tAtivo: 2.6, cor: '#22C55E'},
  ];

  const dificilAtivo = t >= 1.43;
  const clientesAtivo = t >= 2.6;
  const pulsoAlerta = 1 + 0.05 * Math.sin(t * 7);

  // Micro-interações de alerta e sobrecarga operacional (q03: entre 2.58s e 4.14s)
  const shakeX = t >= 2.6 ? Math.sin((t - 2.6) * 32) * 4 : 0;
  const pulsoTravado = t >= 2.6 ? 1 + 0.08 * Math.sin((t - 2.6) * 12) : 1;

  // Interpolações para PiP do apresentador (proporção vertical que enquadra perfeitamente rosto e tronco)
  const pipTop = interpolate(pipSpring, [0, 1], [0, 365]);
  const pipLeft = interpolate(pipSpring, [0, 1], [0, 300]);
  const pipWidth = interpolate(pipSpring, [0, 1], [1080, 480]);
  const pipHeight = interpolate(pipSpring, [0, 1], [1920, 380]);
  const pipRadius = interpolate(pipSpring, [0, 1], [0, 26]);
  const fundoVivoOpacity = interpolate(pipSpring, [0, 1], [0, 1]);

  return (
    <AbsoluteFill style={{opacity: fadeSaida}}>
      {/* Fundo vivo tecnológico aparece suavemente na transição para PiP */}
      <div style={{position: 'absolute', inset: 0, opacity: fundoVivoOpacity}}>
        <FundoVivo foto="img_0.jpg" t={t} variante={1} />
      </div>

      {/* APRESENTADOR NO SEGUNDO ZERO: Começa em tela cheia e transiciona suavemente para PiP */}
      <div
        style={{
          position: 'absolute',
          top: pipTop,
          left: pipLeft,
          width: pipWidth,
          height: pipHeight,
          borderRadius: pipRadius,
          overflow: 'hidden',
          border: pipSpring > 0.05 ? `3px solid ${COR.marca}` : 'none',
          boxShadow: pipSpring > 0.05 ? '0 18px 45px rgba(0,0,0,0.7)' : 'none',
          zIndex: 10,
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: pipSpring > 0.1 ? 'center 15%' : 'center center',
          }}
        />
        {/* Selo ao vivo no PiP */}
        {pipSpring > 0.35 && (
          <div
            style={{
              position: 'absolute',
              top: 14,
              left: 16,
              background: 'rgba(17, 24, 39, 0.92)',
              border: `2px solid ${COR.marca}`,
              borderRadius: 999,
              padding: '4px 14px',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              zIndex: 15,
            }}
          >
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: '#EF4444',
                boxShadow: '0 0 8px #EF4444',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: COR.branco,
              }}
            >
              AO VIVO
            </span>
          </div>
        )}
      </div>

      {/* TOPO: Selo Gancho + Título Cinético da Pergunta (y=168..385) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 80,
          right: 80,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `translateY(${interpolate(entradaTopo, [0, 1], [-35, 0])}px)`,
          zIndex: 20,
        }}
      >
        {/* Selo gancho_tela */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 14,
            padding: '10px 26px',
            borderRadius: 999,
            background: 'rgba(17, 24, 39, 0.94)',
            border: `3px solid ${COR.marca}`,
            boxShadow: '0 10px 30px rgba(34,197,94,0.32)',
            marginBottom: 12,
          }}
        >
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              background: COR.marca,
              boxShadow: `0 0 14px ${COR.marca}`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: COR.marca,
              letterSpacing: 0.4,
            }}
          >
            Lista grande no WhatsApp?
          </span>
        </div>

        {/* Título Cinético = Fala exata da cena com espaçamento perfeitamente uniforme */}
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.94)',
            border: '2px solid rgba(255,255,255,0.16)',
            borderRadius: 22,
            padding: '16px 24px',
            width: '100%',
            boxShadow: '0 18px 45px rgba(0,0,0,0.55)',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 44,
              fontWeight: 900,
              lineHeight: 1.2,
              color: COR.branco,
            }}
          >
            <span>Sua </span>
            <span
              style={{
                color: t >= 0.6 ? COR.textoMarca : COR.branco,
                background: t >= 0.6 ? COR.marca : 'transparent',
                padding: t >= 0.6 ? '2px 10px' : '0px',
                borderRadius: 10,
                display: 'inline-block',
              }}
            >
              lista cresceu
            </span>
            <span> e ficou </span>
            <span
              style={{
                color: dificilAtivo ? '#111827' : COR.branco,
                background: dificilAtivo ? COR.alerta : 'transparent',
                padding: dificilAtivo ? '2px 10px' : '0px',
                borderRadius: 10,
                display: 'inline-block',
              }}
            >
              difícil avisar
            </span>
            <span> </span>
            <span
              style={{
                textDecoration: clientesAtivo ? 'underline' : 'none',
                textDecorationColor: COR.marca,
                color: clientesAtivo ? COR.marca : COR.branco,
              }}
            >
              todos os clientes?
            </span>
          </div>
        </div>
      </div>

      {/* CENTRO: Painel CRM de Disparo entrando dinamicamente aos 1.45s (y=765..1315, margem segura acima do Karaokê) */}
      <div
        style={{
          position: 'absolute',
          top: 765,
          left: 80,
          right: 80,
          height: 550,
          background: 'rgba(17, 24, 39, 0.95)',
          borderRadius: 26,
          border: `3px solid ${dificilAtivo ? COR.alerta : COR.marca}`,
          padding: '18px 22px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 24px 60px rgba(0,0,0,0.68)',
          transform: `translateY(${interpolate(crmSpring, [0, 1], [600, 0])}px) translateX(${shakeX.toFixed(1)}px)`,
          opacity: crmSpring,
          zIndex: 15,
        }}
      >
        {/* Cabeçalho do CRM */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingBottom: 10,
            borderBottom: '2px solid rgba(255,255,255,0.12)',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: '50%',
                background: dificilAtivo ? COR.alerta : COR.marca,
                boxShadow: `0 0 14px ${dificilAtivo ? COR.alerta : COR.marca}`,
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: COR.branco,
              }}
            >
              Fila de Envio · WhatsApp
            </span>
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: COR.textoMarca,
              background: dificilAtivo ? COR.alerta : COR.marca,
              padding: '4px 16px',
              borderRadius: 999,
            }}
          >
            {dificilAtivo ? 'Sobrecarga manual' : 'Lista em expansão'}
          </span>
        </div>

        {/* Lista de Contatos */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
            margin: '4px 0',
          }}
        >
          {contatos.map((c, idx) => {
            const ativoItem = t >= c.tAtivo;
            const itemX = Math.sin(t * 3.5 + idx) * 4;
            let statusTexto = 'Aguardando fila';
            let statusCor = 'rgba(15, 23, 42, 0.9)';
            let statusTextoCor = COR.cinzaClaro;
            let isTravado = false;

            if (idx === 0 && t >= 0.6) {
              statusTexto = 'Enviando...';
              statusCor = COR.marca;
              statusTextoCor = COR.textoMarca;
            } else if (idx === 1 && t >= 1.0) {
              statusTexto = dificilAtivo ? 'Fila travando' : 'Pendente';
              statusCor = dificilAtivo ? COR.alerta : 'rgba(30, 41, 59, 0.95)';
              statusTextoCor = dificilAtivo ? COR.textoMarca : COR.branco;
            } else if (idx === 2 && t >= 1.8) {
              statusTexto = dificilAtivo ? 'Atraso manual' : 'Na fila';
              statusCor = dificilAtivo ? COR.alerta : 'rgba(30, 41, 59, 0.95)';
              statusTextoCor = dificilAtivo ? COR.textoMarca : COR.branco;
            } else if (idx === 3 && t >= 2.6) {
              statusTexto = 'Operação travada';
              statusCor = '#EF4444';
              statusTextoCor = '#FFFFFF';
              isTravado = true;
            }

            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: ativoItem ? 'rgba(30, 41, 59, 0.98)' : 'rgba(15, 23, 42, 0.75)',
                  padding: '8px 16px',
                  borderRadius: 14,
                  borderLeft: `6px solid ${ativoItem ? (dificilAtivo && idx >= 1 ? (isTravado ? '#EF4444' : COR.alerta) : c.cor) : '#475569'}`,
                  transform: `translateX(${itemX.toFixed(1)}px)`,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      background: ativoItem ? (isTravado ? '#EF4444' : c.cor) : '#334155',
                      color: ativoItem ? (isTravado ? '#FFFFFF' : COR.textoMarca) : COR.branco,
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 900,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {c.nome.charAt(0)}
                  </div>
                  <div style={{display: 'flex', flexDirection: 'column'}}>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 800,
                        color: COR.branco,
                        lineHeight: 1.15,
                      }}
                    >
                      {c.nome}
                    </span>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 600,
                        color: '#94A3B8',
                        lineHeight: 1.15,
                      }}
                    >
                      {c.servico}
                    </span>
                  </div>
                </div>

                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: statusTextoCor,
                    background: statusCor,
                    padding: '4px 14px',
                    borderRadius: 10,
                    whiteSpace: 'nowrap',
                    transform: isTravado ? `scale(${pulsoTravado.toFixed(3)})` : 'none',
                    boxShadow: isTravado ? '0 0 16px rgba(239,68,68,0.7)' : 'none',
                  }}
                >
                  {statusTexto}
                </span>
              </div>
            );
          })}
        </div>

        {/* Rodapé do CRM: Banner de Alerta de Escala com alto contraste (q02 fix) */}
        <div
          style={{
            background: dificilAtivo ? 'rgba(239, 68, 68, 0.28)' : 'rgba(34, 197, 94, 0.20)',
            border: `2px solid ${dificilAtivo ? '#F59E0B' : COR.marca}`,
            borderRadius: 16,
            padding: '10px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            transform: `scale(${pulsoAlerta.toFixed(3)})`,
          }}
        >
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="9" stroke={dificilAtivo ? '#FBBF24' : COR.marca} strokeWidth="2.5" />
            <path
              d="M12 7V12L15.5 14"
              stroke="#FFFFFF"
              strokeWidth="2.5"
              strokeLinecap="round"
              transform={`rotate(${(t * 95) % 360} 12 12)`}
            />
          </svg>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              textAlign: 'center',
              textShadow: '0 2px 8px rgba(0,0,0,0.9)',
            }}
          >
            {dificilAtivo
              ? 'Difícil avisar um por um sem travar a operação'
              : 'Disparo manual para milhares de contatos'}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// CENA 1: DONO 1 — O DESAFIO (4.82s - 13.00s)
// Composição (h): Vídeo real do dono em tela cheia com zoom suave + Card flutuante só na faixa superior (y=170..410)
const Cena1DonoDesafio: React.FC<{t: number}> = ({t}) => {
  const {fps} = useVideoConfig();
  const localT = Math.max(0, t - 4.82);
  const localFrame = Math.round(localT * fps);

  const entrada = spring({
    frame: localFrame,
    fps,
    config: {damping: 15, stiffness: 130},
  });
  const saida = interpolate(t, [12.65, 13.0], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const videoScale = interpolate(t, [4.82, 13.0], [1.0, 1.07], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const fase2 = t >= 8.6; // "avisar todo mundo no WhatsApp"
  const faseTravar = t >= 10.2; // "sem travar a operação"

  return (
    <AbsoluteFill style={{opacity: Math.min(entrada, saida)}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${videoScale.toFixed(4)})`,
          }}
        />
      </AbsoluteFill>

      {/* Card Flutuante Translúcido no Topo (y=170..415) — rosto do dono em y>=470 100% livre */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 80,
          right: 80,
          background: 'rgba(17, 24, 39, 0.92)',
          borderRadius: 26,
          padding: '20px 28px',
          border: `3px solid ${faseTravar ? COR.alerta : COR.marca}`,
          boxShadow: '0 18px 42px rgba(0,0,0,0.6)',
          transform: `translateY(${interpolate(entrada, [0, 1], [-40, 0])}px)`,
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
            {/* Ícone estrela/sparkle (aprendizado 5a166e51) */}
            <svg width="34" height="34" viewBox="0 0 24 24" fill={faseTravar ? COR.alerta : COR.marca}>
              <path d="M12 2L14.8 9.2L22 12L14.8 14.8L12 22L9.2 14.8L2 12L9.2 9.2L12 2Z" />
            </svg>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: faseTravar ? COR.alerta : COR.marca,
                textTransform: 'uppercase',
                letterSpacing: 0.8,
              }}
            >
              O desafio
            </span>
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: COR.textoMarca,
              background: faseTravar ? COR.alerta : COR.marca,
              padding: '4px 18px',
              borderRadius: 999,
            }}
          >
            {faseTravar ? 'Operação travada' : fase2 ? 'Todo mundo no WhatsApp' : 'Base cresceu'}
          </span>
        </div>

        <div
          style={{
            fontFamily,
            fontSize: 42,
            fontWeight: 900,
            color: COR.branco,
            lineHeight: 1.2,
          }}
        >
          {faseTravar
            ? 'Difícil avisar a base sem travar a operação'
            : fase2
            ? 'Não dava para avisar todo mundo no WhatsApp'
            : 'Quando a base de clientes cresceu'}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// CENA 2: CONVERSA — A SOLUÇÃO (12.65s - 21.54s)
// Composição (b/d): Topo com Rotação de Números sincronizada + Celular WhatsApp sem área ociosa
const Cena2ConversaSolucao: React.FC<{t: number}> = ({t}) => {
  const {fps} = useVideoConfig();
  const localT = Math.max(0, t - 12.65);
  const localFrame = Math.round(localT * fps);

  const entrada = spring({
    frame: localFrame,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const saida = interpolate(t, [21.19, 21.54], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Mensagens da conversa oficial do briefing com timestamps e indicação de rotação de instâncias
  const msgs = [
    {
      de: 'empresa',
      instancia: 'Instância #1',
      texto: 'Olá, Mariana! Preparamos uma condição especial para você na nossa campanha de hoje.',
      tIni: 13.15,
      hora: '09:41',
    },
    {
      de: 'cliente',
      texto: 'Oi! Que ótimo, já estava esperando esse aviso. Como faço para aproveitar?',
      tIni: 15.25,
      hora: '09:41',
    },
    {
      de: 'empresa',
      instancia: 'Instância #2',
      texto: 'Já separei seu pedido aqui. Posso te mandar a chave Pix para agilizar?',
      tIni: 17.35,
      hora: '09:42',
    },
    {
      de: 'cliente',
      texto: 'Pode mandar sim, obrigada!',
      tIni: 19.35,
      hora: '09:42',
    },
  ];

  // Rotação de instâncias sincronizada rigorosamente com a locução (q08 e q09 fixes)
  let instanciaAtiva = 0;
  if (t >= 16.48 && t < 17.55) {
    instanciaAtiva = 1; // Instância #2 na fala "alterna seus números" (q08)
  } else if (t >= 17.55 && t < 18.84) {
    instanciaAtiva = 2; // Instância #3 na fala "aviso personalizado"
  } else if (t >= 18.84) {
    instanciaAtiva = 1; // Instância #2 na fala "sozinho" (q09)
  }
  const instancias = ['Instância #1', 'Instância #2', 'Instância #3'];

  // Scroll suave sincronizado com a entrada da 4ª mensagem aos 19.35s
  const chatScroll = interpolate(t, [19.2, 19.8], [0, -95], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const tiltY = interpolate(Math.sin(t * 0.9), [-1, 1], [-2.5, 2.5]);

  return (
    <AbsoluteFill style={{opacity: Math.min(entrada, saida)}}>
      <FundoVivo foto="img_2.jpg" t={t} variante={2} />

      {/* TOPO (y=168..385): Rótulo 'A solução' + Painel de Rotação de Números */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 80,
          right: 80,
          background: 'rgba(17, 24, 39, 0.94)',
          borderRadius: 26,
          padding: '18px 26px',
          border: `3px solid ${COR.marca}`,
          boxShadow: '0 16px 40px rgba(0,0,0,0.55)',
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
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
              fontWeight: 900,
              color: COR.marca,
              textTransform: 'uppercase',
            }}
          >
            A solução · Disparo em Massa IA
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: COR.textoMarca,
              background: COR.marca,
              padding: '4px 16px',
              borderRadius: 999,
            }}
          >
            Rotação de números
          </span>
        </div>

        {/* Pílulas de Rotação de Instâncias alternando dinamicamente com a fala */}
        <div style={{display: 'flex', gap: 14, justifyContent: 'space-between'}}>
          {instancias.map((inst, idx) => {
            const ativo = idx === instanciaAtiva;
            return (
              <div
                key={inst}
                style={{
                  flex: 1,
                  textAlign: 'center',
                  padding: '10px 12px',
                  borderRadius: 16,
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  background: ativo ? COR.marca : 'rgba(30, 41, 59, 0.95)',
                  color: ativo ? COR.textoMarca : COR.cinzaClaro,
                  border: ativo ? `2px solid ${COR.branco}` : '2px solid rgba(255,255,255,0.12)',
                  boxShadow: ativo ? '0 0 16px rgba(34,197,94,0.6)' : 'none',
                  transform: ativo ? 'scale(1.02)' : 'scale(1.0)',
                  transition: 'all 0.2s',
                }}
              >
                {inst}
              </div>
            );
          })}
        </div>
      </div>

      {/* CENTRO (y=395..1235): Mockup de WhatsApp preenchido e dinâmico, sem área ociosa */}
      <div
        style={{
          position: 'absolute',
          top: 395,
          left: 80,
          right: 80,
          height: 840,
          background: '#0B141A',
          borderRadius: 36,
          border: '4px solid rgba(34, 197, 94, 0.65)',
          boxShadow: '0 26px 65px rgba(0,0,0,0.75)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          transform: `perspective(1200px) rotateY(${tiltY.toFixed(2)}deg)`,
        }}
      >
        {/* Cabeçalho do Celular */}
        <div
          style={{
            background: '#1F2C34',
            padding: '16px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '2px solid rgba(255,255,255,0.1)',
            zIndex: 5,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                background: COR.marca,
                color: COR.textoMarca,
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              M
            </div>
            <div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: COR.branco,
                }}
              >
                Mariana · Cliente
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: COR.marca,
                }}
              >
                Envio automático personalizado
              </div>
            </div>
          </div>

          {/* Selo obrigatório Simulação >= 32px */}
          <div
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: COR.cinzaClaro,
              background: 'rgba(15, 23, 42, 0.9)',
              padding: '8px 18px',
              borderRadius: 999,
              border: '2px solid rgba(255,255,255,0.2)',
            }}
          >
            Simulação
          </div>
        </div>

        {/* Corpo das mensagens com selos de rotação e timestamps (elimina área ociosa) */}
        <div
          style={{
            flex: 1,
            padding: '16px 22px',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              transform: `translateY(${chatScroll.toFixed(1)}px)`,
            }}
          >
            {msgs.map((m, idx) => {
              if (t < m.tIni) return null;
              const mFrame = Math.max(0, Math.round((t - m.tIni) * fps));
              const pop = spring({
                frame: mFrame,
                fps,
                config: {damping: 14, stiffness: 160},
              });
              const isEmpresa = m.de === 'empresa';
              return (
                <div
                  key={idx}
                  style={{
                    alignSelf: isEmpresa ? 'flex-end' : 'flex-start',
                    maxWidth: '88%',
                    background: isEmpresa ? '#005C4B' : '#202C33',
                    color: COR.branco,
                    padding: '10px 18px',
                    borderRadius: 20,
                    borderTopRightRadius: isEmpresa ? 6 : 20,
                    borderTopLeftRadius: isEmpresa ? 20 : 6,
                    boxShadow: '0 8px 22px rgba(0,0,0,0.35)',
                    transform: `scale(${interpolate(pop, [0, 1], [0.85, 1])}) translateY(${interpolate(
                      pop,
                      [0, 1],
                      [16, 0]
                    )}px)`,
                    opacity: pop,
                  }}
                >
                  {/* Tag da Instância rotacionada nas mensagens da empresa */}
                  {isEmpresa && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: 12,
                        marginBottom: 4,
                        paddingBottom: 2,
                        borderBottom: '1px solid rgba(255,255,255,0.15)',
                      }}
                    >
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 800,
                          color: '#34D399',
                        }}
                      >
                        ⚡ {m.instancia}
                      </span>
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 600,
                          color: 'rgba(255,255,255,0.7)',
                        }}
                      >
                        Automático
                      </span>
                    </div>
                  )}

                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      lineHeight: 1.25,
                      color: COR.branco,
                    }}
                  >
                    {m.texto}
                  </div>

                  {/* Rodapé do balão: hora e status de entrega */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'flex-end',
                      alignItems: 'center',
                      gap: 6,
                      marginTop: 4,
                    }}
                  >
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 600,
                        color: '#94A3B8',
                      }}
                    >
                      {m.hora}
                    </span>
                    {isEmpresa && (
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 900,
                          color: '#22C55E',
                        }}
                      >
                        ✓✓
                      </span>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Indicador "digitando..." antes da 2ª mensagem da empresa */}
            {t >= 16.55 && t < 17.35 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  background: '#005C4B',
                  padding: '10px 20px',
                  borderRadius: 18,
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: COR.marca,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span>⚡ Instância #2 digitando...</span>
              </div>
            )}
          </div>
        </div>

        {/* Barra de Rodapé WhatsApp para fechar mockup com realismo técnico */}
        <div
          style={{
            background: '#1F2C34',
            padding: '12px 20px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            borderTop: '2px solid rgba(255,255,255,0.08)',
          }}
        >
          <div
            style={{
              flex: 1,
              background: '#2A3942',
              borderRadius: 22,
              padding: '8px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <span style={{fontSize: 32}}>📎</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
                color: '#8696A0',
              }}
            >
              Envio automático ativo...
            </span>
          </div>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              background: COR.marca,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span style={{fontSize: 32}}>⚡</span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// CENA 3: DONO 3 — O RESULTADO (21.19s - 29.22s)
// Composição (h + g): Corte com enquadramento mais fechado (médio/close) + 3 pílulas dinâmicas
const Cena3DonoResultado: React.FC<{t: number}> = ({t}) => {
  const {fps} = useVideoConfig();
  const localT = Math.max(0, t - 21.19);
  const localFrame = Math.round(localT * fps);

  const entrada = spring({
    frame: localFrame,
    fps,
    config: {damping: 15, stiffness: 130},
  });
  const saida = interpolate(t, [28.5, 28.87], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Enquadramento mais fechado (médio/close cut) para conferir dinamismo e autoridade (q04 fix)
  const videoScale = interpolate(t, [21.19, 29.22], [1.18, 1.25], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const p1 = t >= 22.15; // "alcanço toda a minha carteira"
  const p2 = t >= 24.81; // "campanhas organizadas"
  const p3 = t >= 26.63; // "atendimento muito mais ágil"

  const beneficios = [
    {texto: 'Carteira alcançada', ativo: p1},
    {texto: 'Campanhas organizadas', ativo: p2},
    {texto: 'Atendimento ágil', ativo: p3},
  ];

  return (
    <AbsoluteFill style={{opacity: Math.min(entrada, saida)}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transformOrigin: '50% 32%',
            transform: `scale(${videoScale.toFixed(4)})`,
          }}
        />
        {/* Vinheta suave para diminuir distrações do fundo */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(ellipse at center, transparent 40%, rgba(17,24,39,0.55) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Painel Superior de Resultado (y=168..425) — rosto do dono em y>=470 100% livre */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 80,
          right: 80,
          background: 'rgba(17, 24, 39, 0.93)',
          borderRadius: 26,
          padding: '18px 24px',
          border: `3px solid ${COR.marca}`,
          boxShadow: '0 18px 42px rgba(0,0,0,0.62)',
          transform: `translateY(${interpolate(entrada, [0, 1], [-40, 0])}px)`,
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
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <svg width="34" height="34" viewBox="0 0 24 24" fill={COR.marca}>
              <path d="M12 2L14.8 9.2L22 12L14.8 14.8L12 22L9.2 14.8L2 12L9.2 9.2L12 2Z" />
            </svg>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: COR.marca,
                textTransform: 'uppercase',
              }}
            >
              O resultado
            </span>
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: COR.branco,
            }}
          >
            Disparo em Massa IA
          </span>
        </div>

        <div style={{display: 'flex', gap: 12, justifyContent: 'space-between'}}>
          {beneficios.map((b, idx) => (
            <div
              key={idx}
              style={{
                flex: 1,
                padding: '12px 14px',
                borderRadius: 18,
                background: b.ativo ? COR.marca : 'rgba(30, 41, 59, 0.95)',
                color: b.ativo ? COR.textoMarca : COR.cinzaClaro,
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                textAlign: 'center',
                lineHeight: 1.15,
                border: b.ativo ? `2px solid ${COR.branco}` : '2px solid rgba(255,255,255,0.15)',
                boxShadow: b.ativo ? '0 0 16px rgba(34,197,94,0.6)' : 'none',
                transform: `scale(${b.ativo ? 1.02 : 0.98})`,
              }}
            >
              {b.texto}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// CENA 4: CARTÃO FINAL (28.87s - 32.82s)
// Composição escalonada (stagger), foco total em conversão, slow zoom-in contínuo e shimmer no botão CTA
const Cena4CartaoFinal: React.FC<{t: number}> = ({t}) => {
  const {fps} = useVideoConfig();
  const localT = Math.max(0, t - 28.87);
  const localFrame = Math.round(localT * fps);

  // Entrada suave com slide-up e opacidade progressiva (q13 fix)
  const entradaCard = spring({
    frame: localFrame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Slow zoom-in contínuo no cartão durante a fala final (1.0 para 1.04) (q14 fix)
  const slowZoom = interpolate(localT, [0, 3.95], [1.0, 1.04], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const flutuaCard = Math.sin(localT * 3.0) * 8;

  // Animação escalonada (stagger) para os chips de benefícios (q14 fix)
  const pillSpring0 = spring({frame: Math.max(0, localFrame - 8), fps, config: {damping: 14, stiffness: 140}});
  const pillSpring1 = spring({frame: Math.max(0, localFrame - 14), fps, config: {damping: 14, stiffness: 140}});
  const pillSpring2 = spring({frame: Math.max(0, localFrame - 20), fps, config: {damping: 14, stiffness: 140}});
  const pillSpring3 = spring({frame: Math.max(0, localFrame - 26), fps, config: {damping: 14, stiffness: 140}});
  const pillSprings = [pillSpring0, pillSpring1, pillSpring2, pillSpring3];

  // Entrada do botão aos ~1.1s com efeito shimmer contínuo e pulso
  const botaoSpring = spring({frame: Math.max(0, localFrame - 32), fps, config: {damping: 13, stiffness: 150}});
  const pulsoBotao = (1 + 0.05 * Math.sin(localT * 7.5)) * botaoSpring;
  const shimmerPos = ((localT * 320) % 650) - 150;

  // Entrada do @arroba aos ~1.4s
  const arrobaSpring = spring({frame: Math.max(0, localFrame - 38), fps, config: {damping: 14, stiffness: 130}});

  const servicosFatos = [
    'Disparo inteligente',
    'Rotação de números',
    'Cartão de aniversário',
    'Envio de Pix',
  ];

  return (
    <AbsoluteFill>
      <FundoVivo foto="img_4.jpg" t={t} variante={4} />

      <div
        style={{
          position: 'absolute',
          top: 260,
          bottom: 300,
          left: 80,
          right: 80,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 36,
          transform: `translateY(${flutuaCard.toFixed(1)}px) scale(${slowZoom.toFixed(4)})`,
          opacity: entradaCard,
        }}
      >
        {/* Cartão Central: Foco claro de conversão sem poluição de parágrafo longo (q13 fix) */}
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.95)',
            borderRadius: 34,
            padding: '32px 36px',
            width: '100%',
            border: `3px solid ${COR.marca}`,
            boxShadow: '0 24px 60px rgba(0,0,0,0.65)',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            transform: `translateY(${interpolate(entradaCard, [0, 1], [40, 0])}px)`,
          }}
        >
          <div
            style={{
              padding: '10px 24px',
              borderRadius: 999,
              background: 'rgba(34, 197, 94, 0.18)',
              border: `2px solid ${COR.marca}`,
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: COR.marca,
            }}
          >
            Campanhas no WhatsApp
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 62,
              fontWeight: 900,
              color: COR.branco,
              lineHeight: 1.1,
            }}
          >
            Disparo em Massa IA
          </div>

          {/* Frase direta e concisa (substituindo o parágrafo longo de 3 linhas - q13 fix) */}
          <div
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 700,
              color: COR.cinzaClaro,
              lineHeight: 1.25,
            }}
          >
            Disparo em massa inteligente no WhatsApp
          </div>

          {/* Chips de benefícios com entrada escalonada animada (q14 fix) */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 12,
              justifyContent: 'center',
              marginTop: 6,
            }}
          >
            {servicosFatos.map((s, i) => {
              const pSpring = pillSprings[i];
              return (
                <div
                  key={i}
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: COR.branco,
                    background: 'rgba(30, 41, 59, 0.95)',
                    border: `2px solid ${COR.marca}`,
                    padding: '8px 18px',
                    borderRadius: 16,
                    transform: `scale(${interpolate(pSpring, [0, 1], [0.75, 1])})`,
                    opacity: pSpring,
                    boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                  }}
                >
                  {s}
                </div>
              );
            })}
          </div>
        </div>

        {/* Botão CTA Principal com pulso contínuo e efeito shimmer (q14 fix) + @arroba */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 20,
            width: '100%',
          }}
        >
          <div
            style={{
              position: 'relative',
              background: COR.marca,
              color: COR.textoMarca,
              fontFamily,
              fontSize: 46,
              fontWeight: 900,
              padding: '24px 52px',
              borderRadius: 999,
              boxShadow: `0 0 ${(24 + 14 * Math.sin(localT * 7.5)).toFixed(1)}px rgba(34, 197, 94, 0.65)`,
              transform: `scale(${pulsoBotao.toFixed(4)})`,
              textTransform: 'uppercase',
              letterSpacing: 1,
              textAlign: 'center',
              overflow: 'hidden',
            }}
          >
            {/* Feixe Shimmer contínuo que varre o botão */}
            <div
              style={{
                position: 'absolute',
                top: -30,
                bottom: -30,
                width: 70,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
                transform: `translateX(${shimmerPos.toFixed(1)}px) skewX(-25deg)`,
                pointerEvents: 'none',
              }}
            />
            <span style={{position: 'relative', zIndex: 2}}>CHAME NO DIRECT</span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: COR.branco,
              background: 'rgba(17, 24, 39, 0.92)',
              padding: '12px 32px',
              borderRadius: 999,
              border: '2px solid rgba(255,255,255,0.22)',
              transform: `translateY(${interpolate(arrobaSpring, [0, 1], [25, 0])}px)`,
              opacity: arrobaSpring,
            }}
          >
            @disparoemmassa.ia
          </div>
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
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Volume da trilha: 0.10 durante fala, 0.18 no fim com fade out suave
  const volTrilha = interpolate(
    t,
    [0, 0.5, 28.8, 31.0, 32.82],
    [0.03, 0.1, 0.1, 0.16, 0.04],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: COR.fundo, fontFamily}}>
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={volTrilha} />

      {/* Cena 0: Pergunta (0.00s - 5.17s) */}
      <Sequence from={0} durationInFrames={Math.ceil(5.17 * fps)}>
        <Cena0Pergunta t={t} />
      </Sequence>

      {/* Cena 1: Dono Desafio (4.82s - 13.00s) */}
      <Sequence
        from={Math.floor(4.82 * fps)}
        durationInFrames={Math.ceil((13.0 - 4.82) * fps)}
      >
        <Cena1DonoDesafio t={t} />
      </Sequence>

      {/* Cena 2: Conversa Solução (12.65s - 21.54s) */}
      <Sequence
        from={Math.floor(12.65 * fps)}
        durationInFrames={Math.ceil((21.54 - 12.65) * fps)}
      >
        <Cena2ConversaSolucao t={t} />
      </Sequence>

      {/* Cena 3: Dono Resultado (21.19s - 28.87s) */}
      <Sequence
        from={Math.floor(21.19 * fps)}
        durationInFrames={Math.ceil((28.87 - 21.19) * fps)}
      >
        <Cena3DonoResultado t={t} />
      </Sequence>

      {/* Cena 4: Cartão Final (28.87s - 32.82s) */}
      <Sequence
        from={Math.floor(28.87 * fps)}
        durationInFrames={TOTAL_FRAMES - Math.floor(28.87 * fps)}
      >
        <Cena4CartaoFinal t={t} />
      </Sequence>

      {/* Barra de Progresso na Safe Zone (y=152, x=60..1020) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 8,
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: 99,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso.toFixed(2)}%`,
            height: '100%',
            background: COR.marca,
            borderRadius: 99,
          }}
        />
      </div>

      {/* Legenda Karaokê (somente nas cenas 0 a 3; oculta no Cartão Final) */}
      {t < 28.85 && (
        <Karaoke
          palavras={PALAVRAS_K}
          fontFamily={fontFamily}
          destaque={COR.destaque}
          textoDestaque={COR.textoMarca}
          tamanho={44}
          base={360}
          maxLetras={38}
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
