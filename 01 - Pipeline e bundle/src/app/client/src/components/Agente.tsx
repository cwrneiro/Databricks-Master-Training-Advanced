import { marked } from 'marked';
import { useEffect, useRef, useState } from 'react';
import { api, type ChatResult } from '../lib/api';

interface Mensagem {
  autor: 'atendente' | 'agente';
  texto: string;
  tools?: string[];
  estado?: 'aguardando' | 'pronta' | 'erro';
  inicio?: number;
}

interface Props {
  rascunho: string;
  onRascunho: (t: string) => void;
}

// O texto do agente vem em markdown; o HTML cru é escapado antes, para não virar marcação.
const html = (md: string) =>
  marked.parse(md.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'), { async: false });

function nomeTool(t: string) {
  if (t.startsWith('genie')) return 'Tabelas (Genie)';
  if (t.includes('documentos_idx')) return 'Documentos';
  if (t === 'remember' || t === 'recall') return 'Memória';
  return t;
}

const espera = (ms: number) => new Promise((r) => setTimeout(r, ms));

export function Agente({ rascunho, onRascunho }: Props) {
  const [sessao, setSessao] = useState(() => crypto.randomUUID());
  const [msgs, setMsgs] = useState<Mensagem[]>([]);
  const [agora, setAgora] = useState(Date.now());
  const fim = useRef<HTMLDivElement>(null);
  const campo = useRef<HTMLTextAreaElement>(null);
  const aguardando = msgs.some((m) => m.estado === 'aguardando');

  useEffect(() => {
    if (!aguardando) return;
    const t = setInterval(() => setAgora(Date.now()), 1000);
    return () => clearInterval(t);
  }, [aguardando]);

  useEffect(() => {
    // Sem retorno: no Chrome novo scrollIntoView devolve uma Promise, que o React tentaria chamar como cleanup.
    void fim.current?.scrollIntoView({ block: 'end' });
  }, [msgs.length]);
  useEffect(() => {
    if (rascunho) campo.current?.focus();
  }, [rascunho]);

  const atualizarUltima = (m: Partial<Mensagem>) => setMsgs((ms) => [...ms.slice(0, -1), { ...ms[ms.length - 1], ...m }]);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    const texto = rascunho.trim();
    if (!texto || aguardando) return;
    onRascunho('');
    const s = sessao;
    setMsgs((ms) => [...ms, { autor: 'atendente', texto }, { autor: 'agente', texto: '', estado: 'aguardando', inicio: Date.now() }]);
    try {
      const { id } = await api<{ id: string }>('/api/chat', { method: 'POST', body: { session_id: s, mensagem: texto } });
      // A pergunta roda em background no agente; aqui só acompanhamos.
      for (;;) {
        await espera(3000);
        const r = await api<ChatResult>(`/api/chat/${id}`);
        if (r.status === 'completed') return atualizarUltima({ texto: r.resposta ?? '(sem resposta)', tools: r.tools, estado: 'pronta' });
        if (r.status === 'failed' || r.status === 'cancelled')
          return atualizarUltima({ texto: 'O agente não conseguiu responder. Tente de novo ou reformule a pergunta.', estado: 'erro' });
      }
    } catch (err) {
      atualizarUltima({ texto: (err as Error).message, estado: 'erro' });
    }
  }

  return (
    <section className="folha agente" aria-labelledby="agente-titulo">
      <div className="faixa-titulo faixa-com-acao">
        <h2 id="agente-titulo">Agente Vida+</h2>
        <button
          type="button"
          className="botao-faixa"
          disabled={aguardando || msgs.length === 0}
          onClick={() => {
            setSessao(crypto.randomUUID());
            setMsgs([]);
          }}
        >
          Nova conversa
        </button>
      </div>

      <div className="rolagem conversa" aria-live="polite">
        {msgs.length === 0 && (
          <div className="aviso conversa-vazia">
            Pergunte sobre regras e prazos (documentos da operadora) ou sobre números das guias (tabelas).
            <span>Exemplos: “Qual o prazo de uma ressonância magnética?” · “Quantas tomografias estão em análise?”</span>
          </div>
        )}
        {msgs.map((m, i) =>
          m.autor === 'atendente' ? (
            <div key={i} className="msg msg-atendente">
              <span className="rotulo">Atendente</span>
              <p>{m.texto}</p>
            </div>
          ) : (
            <div key={i} className={`msg msg-agente${m.estado === 'erro' ? ' msg-erro' : ''}${m.estado === 'aguardando' ? ' msg-espera' : ''}`}>
              <span className="rotulo">
                Agente
                {m.tools?.map((t) => (
                  <span key={t} className="fonte">{nomeTool(t)}</span>
                ))}
              </span>
              {m.estado === 'aguardando' ? (
                <p>
                  <span className="pontos" aria-hidden="true"><i /><i /><i /></span>
                  Consultando… <span className="mono">{Math.max(0, Math.floor((agora - (m.inicio ?? agora)) / 1000))} s</span>
                  <span className="msg-nota">Perguntas sobre números consultam as tabelas e podem levar alguns minutos. A guia ao lado continua disponível.</span>
                </p>
              ) : m.estado === 'erro' ? (
                <p role="alert">{m.texto}</p>
              ) : (
                <div className="md" dangerouslySetInnerHTML={{ __html: html(m.texto) }} />
              )}
            </div>
          ),
        )}
        <div ref={fim} />
      </div>

      <form className="envio" onSubmit={(e) => void enviar(e)}>
        <label className="rotulo" htmlFor="mensagem">Pergunta ao agente</label>
        <textarea
          id="mensagem"
          ref={campo}
          rows={2}
          value={rascunho}
          maxLength={4000}
          onChange={(e) => onRascunho(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              e.currentTarget.form?.requestSubmit();
            }
          }}
          placeholder="Escreva e tecle Enter"
        />
        <button type="submit" className="botao" disabled={aguardando || !rascunho.trim()}>
          {aguardando ? 'Aguardando…' : 'Enviar'}
        </button>
      </form>
    </section>
  );
}
