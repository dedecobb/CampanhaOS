import { useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Select } from "@/shared/components/ui/select";
import { getApiErrorMessage } from "@/shared/lib/api-client";
import { getCampaignInfo, submitPublicRegistration } from "@/features/public-registration/api/public-registration-api";
import { GENDER_OPTIONS } from "@/features/public-registration/api/types";

export function PublicRegistrationPage() {
  const { token } = useParams<{ token: string }>();

  const { data: campaignInfo, isLoading: isLoadingCampaign, isError: isCampaignError } = useQuery({
    queryKey: ["public-campaign-info", token],
    queryFn: () => getCampaignInfo(token as string),
    enabled: Boolean(token),
    retry: false,
  });

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [neighborhood, setNeighborhood] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [gender, setGender] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [consentGiven, setConsentGiven] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitError(null);

    if (!name.trim()) {
      setSubmitError("Nome é obrigatório.");
      return;
    }
    if (!consentGiven) {
      setSubmitError("É necessário concordar com o uso dos dados para se cadastrar.");
      return;
    }

    setIsSubmitting(true);
    try {
      await submitPublicRegistration(token as string, {
        name,
        consent_given: consentGiven,
        phone: phone || null,
        address: address || null,
        neighborhood: neighborhood || null,
        city: city || null,
        state: state || null,
        postal_code: postalCode || null,
        gender: gender || null,
        birth_date: birthDate || null,
      });
      setSubmitSuccess(true);
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoadingCampaign) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Carregando...</p>
      </div>
    );
  }

  if (isCampaignError || !campaignInfo) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <Card className="w-full max-w-sm">
          <CardContent className="pt-6 text-center">
            <p className="text-destructive">
              Este link de cadastro é inválido ou não está mais ativo. Confirme com quem te enviou o link se
              ele ainda está correto.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (submitSuccess) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <Card className="w-full max-w-sm">
          <CardContent className="pt-6 text-center">
            <p className="text-lg font-medium text-emerald-600">Cadastro realizado com sucesso!</p>
            <p className="mt-2 text-sm text-muted-foreground">Obrigado por apoiar a campanha.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 px-4 py-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Cadastro — {campaignInfo.tenant_name}</CardTitle>
          <CardDescription>Preencha seus dados para se cadastrar como apoiador(a).</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nome</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Telefone</Label>
              <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="gender">Gênero</Label>
                <Select id="gender" value={gender} onChange={(e) => setGender(e.target.value)}>
                  <option value="">Prefere não informar</option>
                  {GENDER_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="birth_date">Nascimento</Label>
                <Input id="birth_date" type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="address">Endereço</Label>
              <Input id="address" value={address} onChange={(e) => setAddress(e.target.value)} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="neighborhood">Bairro</Label>
              <Input id="neighborhood" value={neighborhood} onChange={(e) => setNeighborhood(e.target.value)} />
            </div>

            <div className="grid grid-cols-[1fr_auto_auto] gap-4">
              <div className="space-y-2">
                <Label htmlFor="city">Cidade</Label>
                <Input id="city" value={city} onChange={(e) => setCity(e.target.value)} />
              </div>
              <div className="w-20 space-y-2">
                <Label htmlFor="state">UF</Label>
                <Input id="state" value={state} onChange={(e) => setState(e.target.value.toUpperCase())} maxLength={2} />
              </div>
              <div className="w-32 space-y-2">
                <Label htmlFor="postal_code">CEP</Label>
                <Input id="postal_code" value={postalCode} onChange={(e) => setPostalCode(e.target.value)} />
              </div>
            </div>

            <label className="flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                checked={consentGiven}
                onChange={(e) => setConsentGiven(e.target.checked)}
                className="mt-1"
              />
              <span>
                Concordo em fornecer meus dados para esta campanha, de acordo com a Lei Geral de Proteção de
                Dados (LGPD). Meus dados serão usados apenas para fins de comunicação e organização desta
                campanha.
              </span>
            </label>

            {submitError && <p className="text-sm text-destructive">{submitError}</p>}

            <Button type="submit" className="w-full" disabled={isSubmitting || !consentGiven}>
              {isSubmitting ? "Enviando..." : "Confirmar cadastro"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
