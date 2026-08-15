import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";

// Arquivo separado de vite.config.ts, de propósito: tentar colocar o
// campo `test` dentro do vite.config.ts causa um conflito de tipos entre
// a cópia do Vite que o `vitest` usa internamente e a cópia direta do
// projeto — mesmo sendo a "mesma" versão, o TypeScript trata como tipos
// diferentes. `mergeConfig` é o jeito oficial do Vitest de combinar as
// duas configurações sem esse problema.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      // jsdom simula um DOM de navegador dentro do Node — necessário
      // para testar componentes React sem abrir um navegador de verdade.
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
      globals: true,
      css: true,
    },
  }),
);
