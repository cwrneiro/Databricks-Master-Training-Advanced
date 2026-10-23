import { useCallback, useEffect, useState } from 'react';
import { Agente } from './components/Agente';
import { Fichario } from './components/Fichario';
import { Guia } from './components/Guia';
import { api, type Autorizacao, type Status } from './lib/api';

interface Lista {
  contagem: { status: Status; total: number }[];
  autorizacoes: Autorizacao[];
}

// Os lotes chegam a cada 10 min; atualizar a cada 30 s mostra a mudança sem pesar no Postgres.
const ATUALIZAR_MS = 30_000;
const hora = new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' });

export default function App() {
  const [email, setEmail] = useState<string | null>(null);
  const [busca, setBusca] = useState('');
  const [termo, setTermo] = useState('');
  const [filtro, setFiltro] = useState<Status | null>(null);
  const [lista, setLista] = useState<Lista | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [atualizado, setAtualizado] = useState<Date | null>(null);
  const [guia, setGuia] = useState<Autorizacao | null>(null);
  const [rascunho, setRascunho] = useState('');

  useEffect(() => {
    api<{ email: string | null }>('/api/me').then((r) => setEmail(r.email)).catch(() => setEmail(null));
  }, []);

  useEffect(() => {
    const t = setTimeout(() => setTermo(busca.trim()), 250);
    return () => clearTimeout(t);
  }, [busca]);

  const carregar = useCallback(async () => {
    const qs = new URLSearchParams();
    if (termo) qs.set('busca', termo);
    if (filtro) qs.set('status', filtro);
    try {
      const r = await api<Lista>(`/api/autorizacoes?${qs}`);
      setLista(r);
      setErro(null);
      setAtualizado(new Date());
      // A guia aberta acompanha a atualização: se o status mudou, o carimbo bate de novo.
      setGuia((g) => (g ? (r.autorizacoes.find((a) => a.autorizacao_id === g.autorizacao_id) ?? g) : g));
    } catch (e) {
      setErro((e as Error).message);
    }
  }, [termo, filtro]);

  useEffect(() => {
    const primeira = setTimeout(() => void carregar(), 0);
    const t = setInterval(() => void carregar(), ATUALIZAR_MS);
    return () => {
      clearTimeout(primeira);
      clearInterval(t);
    };
  }, [carregar]);

  const contagem = Object.fromEntries((lista?.contagem ?? []).map((c) => [c.status, c.total]));

  return (
    <div className="mesa">
      <header className="cabecalho">
        <span className="marca">
          Vida<b>+</b> Saúde
        </span>
        <span className="cabecalho-sub">Central de autorizações</span>
        <span className="cabecalho-hora">
          {erro && atualizado ? `Dados de ${hora.format(atualizado)} · falha ao atualizar` : atualizado ? `Atualizado às ${hora.format(atualizado)}` : 'Carregando…'}
        </span>
        <span className="cabecalho-usuario">{email ?? 'usuário não identificado'}</span>
      </header>

      <form className="busca" role="search" onSubmit={(e) => e.preventDefault()}>
        <label className="rotulo" htmlFor="busca">Buscar guia</label>
        <input
          id="busca"
          type="search"
          value={busca}
          maxLength={40}
          onChange={(e) => setBusca(e.target.value.toUpperCase())}
          placeholder="AUT-00137, BEN-0532 ou PRE-014"
          autoComplete="off"
        />
      </form>

      <main className="colunas">
        <Fichario
          contagem={contagem}
          autorizacoes={lista?.autorizacoes ?? null}
          erro={erro}
          atualizado={atualizado ? hora.format(atualizado) : null}
          busca={termo}
          filtro={filtro}
          selecionada={guia?.autorizacao_id ?? null}
          onFiltro={setFiltro}
          onSelecionar={(a) => {
            setGuia(a);
            // Em tela estreita a guia fica abaixo do fichário: leva o atendente até ela.
            if (window.matchMedia('(max-width: 1100px)').matches)
              requestAnimationFrame(() => void document.getElementById('guia')?.scrollIntoView({ block: 'start' }));
          }}
        />
        <Guia guia={guia} onPerguntar={setRascunho} />
        <Agente rascunho={rascunho} onRascunho={setRascunho} />
      </main>
    </div>
  );
}
