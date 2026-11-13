import { create } from "zustand";
import type { Contact } from "@/types/contacts";

interface State {
  contacts: Contact[];
  jobId: string | null;
  setContacts: (contacts: Contact[]) => void;
  setJobId: (id: string | null) => void;
  clear: () => void;
}

export const useMassCallStore = create<State>((set) => ({
  contacts: [],
  jobId: null,
  setContacts: (contacts) => set({ contacts }),
  setJobId: (id) => set({ jobId: id }),
  clear: () => set({ contacts: [], jobId: null }),
}));
