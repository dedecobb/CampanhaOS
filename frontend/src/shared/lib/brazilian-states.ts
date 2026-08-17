/**
 * Preenchimento automático de alguns celulares (confirmado: iOS Safari)
 * insere o NOME COMPLETO do estado no campo de UF (ex: "Mato Grosso") em
 * vez da sigla de 2 letras — cortar isso ingenuamente pros 2 primeiros
 * caracteres dá errado (ex: "Mato Grosso" cortado vira "MA", que é
 * Maranhão, não Mato Grosso). Esse mapa resolve isso corretamente.
 */
const STATE_NAME_TO_UF: Record<string, string> = {
  acre: "AC",
  alagoas: "AL",
  amapa: "AP",
  amazonas: "AM",
  bahia: "BA",
  ceara: "CE",
  "distrito federal": "DF",
  "espirito santo": "ES",
  goias: "GO",
  maranhao: "MA",
  "mato grosso": "MT",
  "mato grosso do sul": "MS",
  "minas gerais": "MG",
  para: "PA",
  paraiba: "PB",
  parana: "PR",
  pernambuco: "PE",
  piaui: "PI",
  "rio de janeiro": "RJ",
  "rio grande do norte": "RN",
  "rio grande do sul": "RS",
  rondonia: "RO",
  roraima: "RR",
  "santa catarina": "SC",
  "sao paulo": "SP",
  sergipe: "SE",
  tocantins: "TO",
};

function stripAccents(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

/**
 * Normaliza o valor digitado/autopreenchido no campo de UF: se for um
 * nome completo de estado reconhecido (com ou sem acento, maiúsculo ou
 * minúsculo), converte pra sigla certa. Caso contrário, assume que já é
 * uma sigla (ou está sendo digitada), e só corta pra 2 caracteres como
 * proteção — nunca deixa passar mais que 2 caracteres pro backend, que
 * exige exatamente isso.
 */
export function normalizeStateInput(rawValue: string): string {
  const trimmed = rawValue.trim();
  const normalizedKey = stripAccents(trimmed).toLowerCase();

  const matchedUf = STATE_NAME_TO_UF[normalizedKey];
  if (matchedUf) {
    return matchedUf;
  }

  return trimmed.toUpperCase().slice(0, 2);
}
