// Rotas do app. O Lakebase roda como o SP do app; o chat chama o agente com o token de quem está logado.
import { randomUUID } from 'node:crypto';
import type { Application, Request, Response } from 'express';
import { z } from 'zod';

interface AppKit {
  lakebase: { query(text: string, params?: unknown[]): Promise<{ rows: Record<string, unknown>[] }> };
  server: { extend(fn: (app: Application) => void): void };
}

// Schema do aluno no Postgres: em prod, o nome do aluno, tirado do app do agente (agent-bricks-<aluno>).
// PG_SCHEMA só existe para testar em dev, onde o schema é dev_<usuario>_<aluno>.
export const SCHEMA = process.env.PG_SCHEMA ?? (process.env.AGENT_APP ?? '').replace(/^agent-bricks-/, '');
if (!/^[a-z0-9_]+$/.test(SCHEMA)) throw new Error(`PG_SCHEMA inválido: "${SCHEMA}"`);
const STATUS = `"${SCHEMA}".autorizacao_status`;
const OBS = `"${SCHEMA}".observacao_atendente`;

const AutorizacaoId = z.string().regex(/^AUT-\d{5}$/);
const ListQuery = z.object({
  busca: z.string().trim().max(40).optional(),
  status: z.enum(['solicitada', 'em_analise', 'aprovada', 'negada']).optional(),
});
const ObsBody = z.object({ texto: z.string().trim().min(1).max(2000) });
const ChatBody = z.object({ session_id: z.string().uuid(), mensagem: z.string().trim().min(1).max(4000) });

// Erros do Postgres que o aluno resolve sozinho: viram uma mensagem que diz o que falta.
function pgError(res: Response, err: unknown, acao: string) {
  const code = (err as { code?: string }).code;
  console.error(`[lakebase] ${acao}:`, err);
  if (code === '42501')
    return void res.status(403).json({
      error: `O app ainda não tem permissão no schema ${SCHEMA} do Postgres. Rode os GRANTs do módulo 4 para o service principal do app.`,
    });
  if (code === '42P01' || code === '3F000')
    return void res.status(404).json({
      error: `Tabela não encontrada no schema ${SCHEMA}. Confira o sync do módulo 2 e a tabela observacao_atendente.`,
    });
  return void res.status(500).json({ error: `Falha ao ${acao}.` });
}

// URL do app do agente: o mesmo domínio deste app, com o nome do app do agente (recurso "agente" do bundle).
function agentUrl(req: Request) {
  const host = req.header('x-forwarded-host') ?? req.header('host') ?? '';
  return `https://${process.env.AGENT_APP}-${process.env.DATABRICKS_WORKSPACE_ID}.${host.split('.').slice(1).join('.')}`;
}

function userToken(req: Request, res: Response) {
  const token = req.header('x-forwarded-access-token');
  if (!token)
    res.status(401).json({ error: 'Sem o token do usuário. O app precisa do escopo genie (user_api_scopes) e do seu consentimento.' });
  return token;
}

interface AgentMessage { type: string; name?: string; content?: unknown }
interface AgentInvocation { status: string; output?: { output?: AgentMessage[] }; error?: unknown; detail?: unknown }

// Resposta do agente → o que a tela precisa: status, texto final e tools chamadas.
export function toChat(inv: AgentInvocation) {
  const msgs = inv.output?.output ?? [];
  const last = msgs[msgs.length - 1];
  return {
    status: inv.status,
    resposta: last?.type === 'ai' && typeof last.content === 'string' ? last.content : null,
    tools: [...new Set(msgs.filter((m) => m.type === 'tool').map((m) => m.name ?? 'tool'))],
  };
}

async function callAgent(req: Request, res: Response, path: string, body?: unknown) {
  const token = userToken(req, res);
  if (!token) return null;
  try {
    const r = await fetch(`${agentUrl(req)}${path}`, {
      method: body ? 'POST' : 'GET',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    const text = await r.text();
    if (!r.ok) {
      console.error(`[agente] ${r.status} ${path}: ${text.slice(0, 500)}`);
      res.status(502).json({ error: `O agente respondeu ${r.status}. Confira se o app ${process.env.AGENT_APP} está rodando.` });
      return null;
    }
    return JSON.parse(text) as AgentInvocation & { id?: string };
  } catch (err) {
    console.error('[agente]', err);
    res.status(502).json({ error: `Não foi possível falar com o app ${process.env.AGENT_APP}.` });
    return null;
  }
}

export function setupRoutes(appkit: AppKit) {
  const q = appkit.lakebase.query.bind(appkit.lakebase);

  appkit.server.extend((app) => {
    app.get('/api/me', (req, res) => {
      res.json({ email: req.header('x-forwarded-email') ?? null, schema: SCHEMA });
    });

    // Contagem por status + até 50 autorizações, as mais recentes primeiro.
    app.get('/api/autorizacoes', async (req, res) => {
      const parsed = ListQuery.safeParse(req.query);
      if (!parsed.success) return void res.status(400).json({ error: 'Filtro inválido.' });
      const { busca, status } = parsed.data;
      try {
        const [contagem, lista] = await Promise.all([
          q(`SELECT status, count(*)::int AS total FROM ${STATUS} GROUP BY status`),
          q(
            `SELECT autorizacao_id, beneficiario_id, prestador_id, procedimento, status, event_ts
             FROM ${STATUS}
             WHERE ($1::text IS NULL OR autorizacao_id ILIKE $1 || '%' OR beneficiario_id ILIKE $1 || '%' OR prestador_id ILIKE $1 || '%')
               AND ($2::text IS NULL OR status = $2)
             ORDER BY event_ts DESC LIMIT 50`,
            [busca || null, status ?? null],
          ),
        ]);
        res.json({ contagem: contagem.rows, autorizacoes: lista.rows });
      } catch (err) {
        pgError(res, err, 'consultar as autorizações');
      }
    });

    app.get('/api/autorizacoes/:id/observacoes', async (req, res) => {
      const id = AutorizacaoId.safeParse(req.params.id);
      if (!id.success) return void res.status(400).json({ error: 'ID de autorização inválido.' });
      try {
        const r = await q(`SELECT id, texto, autor, criado_em FROM ${OBS} WHERE autorizacao_id = $1 ORDER BY criado_em DESC`, [id.data]);
        res.json(r.rows);
      } catch (err) {
        pgError(res, err, 'ler as observações');
      }
    });

    app.post('/api/autorizacoes/:id/observacoes', async (req, res) => {
      const id = AutorizacaoId.safeParse(req.params.id);
      const body = ObsBody.safeParse(req.body);
      if (!id.success || !body.success) return void res.status(400).json({ error: 'Escreva a observação (até 2000 caracteres).' });
      const autor = req.header('x-forwarded-email');
      if (!autor) return void res.status(401).json({ error: 'Usuário não identificado.' });
      try {
        const r = await q(
          `INSERT INTO ${OBS} (autorizacao_id, texto, autor) VALUES ($1, $2, $3) RETURNING id, texto, autor, criado_em`,
          [id.data, body.data.texto, autor],
        );
        res.status(201).json(r.rows[0]);
      } catch (err) {
        pgError(res, err, 'gravar a observação');
      }
    });

    // Chat: dispara a pergunta em background no agente (a Genie pode passar de 2 min, o limite do proxy)...
    app.post('/api/chat', async (req, res) => {
      const body = ChatBody.safeParse(req.body);
      if (!body.success) return void res.status(400).json({ error: 'Mensagem inválida.' });
      const inv = await callAgent(req, res, '/api/invocations', {
        id: randomUUID(),
        session_id: body.data.session_id,
        background: true,
        // actor: dono da memória de longo prazo do agente; sem ele, a memória fica presa à sessão.
        input: { actor: req.header('x-forwarded-email'), messages: [{ role: 'user', content: body.data.mensagem }] },
      });
      if (inv) res.status(202).json({ id: inv.id, status: inv.status });
    });

    // ...e a tela pergunta o andamento até ficar completed ou failed.
    app.get('/api/chat/:id', async (req, res) => {
      const id = z.string().uuid().safeParse(req.params.id);
      if (!id.success) return void res.status(400).json({ error: 'ID inválido.' });
      const inv = await callAgent(req, res, `/api/invocations/${id.data}`);
      if (inv) res.json(toChat(inv));
    });
  });
}
