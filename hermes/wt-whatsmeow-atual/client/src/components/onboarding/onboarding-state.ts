import { getUser } from "@/lib/auth";

// Estado "já viu o tour de boas-vindas", por usuário. Fica separado do SetupWizard para
// o App consultar sem baixar o driver.js (o tour só é carregado quando vai aparecer).
//
// FIX P2-001 (2026-07-25): chave do onboarding agora inclui user_id.
// Antes era "hermes.onboarding.done" (uma chave só), então:
//   - user A faz onboarding → marca "done"
//   - user B faz login no mesmo navegador → wizard pula (BUG! era pra mostrar)
//   - user A volta → se B não desfez, A vê o onboarding pulado também
// Agora cada user tem sua própria flag.
const doneKeyFor = (userId: string) => `hermes.onboarding.done.${userId}`;

export const currentUserId = (): string => {
  const u = getUser();
  return u?.id || u?.ID || "_anon";
};

export const isOnboardingDone = () => localStorage.getItem(doneKeyFor(currentUserId())) === "1";
export const markOnboardingDone = () => localStorage.setItem(doneKeyFor(currentUserId()), "1");
