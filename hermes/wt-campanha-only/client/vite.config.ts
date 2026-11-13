import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Vite configuration optimized for SaaS V3
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
        ws: true,
      },
    },
  },
  build: {
    // As telas são carregadas sob demanda (React.lazy no App.tsx). Aqui separamos as
    // bibliotecas pesadas em arquivos próprios, para só baixarem com a tela que as usa
    // e ficarem em cache entre versões do painel:
    //   flow   → editor de fluxo (reactflow + dagre), só no Orquestrador
    //   charts → gráficos (recharts), Painel/Análises/Agenda/CRM
    //   tour   → tour guiado (driver.js) e animações (gsap)
    //   react  → react/react-dom num arquivo próprio. Sem isso o Rollup colocava o react
    //            dentro do "charts" e o arquivo inicial passava a importar o charts (411 kB)
    //            em TODA página.
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return undefined;
          if (/[\\/]node_modules[\\/](react|react-dom|scheduler|use-sync-external-store)[\\/]/.test(id)) return "react";
          // clsx é usado pelo painel (cn) E pelo recharts: fora do "charts" pelo mesmo motivo.
          if (/[\\/]node_modules[\\/](clsx|tailwind-merge|class-variance-authority)[\\/]/.test(id)) return "vendor";
          if (/[\\/]node_modules[\\/](reactflow|@reactflow|dagre)[\\/]/.test(id)) return "flow";
          if (/[\\/]node_modules[\\/]recharts[\\/]/.test(id)) return "charts";
          if (/[\\/]node_modules[\\/](gsap|driver\.js)[\\/]/.test(id)) return "tour";
          return undefined;
        },
      },
    },
    // Aviso se algum arquivo passar de ~600 kB (antes o limite estava em 1200 para
    // esconder o pacote único de 2,3 MB).
    chunkSizeWarningLimit: 600,
  }
});




