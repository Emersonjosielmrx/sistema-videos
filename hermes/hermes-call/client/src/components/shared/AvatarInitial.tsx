import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";

// Lista de cores suaves para fundo de avatares no modo dark/light
const AVATAR_COLORS = [
  "bg-red-500/20 text-red-500",
  "bg-orange-500/20 text-orange-500",
  "bg-amber-500/20 text-amber-500",
  "bg-green-500/20 text-green-500",
  "bg-emerald-500/20 text-emerald-500",
  "bg-teal-500/20 text-teal-500",
  "bg-cyan-500/20 text-cyan-500",
  "bg-blue-500/20 text-blue-500",
  "bg-indigo-500/20 text-indigo-500",
  "bg-violet-500/20 text-violet-500",
  "bg-purple-500/20 text-purple-500",
  "bg-fuchsia-500/20 text-fuchsia-500",
  "bg-pink-500/20 text-pink-500",
  "bg-rose-500/20 text-rose-500",
];

function stringToColorIndex(str: string) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash) % AVATAR_COLORS.length;
}

function getInitials(name: string) {
  const parts = name.trim().split(" ");
  if (parts.length === 0 || !parts[0]) return "?";
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// src (opcional): foto do contato. Sem foto, ou se ela não carregar, mostra as iniciais.
export function AvatarInitial({ name, className, src }: { name: string; className?: string; src?: string }) {
  const colorClass = useMemo(() => {
    return AVATAR_COLORS[stringToColorIndex(name)];
  }, [name]);
  
  const initials = useMemo(() => getInitials(name), [name]);
  const [failedSrc, setFailedSrc] = useState<string | null>(null);

  if (src && failedSrc !== src) {
    return (
      <img
        src={src}
        alt={name}
        onError={() => setFailedSrc(src)}
        className={cn("h-8 w-8 rounded-full object-cover ring-1 ring-border/50", className)}
      />
    );
  }

  return (
    <div 
      className={cn(
        "flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ring-1 ring-border/50",
        colorClass,
        className
      )}
    >
      {initials}
    </div>
  );
}
