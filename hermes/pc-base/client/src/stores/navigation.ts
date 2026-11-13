import { create } from "zustand";
import { persist } from "zustand/middleware";

export type View = "dashboard" | "calls" | "contacts" | "mass-call" | "mass-message" | "campaigns" | "lists" | "crm" | "settings" | "logs" | "analytics" | "recordings" | "security" | "help" | "cost" | "transcripts" | "credentials" | "specialized" | "agenda" | "catalog" | "profile" | "team" | "meeting-ai" | "follow_up" | "promises" | "knowledge" | "chat";

type State = {
  view: View;
  sidebarCollapsed: boolean;
  hiddenViews: View[];
  hiddenViewsEmployee: View[];
  hiddenSettingsTabs: string[];
  hiddenSettingsTabsEmployee: string[];
  hiddenSubTabs: string[];
  hiddenSubTabsEmployee: string[];
  isEditMode: boolean;
  isEmployeeEditMode: boolean;
  commandOpen: boolean;
  chatOpen: boolean;
  chatInitialMessage: string;
  // Deep-link: aba de Configurações a abrir quando view === "settings" (ex.: "voice").
  // Consumido uma vez pela SettingsPage e limpo. Não persiste.
  settingsTab: string;
  // SimulaÃƒÂ§ÃƒÂ£o de permissÃƒÂµes
  userRole: "superadmin" | "admin" | "employee";
};

export const useNavigation = create<State>()(
  persist(
    (): State => ({
      view: "cost",
      sidebarCollapsed: false,
      hiddenViews: [],
      hiddenViewsEmployee: [],
      hiddenSettingsTabs: [],
      hiddenSettingsTabsEmployee: [],
      hiddenSubTabs: [],
      hiddenSubTabsEmployee: [],
      isEditMode: false,
      isEmployeeEditMode: false,
      commandOpen: false,
      chatOpen: false,
      chatInitialMessage: "",
      settingsTab: "",
      userRole: "admin",
    }),
    // version 1: o logo não troca mais o papel; quem ficou preso em "colaborador"/"superadmin"
    // por clique acidental volta pra "admin" (o papel só simula a visão de funcionário).
    { name: "hermes-nav-store", version: 1, migrate: (persisted: any) => ({ ...(persisted ?? {}), userRole: "admin" }), partialize: (s) => ({ view: s.view, sidebarCollapsed: s.sidebarCollapsed, hiddenViews: s.hiddenViews, hiddenViewsEmployee: s.hiddenViewsEmployee, hiddenSettingsTabs: s.hiddenSettingsTabs, hiddenSettingsTabsEmployee: s.hiddenSettingsTabsEmployee, hiddenSubTabs: s.hiddenSubTabs, hiddenSubTabsEmployee: s.hiddenSubTabsEmployee, userRole: s.userRole }) }
  )
);

export const setView = (view: View) => useNavigation.setState({ view });
// Navega pra Configurações já numa aba específica (deep-link). Ex.: openSettingsTab("voice").
export const openSettingsTab = (tab: string) => useNavigation.setState({ view: "settings", settingsTab: tab });
export const consumeSettingsTab = () => {
  const t = useNavigation.getState().settingsTab;
  if (t) useNavigation.setState({ settingsTab: "" });
  return t;
};
export const setCommandOpen = (commandOpen: boolean) => useNavigation.setState({ commandOpen });
export const setChatOpen = (chatOpen: boolean, initialMessage = "") => useNavigation.setState({ chatOpen, chatInitialMessage: initialMessage });
export const setSidebarCollapsed = (collapsed: boolean) => useNavigation.setState({ sidebarCollapsed: collapsed });
export const setEditMode = (isEditMode: boolean) => useNavigation.setState({ isEditMode, isEmployeeEditMode: false });
export const setEmployeeEditMode = (isEmployeeEditMode: boolean) => useNavigation.setState({ isEmployeeEditMode, isEditMode: false });
export const setUserRole = (userRole: "superadmin" | "admin" | "employee") => useNavigation.setState({ userRole, isEditMode: false, isEmployeeEditMode: false });

export const toggleHiddenView = (view: View) => {
  const state = useNavigation.getState();
  if (state.isEmployeeEditMode) {
    if (state.hiddenViewsEmployee.includes(view)) {
      useNavigation.setState({ hiddenViewsEmployee: state.hiddenViewsEmployee.filter((v) => v !== view) });
    } else {
      useNavigation.setState({ hiddenViewsEmployee: [...state.hiddenViewsEmployee, view] });
    }
    return;
  }
  
  if (state.hiddenViews.includes(view)) {
    useNavigation.setState({ hiddenViews: state.hiddenViews.filter((v) => v !== view) });
  } else {
    useNavigation.setState({ hiddenViews: [...state.hiddenViews, view] });
  }
};

export const toggleHiddenSettingsTab = (tab: string) => {
  const state = useNavigation.getState();
  if (state.isEmployeeEditMode) {
    if (state.hiddenSettingsTabsEmployee.includes(tab)) {
      useNavigation.setState({ hiddenSettingsTabsEmployee: state.hiddenSettingsTabsEmployee.filter((t) => t !== tab) });
    } else {
      useNavigation.setState({ hiddenSettingsTabsEmployee: [...state.hiddenSettingsTabsEmployee, tab] });
    }
    return;
  }
  
  if (state.hiddenSettingsTabs.includes(tab)) {
    useNavigation.setState({ hiddenSettingsTabs: state.hiddenSettingsTabs.filter((t) => t !== tab) });
  } else {
    useNavigation.setState({ hiddenSettingsTabs: [...state.hiddenSettingsTabs, tab] });
  }
};

export const toggleHiddenSubTab = (tabId: string) => {
  const state = useNavigation.getState();
  if (state.isEmployeeEditMode) {
    if (state.hiddenSubTabsEmployee.includes(tabId)) {
      useNavigation.setState({ hiddenSubTabsEmployee: state.hiddenSubTabsEmployee.filter((t) => t !== tabId) });
    } else {
      useNavigation.setState({ hiddenSubTabsEmployee: [...state.hiddenSubTabsEmployee, tabId] });
    }
    return;
  }
  
  if (state.hiddenSubTabs.includes(tabId)) {
    useNavigation.setState({ hiddenSubTabs: state.hiddenSubTabs.filter((t) => t !== tabId) });
  } else {
    useNavigation.setState({ hiddenSubTabs: [...state.hiddenSubTabs, tabId] });
  }
};

export const resetHiddenViews = () => {
  const state = useNavigation.getState();
  if (state.isEmployeeEditMode) {
    useNavigation.setState({ hiddenViewsEmployee: [], hiddenSettingsTabsEmployee: [], hiddenSubTabsEmployee: [] });
  } else {
    useNavigation.setState({ hiddenViews: [], hiddenSettingsTabs: [], hiddenSubTabs: [] });
  }
};
