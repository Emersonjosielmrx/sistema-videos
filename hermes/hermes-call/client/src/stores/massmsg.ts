import { create } from "zustand";
import type { Contact } from "@/types/contacts";

interface MassMessageState {
  contacts: Contact[];
  setContacts: (contacts: Contact[]) => void;
  clear: () => void;
}

export const useMassMessageStore = create<MassMessageState>((set) => ({
  contacts: [],
  setContacts: (contacts) => set({ contacts }),
  clear: () => set({ contacts: [] }),
}));
