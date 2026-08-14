import * as React from "react";
import { cn } from "@/shared/lib/utils";

/**
 * Select NATIVO (elemento <select> do HTML), só estilizado com Tailwind —
 * não é o componente Select completo do Radix/Shadcn (que suporta
 * pesquisa, opções customizadas, etc). Decisão consciente de escopo: para
 * dropdowns simples como "base legal", o nativo já é totalmente acessível
 * e evita adicionar @radix-ui/react-select como dependência nova só para
 * isso. Se um caso de uso futuro precisar de mais (busca, opções ricas),
 * aí sim vale trazer o Radix Select de verdade.
 */
export type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement>;

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(({ className, children, ...props }, ref) => {
  return (
    <select
      ref={ref}
      className={cn(
        "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
});
Select.displayName = "Select";

export { Select };
