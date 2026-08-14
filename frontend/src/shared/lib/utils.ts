import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combina classes condicionais (clsx) e resolve conflitos entre classes
 * Tailwind (twMerge) — ex: cn("p-2", condition && "p-4") resulta em só
 * "p-4" quando a condição é verdadeira, em vez de "p-2 p-4" (que
 * quebraria, já que CSS aplica a última classe declarada no arquivo
 * gerado, não a última passada na função).
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
