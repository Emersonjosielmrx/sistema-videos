import { create } from "zustand";

type Theme = "light" | "dark-black" | "dark-blue";
let savedTheme = localStorage.getItem("theme") as string | null;
if (savedTheme === "dark") savedTheme = "dark-black";
const initial: Theme =
  (savedTheme as Theme | null) ??
  (matchMedia("(prefers-color-scheme: dark)").matches ? "dark-black" : "light");

export const useTheme = create<{ theme: Theme; toggle: () => void; setTheme: (t: Theme) => void }>((set) => ({
  theme: initial,
  // Alterna claro/escuro lembrando QUAL escuro a pessoa usava (antes quem estava no "dark-blue"
  // ia pro claro e, ao voltar, caía no "dark-black").
  toggle: () =>
    set((s) => {
      let next: Theme;
      if (s.theme.startsWith("dark")) {
        localStorage.setItem("theme-escuro", s.theme);
        next = "light";
      } else {
        next = localStorage.getItem("theme-escuro") === "dark-blue" ? "dark-blue" : "dark-black";
      }
      localStorage.setItem("theme", next);
      return { theme: next };
    }),
  setTheme: (t: Theme) =>
    set(() => {
      localStorage.setItem("theme", t);
      return { theme: t };
    }),
}));

useTheme.subscribe((s) => {
  const root = document.documentElement;
  root.classList.remove("dark", "dark-black", "dark-blue");
  if (s.theme === "dark-black") root.classList.add("dark", "dark-black");
  else if (s.theme === "dark-blue") root.classList.add("dark", "dark-blue");
});
const current = useTheme.getState().theme;
if (current === "dark-black") document.documentElement.classList.add("dark", "dark-black");
else if (current === "dark-blue") document.documentElement.classList.add("dark", "dark-blue");
