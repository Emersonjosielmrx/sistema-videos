import { useEffect, useRef } from "react";
import { driver } from "driver.js";
import "driver.js/dist/driver.css";
import { useSessions } from "@/stores/sessions";
import { markOnboardingDone } from "./onboarding-state";

// O estado "já viu o tour" mora em ./onboarding-state (reexportado aqui por compatibilidade).
export { isOnboardingDone, markOnboardingDone } from "./onboarding-state";

export const SetupWizard = ({ onClose }: { onClose: () => void }) => {
  const paired = useSessions((s) => s.sessions).some((s) => s.paired);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const finish = () => {
      markOnboardingDone();
      onCloseRef.current();
    };

    const driverObj = driver({
      showProgress: true,
      animate: true,
      nextBtnText: "Próximo",
      prevBtnText: "Anterior",
      doneBtnText: "Começar a Usar",
      popoverClass: "hermes-driver-theme",
      onDestroyed: finish,
      steps: [
        {
          popover: {
            title: "Bem-vindo(a) ao Novo Hermes Call!",
            description: "Fizemos uma grande reformulação no sistema. Vamos dar um tour rápido pelas novas ferramentas de IA para sua operação.",
          },
        },
        {
          element: "#nav-cost",
          popover: {
            title: "1. Visão Geral (Dashboard)",
            description: "Acompanhe tudo ao vivo. Métricas de ligações, sentimento das conversas e os agendamentos feitos pela sua IA.",
            side: "right",
            align: "start",
          },
        },
        {
          element: "#nav-crm",
          popover: {
            title: "2. Gestão de Leads",
            description: "Onde as vendas acontecem. Arraste contatos pelo Kanban, visualize o histórico completo no painel lateral e filtre por campanhas.",
            side: "right",
            align: "start",
          },
        },
        {
          element: "#nav-specialized",
          popover: {
            title: "3. Funcionários IA",
            description: "Crie quantos agentes quiser. Dê uma personalidade, suba PDFs para treiná-los e faça um Test Drive direto pelo chat antes de colocá-los para ligar.",
            side: "right",
            align: "start",
          },
        },
        {
          element: "#nav-agenda",
          popover: {
            title: "4. Agenda Inteligente",
            description: "Gerencie os compromissos marcados pela IA. Você também pode bloquear dias de folga e copiar seu link de agendamento público.",
            side: "right",
            align: "start",
          },
        },
        {
          element: "#nav-catalog",
          popover: {
            title: "5. Vitrine de Produtos",
            description: "Cadastre seus produtos ou serviços. A IA usará esse catálogo dinamicamente durante as ligações para oferecer as melhores opções.",
            side: "right",
            align: "start",
          },
        },
        {
          element: "#nav-calls",
          popover: {
            title: "6. Central de Telefonia",
            description: "Escute as gravações reais, leia a transcrição palavra por palavra das conversas e acompanhe as linhas em andamento.",
            side: "right",
            align: "start",
          },
        },
        {
          element: "#nav-settings",
          popover: {
            title: "7. Configurações & Cofre",
            description: "Cadastre suas chaves (OpenAI, ElevenLabs) no novo Cofre de Credenciais e gerencie integrações como Webhooks e API do Sistema.",
            side: "top",
            align: "start",
          },
        },
      ],
    });

    driverObj.drive();

    return () => {
      driverObj.destroy();
    };
  }, [paired]);

  return null;
};
