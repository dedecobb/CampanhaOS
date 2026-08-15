import react from "@vitejs/plugin-react";
import path from "node:path";
// `defineConfig` vem de "vitest/config", não de "vite" — é a forma
// oficialmente recomendada pelo Vitest para o campo `test` (abaixo) ser
// reconhecido pelo TypeScript. O comentário de referência de tipos que
// eu tinha usado antes não resolvia de forma confiável em todo ambiente
// de build (funcionava localmente, mas não no build do Vercel).
import { defineConfig } from "vitest/config";

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
  test: {
    // jsdom simula um DOM de navegador dentro do Node — necessário para
    // testar componentes React sem abrir um navegador de verdade.
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    globals: true,
    css: true,
  },
});
