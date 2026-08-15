import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Permite imports como `import { Button } from "@/shared/components/ui/button"`
      // em vez de caminhos relativos longos (`../../../shared/...`).
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // Precisa bater com o CORS liberado no backend (Módulo 0:
    // allow_origins=["http://localhost:5173"]).
    port: 5173,
    // Necessário para o servidor de dev do Vite aceitar conexões de fora
    // do container Docker (ver docker-compose.yml).
    host: "0.0.0.0",
  },
});
