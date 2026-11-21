import React from 'react';

type ChamferRibbonProps = {
  step: string;
  title: string;
  fontFamily: string;
  accentColor?: string;
  bgColor?: string;
  style?: React.CSSProperties;
};

export const ChamferRibbon: React.FC<ChamferRibbonProps> = ({
  step,
  title,
  fontFamily,
  accentColor = '#7C3AED',
  bgColor = '#0F172A',
  style,
}) => {
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        filter: 'drop-shadow(0 10px 24px rgba(0, 0, 0, 0.6))',
        ...style,
      }}
    >
      {/* Badge numérico com corte diagonal */}
      <div
        style={{
          background: accentColor,
          color: '#FFFFFF',
          fontFamily,
          fontSize: 32,
          fontWeight: 900,
          padding: '10px 24px 10px 20px',
          clipPath: 'polygon(0 0, calc(100% - 14px) 0, 100% 100%, 0 100%)',
          letterSpacing: 1,
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {step}
      </div>

      {/* Tarja com título e chanfro na ponta */}
      <div
        style={{
          background: bgColor,
          color: '#F8FAFC',
          fontFamily,
          fontSize: 32,
          fontWeight: 800,
          padding: '10px 32px 10px 22px',
          marginLeft: -8,
          clipPath: 'polygon(0 0, calc(100% - 16px) 0, 100% 100%, 0 100%)',
          borderTop: '1.5px solid rgba(255, 255, 255, 0.2)',
          borderBottom: '1.5px solid rgba(255, 255, 255, 0.1)',
          letterSpacing: 1.5,
          textTransform: 'uppercase',
        }}
      >
        {title}
      </div>
    </div>
  );
};
