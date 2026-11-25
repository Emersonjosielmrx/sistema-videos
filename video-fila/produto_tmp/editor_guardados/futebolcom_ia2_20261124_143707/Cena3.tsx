import React from 'react';
import {
  Img,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no vídeo dinâmico de fundo (lanchonete / vitrine de comida)
  const bgScale = interpolate(frame, [0, 222], [1.75, 1.95], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Badge do topo (frame 3)
  const badgeSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título principal (frame 6)
  const titleSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Entrada do Mockup do Smartphone (frame 12 - 20.6s)
  const phoneSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Flutuação e push-in sutil da câmera no celular
  const phonePushIn = interpolate(frame, [12, 220], [1.0, 1.05], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const floatY = Math.cos(frame * 0.05) * 5;

  // 22.8s (frame 78): "vê o cardápio no celular" -> Rolagem dinâmica dos pratos no cardápio
  const menuScroll = interpolate(frame, [70, 115], [0, -115], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Seleção e clique do prato aos ~23.3s (frame 92)
  const itemSelected = frame >= 92;
  const selectSpring = spring({
    frame: frame - 92,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 24.2s (frame 118): "e o pedido chega direto no meu WhatsApp" -> Notificação pop-up de pedido recebido
  const notifSpring = spring({
    frame: frame - 118,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#0F0205',
        fontFamily,
      }}
    >
      {/* 1. Fundo Dinâmico com Vídeo Real da Lanchonete / Salgados e Alimentos */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translate(-14%, -6%)`,
          transformOrigin: 'left center',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(10px)',
          }}
        />
        {/* Véu com alto contraste para destaque total do produto na tela */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(15,2,5,0.92) 0%, rgba(49,6,15,0.80) 40%, rgba(15,2,5,0.95) 100%)',
          }}
        />
      </div>

      {/* 2. Topo Seguro: Rótulo e Headline (y: 165 a 290) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 30,
        }}
      >
        {/* Badge da Etapa */}
        {badgeSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${badgeSpring})`,
              opacity: badgeSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 26px',
              borderRadius: 50,
              backgroundColor: '#0B0D13F5',
              border: '2px solid #FACC15',
              boxShadow: '0 6px 20px rgba(0,0,0,0.8)',
            }}
          >
            <span style={{fontSize: 32}}>⚡</span>
            <span
              style={{
                color: '#FFFFFF',
                fontSize: 34,
                fontWeight: 900,
                letterSpacing: '1px',
                textTransform: 'uppercase',
              }}
            >
              O RESULTADO NA PRÁTICA
            </span>
          </div>
        )}

        {/* Título Principal Dinâmico */}
        {titleSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${titleSpring})`,
              opacity: titleSpring,
              textAlign: 'center',
              width: '100%',
              backgroundColor: '#0B0D13F5',
              padding: '14px 24px',
              borderRadius: 20,
              border: '1.5px solid rgba(255, 255, 255, 0.14)',
              boxShadow: '0 10px 25px rgba(0,0,0,0.8)',
            }}
          >
            <span
              style={{
                fontSize: 40,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                lineHeight: 1.15,
              }}
            >
              CARDÁPIO COM FOTOS ➔{' '}
              <span style={{color: '#FACC15'}}>PEDIDO NO WHATSAPP</span>
            </span>
          </div>
        )}
      </div>

      {/* 3. Smartphone em Destaque com o Cardápio Real em Uso (y: 310 a 1360) */}
      <div
        style={{
          position: 'absolute',
          top: 300,
          left: 110,
          width: 860,
          height: 1040,
          perspective: 1200,
          zIndex: 20,
        }}
      >
        {phoneSpring > 0.01 && (
          <div
            style={{
              width: '100%',
              height: '100%',
              transform: `scale(${phoneSpring * phonePushIn}) rotateY(4deg) rotateX(2deg) translateY(${floatY}px)`,
              transformOrigin: 'center center',
              borderRadius: 44,
              backgroundColor: '#0D1418',
              border: '4px solid #222E35',
              boxShadow:
                '0 30px 70px rgba(0, 0, 0, 0.95), 0 0 0 2px rgba(255, 255, 255, 0.12)',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              position: 'relative',
            }}
          >
            {/* Top Bar do App de Cardápio Digital */}
            <div
              style={{
                height: 95,
                backgroundColor: '#1E293B',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 24px',
                borderBottom: '2px solid rgba(255, 255, 255, 0.08)',
                flexShrink: 0,
                zIndex: 10,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span style={{fontSize: 34}}>🍔</span>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                    Cardápio Digital
                  </span>
                  <span style={{fontSize: 32, color: '#38BDF8', fontWeight: 700}}>
                    Restaurante & Delivery
                  </span>
                </div>
              </div>
              <div
                style={{
                  backgroundColor: '#25D366',
                  color: '#FFFFFF',
                  padding: '6px 14px',
                  borderRadius: 10,
                  fontSize: 32,
                  fontWeight: 900,
                }}
              >
                ABERTO
              </div>
            </div>

            {/* Categorias / Abas do Cardápio */}
            <div
              style={{
                display: 'flex',
                gap: 12,
                padding: '14px 22px',
                backgroundColor: '#0F172A',
                borderBottom: '1.5px solid rgba(255, 255, 255, 0.06)',
                flexShrink: 0,
                zIndex: 10,
              }}
            >
              <div
                style={{
                  backgroundColor: '#E11D48',
                  color: '#FFFFFF',
                  padding: '6px 16px',
                  borderRadius: 20,
                  fontSize: 32,
                  fontWeight: 800,
                }}
              >
                🔥 Mais Pedidos
              </div>
              <div
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.08)',
                  color: '#CBD5E1',
                  padding: '6px 16px',
                  borderRadius: 20,
                  fontSize: 32,
                  fontWeight: 700,
                }}
              >
                Burgers
              </div>
              <div
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.08)',
                  color: '#CBD5E1',
                  padding: '6px 16px',
                  borderRadius: 20,
                  fontSize: 32,
                  fontWeight: 700,
                }}
              >
                Porções
              </div>
            </div>

            {/* Área Rolável de Pratos Suculentos (Demonstração Real) */}
            <div
              style={{
                flex: 1,
                padding: '18px 20px',
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              <div
                style={{
                  transform: `translateY(${menuScroll}px)`,
                  transition: 'transform 0.1s ease-out',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                }}
              >
                {/* Prato 1: Burger Artesanal com Foto e Opção */}
                <div
                  style={{
                    backgroundColor: '#1E293B',
                    borderRadius: 20,
                    border: itemSelected ? '2.5px solid #25D366' : '1.5px solid rgba(255, 255, 255, 0.1)',
                    overflow: 'hidden',
                    boxShadow: '0 8px 20px rgba(0,0,0,0.6)',
                  }}
                >
                  <div style={{height: 140, position: 'relative', overflow: 'hidden'}}>
                    <Img
                      src={staticFile('img_0.jpg')}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        transform: 'scale(1.25)',
                        transformOrigin: '50% 20%',
                      }}
                    />
                    <div
                      style={{
                        position: 'absolute',
                        top: 10,
                        left: 12,
                        backgroundColor: '#E11D48',
                        color: '#FFFFFF',
                        fontSize: 30,
                        fontWeight: 900,
                        padding: '4px 12px',
                        borderRadius: 8,
                      }}
                    >
                      ⭐ MAIS VENDIDO
                    </div>
                  </div>
                  <div style={{padding: '14px 18px'}}>
                    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
                      <div>
                        <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                          X-Burger Artesanal Especial
                        </div>
                        <div style={{fontSize: 32, color: '#CBD5E1', marginTop: 4, fontWeight: 600}}>
                          Pão brioche, hambúrguer suculento, queijo derretido e bacon
                        </div>
                      </div>
                    </div>
                    <div
                      style={{
                        marginTop: 12,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <span style={{fontSize: 32, color: '#FACC15', fontWeight: 800}}>
                        📸 Ver foto ampliada
                      </span>
                      <div
                        style={{
                          transform: itemSelected ? `scale(${1 + selectSpring * 0.08})` : 'scale(1)',
                          backgroundColor: itemSelected ? '#25D366' : '#E11D48',
                          color: '#FFFFFF',
                          padding: '10px 20px',
                          borderRadius: 14,
                          fontSize: 32,
                          fontWeight: 900,
                          boxShadow: itemSelected
                            ? '0 0 16px rgba(37, 211, 102, 0.6)'
                            : '0 4px 12px rgba(225, 29, 72, 0.4)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        {itemSelected ? '✓ ADICIONADO' : '+ ADICIONAR'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Prato 2: Batata Rústica Crocante */}
                <div
                  style={{
                    backgroundColor: '#1E293B',
                    borderRadius: 20,
                    border: '1.5px solid rgba(255, 255, 255, 0.1)',
                    overflow: 'hidden',
                    boxShadow: '0 8px 20px rgba(0,0,0,0.6)',
                  }}
                >
                  <div style={{padding: '16px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                    <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                      <div
                        style={{
                          width: 70,
                          height: 70,
                          borderRadius: 14,
                          backgroundColor: '#334155',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: 36,
                        }}
                      >
                        🍟
                      </div>
                      <div>
                        <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                          Batata Rústica Crocante
                        </div>
                        <div style={{fontSize: 32, color: '#CBD5E1', marginTop: 2, fontWeight: 600}}>
                          Porção generosa e crocante
                        </div>
                      </div>
                    </div>
                    <div
                      style={{
                        backgroundColor: '#334155',
                        color: '#FFFFFF',
                        padding: '8px 16px',
                        borderRadius: 12,
                        fontSize: 32,
                        fontWeight: 800,
                      }}
                    >
                      + Adicionar
                    </div>
                  </div>
                </div>

                {/* Prato 3: Bebida / Suco Natural */}
                <div
                  style={{
                    backgroundColor: '#1E293B',
                    borderRadius: 20,
                    border: '1.5px solid rgba(255, 255, 255, 0.1)',
                    overflow: 'hidden',
                    padding: '16px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                    <div
                      style={{
                        width: 70,
                        height: 70,
                        borderRadius: 14,
                        backgroundColor: '#334155',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 36,
                      }}
                    >
                      🥤
                    </div>
                    <div>
                      <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                        Sucos Naturais & Bebidas
                      </div>
                      <div style={{fontSize: 32, color: '#CBD5E1', marginTop: 2, fontWeight: 600}}>
                        Escolha seu sabor favorito
                      </div>
                    </div>
                  </div>
                  <div
                    style={{
                      backgroundColor: '#334155',
                      color: '#FFFFFF',
                      padding: '8px 16px',
                      borderRadius: 12,
                      fontSize: 32,
                      fontWeight: 800,
                    }}
                  >
                    + Adicionar
                  </div>
                </div>
              </div>
            </div>

            {/* 4. Notificação Pop-Up: Pedido Direto no WhatsApp (frame 118 - 24.2s) */}
            {notifSpring > 0.01 && (
              <div
                style={{
                  position: 'absolute',
                  bottom: 24,
                  left: 20,
                  right: 20,
                  transform: `scale(${notifSpring}) translateY(${(1 - notifSpring) * 25}px)`,
                  opacity: notifSpring,
                  backgroundColor: '#0B0D13F8',
                  borderRadius: 24,
                  border: '2.5px solid #25D366',
                  padding: '18px 22px',
                  boxShadow: '0 16px 40px rgba(0, 0, 0, 0.95), 0 0 20px rgba(37, 211, 102, 0.4)',
                  zIndex: 40,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                  <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                    <div
                      style={{
                        width: 52,
                        height: 52,
                        borderRadius: 14,
                        backgroundColor: '#25D366',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 30,
                        color: '#FFFFFF',
                      }}
                    >
                      💬
                    </div>
                    <div>
                      <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                        Pedido Chegou no WhatsApp!
                      </div>
                      <div style={{fontSize: 32, color: '#86EFAC', fontWeight: 700}}>
                        1x X-Burger Especial • Pronto para produzir
                      </div>
                    </div>
                  </div>
                  <div
                    style={{
                      backgroundColor: '#25D366',
                      color: '#FFFFFF',
                      padding: '8px 16px',
                      borderRadius: 12,
                      fontSize: 32,
                      fontWeight: 900,
                    }}
                  >
                    RECEBIDO
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
