import { describe, expect, it } from "vitest";
import { formatCurrencyFromString } from "@/features/finance/api/types";

describe("formatCurrencyFromString", () => {
  it("formata valores positivos com separador de milhar e vírgula decimal", () => {
    expect(formatCurrencyFromString("1000.00")).toBe("R$ 1.000,00");
    expect(formatCurrencyFromString("99.90")).toBe("R$ 99,90");
    expect(formatCurrencyFromString("1000000.00")).toBe("R$ 1.000.000,00");
  });

  it("formata valores negativos corretamente (ex: saldo negativo)", () => {
    expect(formatCurrencyFromString("-300.50")).toBe("-R$ 300,50");
  });

  it("formata zero corretamente", () => {
    expect(formatCurrencyFromString("0.00")).toBe("R$ 0,00");
  });
});
