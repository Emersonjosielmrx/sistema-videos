import { create } from "zustand";

type Lead = { name: string; phone: string; source: string; segment: string; address?: string };

interface LeadCaptureState {
  results: Lead[];
  segment: string;
  location: string;
  setResults: (results: Lead[]) => void;
  setSegment: (segment: string) => void;
  setLocation: (location: string) => void;
  clear: () => void;
}

export const useLeadCaptureStore = create<LeadCaptureState>((set) => ({
  results: [],
  segment: "",
  location: "",
  setResults: (results) => set({ results }),
  setSegment: (segment) => set({ segment }),
  setLocation: (location) => set({ location }),
  clear: () => set({ results: [], segment: "", location: "" }),
}));
