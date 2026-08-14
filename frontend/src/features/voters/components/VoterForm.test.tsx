import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { VoterForm } from "@/features/voters/components/VoterForm";
import type { Voter } from "@/features/voters/api/types";

const fullVoter: Voter = {
  id: "voter-1",
  created_by_user_id: "user-1",
  name: "Maria da Silva",
  phone: "65999998888",
  address: "Rua das Flores, 123",
  latitude: null,
  longitude: null,
  tags: ["lideranca", "zona-norte"],
  custom_fields: {},
  notes: "Contato via WhatsApp",
  legal_basis: "consentimento",
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
  leadership_id: null,
};

describe("VoterForm", () => {
  it("mostra erro e não chama onSubmit quando o nome está vazio", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();

    render(<VoterForm onSubmit={onSubmit} isSubmitting={false} submitLabel="Cadastrar" />);

    await user.click(screen.getByRole("button", { name: "Cadastrar" }));

    expect(await screen.findByText("Nome é obrigatório.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("chama onSubmit com os valores preenchidos quando o formulário é válido", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<VoterForm onSubmit={onSubmit} isSubmitting={false} submitLabel="Cadastrar" />);

    await user.type(screen.getByLabelText("Nome"), "Ana Souza");
    await user.type(screen.getByLabelText("Telefone"), "65988887777");
    await user.click(screen.getByRole("button", { name: "Cadastrar" }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ name: "Ana Souza", phone: "65988887777" }),
    );
  });

  it("pré-preenche os campos quando um eleitor existente é passado (modo edição)", () => {
    render(
      <VoterForm initialVoter={fullVoter} onSubmit={vi.fn()} isSubmitting={false} submitLabel="Salvar" />,
    );

    expect(screen.getByLabelText("Nome")).toHaveValue("Maria da Silva");
    expect(screen.getByLabelText("Telefone")).toHaveValue("65999998888");
    expect(screen.getByLabelText("Tags (separadas por vírgula)")).toHaveValue("lideranca, zona-norte");
  });

  it("desabilita o botão de envio enquanto isSubmitting é true", () => {
    render(<VoterForm onSubmit={vi.fn()} isSubmitting={true} submitLabel="Cadastrar" />);

    expect(screen.getByRole("button", { name: "Salvando..." })).toBeDisabled();
  });
});
