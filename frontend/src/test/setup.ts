/**
 * Setup global do Vitest — equivalente ao `conftest.py` do backend.
 * Roda automaticamente antes de cada arquivo de teste (configurado em
 * vite.config.ts: test.setupFiles).
 */
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Desmonta os componentes renderizados entre um teste e outro — sem
// isso, o DOM de um teste "vazaria" para o próximo, causando falhas
// difíceis de depurar (ex: encontrar um elemento duplicado).
afterEach(() => {
  cleanup();
});
