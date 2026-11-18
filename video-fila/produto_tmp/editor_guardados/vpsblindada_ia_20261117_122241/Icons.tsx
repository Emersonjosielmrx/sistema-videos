import React from 'react';

interface IconProps {
  size?: number;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
}

export const ShieldIcon: React.FC<IconProps> = ({size = 32, color = '#0EA5E9', style}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{display: 'inline-block', verticalAlign: 'middle', flexShrink: 0, ...style}}
  >
    <path
      d="M12 2L3 7V12C3 17.52 6.84 22.74 12 24C17.16 22.74 21 17.52 21 12V7L12 2Z"
      fill={color}
      fillOpacity="0.25"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M9 12L11 14L15 10"
      stroke={color}
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const AlertIcon: React.FC<IconProps> = ({size = 32, color = '#EF4444', style}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{display: 'inline-block', verticalAlign: 'middle', flexShrink: 0, ...style}}
  >
    <path
      d="M12 3L1 22H23L12 3Z"
      fill={color}
      fillOpacity="0.2"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M12 9V14" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
    <circle cx="12" cy="18" r="1.2" fill={color} />
  </svg>
);

export const BotIcon: React.FC<IconProps> = ({size = 32, color = '#0EA5E9', style}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{display: 'inline-block', verticalAlign: 'middle', flexShrink: 0, ...style}}
  >
    <rect
      x="3"
      y="8"
      width="18"
      height="12"
      rx="4"
      fill={color}
      fillOpacity="0.2"
      stroke={color}
      strokeWidth="2"
    />
    <path d="M12 2V8" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <circle cx="12" cy="2" r="1.5" fill={color} />
    <circle cx="8.5" cy="13.5" r="1.75" fill={color} />
    <circle cx="15.5" cy="13.5" r="1.75" fill={color} />
    <path d="M9 17H15" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <path d="M1 13V15" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <path d="M23 13V15" stroke={color} strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export const CheckIcon: React.FC<IconProps> = ({size = 28, color = '#10B981', style}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{display: 'inline-block', verticalAlign: 'middle', flexShrink: 0, ...style}}
  >
    <circle cx="12" cy="12" r="10" fill={color} fillOpacity="0.2" stroke={color} strokeWidth="2" />
    <path
      d="M8 12.5L10.5 15L16 9.5"
      stroke={color}
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const ChatIcon: React.FC<IconProps> = ({size = 32, color = '#FFFFFF', style}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{display: 'inline-block', verticalAlign: 'middle', flexShrink: 0, ...style}}
  >
    <path
      d="M21 11.5C21 16.1944 16.9706 20 12 20C10.4571 20 8.99896 19.6322 7.72895 18.9881L3 20L4.35246 16.2731C3.50426 14.8872 3 13.2562 3 11.5C3 6.80558 7.02944 3 12 3C16.9706 3 21 6.80558 21 11.5Z"
      fill={color}
      fillOpacity="0.25"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle cx="8.5" cy="11.5" r="1.2" fill={color} />
    <circle cx="12" cy="11.5" r="1.2" fill={color} />
    <circle cx="15.5" cy="11.5" r="1.2" fill={color} />
  </svg>
);

export const InstagramIcon: React.FC<IconProps> = ({size = 32, color = '#38BDF8', style}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{display: 'inline-block', verticalAlign: 'middle', flexShrink: 0, ...style}}
  >
    <rect
      x="2"
      y="2"
      width="20"
      height="20"
      rx="6"
      stroke={color}
      strokeWidth="2"
    />
    <circle cx="12" cy="12" r="4.5" stroke={color} strokeWidth="2" />
    <circle cx="17.5" cy="6.5" r="1.2" fill={color} />
  </svg>
);

export const ServerIcon: React.FC<IconProps> = ({size = 32, color = '#0EA5E9', style}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{display: 'inline-block', verticalAlign: 'middle', flexShrink: 0, ...style}}
  >
    <rect
      x="2"
      y="3"
      width="20"
      height="7"
      rx="2"
      fill={color}
      fillOpacity="0.2"
      stroke={color}
      strokeWidth="2"
    />
    <rect
      x="2"
      y="14"
      width="20"
      height="7"
      rx="2"
      fill={color}
      fillOpacity="0.2"
      stroke={color}
      strokeWidth="2"
    />
    <line x1="6" y1="6.5" x2="6.01" y2="6.5" stroke={color} strokeWidth="3" strokeLinecap="round" />
    <line x1="6" y1="17.5" x2="6.01" y2="17.5" stroke={color} strokeWidth="3" strokeLinecap="round" />
    <line x1="10" y1="6.5" x2="10.01" y2="6.5" stroke={color} strokeWidth="3" strokeLinecap="round" />
    <line x1="10" y1="17.5" x2="10.01" y2="17.5" stroke={color} strokeWidth="3" strokeLinecap="round" />
  </svg>
);
