// Chamadas ao servidor do app. Erros viram Error com a mensagem que o servidor mandou.
export type Status = 'solicitada' | 'em_analise' | 'aprovada' | 'negada';

export interface Autorizacao {
  autorizacao_id: string;
  beneficiario_id: string;
  prestador_id: string;
  procedimento: string;
  status: Status;
  event_ts: string;
}

export interface Observacao {
  id: string;
  texto: string;
  autor: string;
  criado_em: string;
}

export interface ChatResult {
  status: string;
  resposta: string | null;
  tools: string[];
}

export async function api<T>(path: string, init?: { method?: string; body?: unknown }): Promise<T> {
  const res = await fetch(path, {
    method: init?.method ?? 'GET',
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    body: init?.body ? JSON.stringify(init.body) : undefined,
  });
  const data: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const msg = data && typeof data === 'object' && 'error' in data ? String(data.error) : `Erro ${res.status}`;
    throw new Error(msg);
  }
  return data as T;
}

export const STATUS: Record<Status, string> = {
  solicitada: 'Solicitada',
  em_analise: 'Em análise',
  aprovada: 'Aprovada',
  negada: 'Negada',
};

const PROCEDIMENTOS: Record<string, string> = {
  consulta_cardiologia: 'Consulta cardiologia',
  ressonancia_magnetica: 'Ressonância magnética',
  tomografia: 'Tomografia',
  endoscopia: 'Endoscopia',
  cirurgia_ortopedica: 'Cirurgia ortopédica',
  ultrassom: 'Ultrassom',
  fisioterapia: 'Fisioterapia',
  internacao: 'Internação',
};
export const procedimento = (codigo: string) => PROCEDIMENTOS[codigo] ?? codigo;

const fmt = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
export const dataHora = (iso: string) => fmt.format(new Date(iso));
const fmtAno = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
export const dataHoraAno = (iso: string) => fmtAno.format(new Date(iso));
