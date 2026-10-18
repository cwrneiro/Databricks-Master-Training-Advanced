import { STATUS, dataHora, procedimento, type Autorizacao, type Status } from '../lib/api';

interface Props {
  contagem: Partial<Record<Status, number>>;
  autorizacoes: Autorizacao[] | null;
  erro: string | null;
  atualizado: string | null;
  busca: string;
  filtro: Status | null;
  selecionada: string | null;
  onFiltro: (s: Status | null) => void;
  onSelecionar: (a: Autorizacao) => void;
}

const ORDEM: Status[] = ['solicitada', 'em_analise', 'aprovada', 'negada'];

export function Fichario({ contagem, autorizacoes, erro, atualizado, busca, filtro, selecionada, onFiltro, onSelecionar }: Props) {
  const total = ORDEM.reduce((s, k) => s + (contagem[k] ?? 0), 0);
  return (
    <section className="folha" aria-labelledby="fichario-titulo">
      <h2 id="fichario-titulo" className="faixa-titulo">Fichário de guias</h2>
      <div className="quadro" role="group" aria-label="Guias por situação">
        {ORDEM.map((s) => (
          <button
            key={s}
            type="button"
            className={`quadro-caixa st-${s}`}
            aria-pressed={filtro === s}
            onClick={() => onFiltro(filtro === s ? null : s)}
          >
            <span className="rotulo">{STATUS[s]}</span>
            <b>{autorizacoes ? (contagem[s] ?? 0) : '–'}</b>
          </button>
        ))}
        <div className="quadro-total">
          <span className="rotulo">Total de guias</span>
          <b>{autorizacoes ? total : '–'}</b>
        </div>
      </div>

      <div className="rolagem">
        {erro && (
          <p className="aviso aviso-erro" role="alert">
            {erro}
            {autorizacoes && atualizado && <span>A lista abaixo é a de {atualizado}, a última que carregou.</span>}
          </p>
        )}
        {!erro && !autorizacoes && (
          <ul className="fichas" aria-hidden="true">
            {Array.from({ length: 8 }, (_, i) => <li key={i} className="ficha ficha-vazia" />)}
          </ul>
        )}
        {!erro && autorizacoes && autorizacoes.length === 0 && (
          <p className="aviso">
            {busca ? (
              <>
                Nenhuma guia encontrada para “{busca}”{filtro ? ` com a situação ${STATUS[filtro].toLowerCase()}` : ''}.
                <span>Confira o número, ou busque pelo beneficiário (BEN-) ou prestador (PRE-).</span>
              </>
            ) : filtro ? (
              <>
                Nenhuma guia {STATUS[filtro].toLowerCase()} agora.
                <span>Clique de novo em “{STATUS[filtro]}” no quadro para ver todas.</span>
              </>
            ) : (
              <>
                Nenhuma guia no sistema ainda.
                <span>Os lotes chegam a cada 10 minutos; a lista se atualiza sozinha.</span>
              </>
            )}
          </p>
        )}
        {autorizacoes && autorizacoes.length > 0 && (
          <ul className="fichas">
            {autorizacoes.map((a) => (
              <li key={a.autorizacao_id}>
                <button
                  type="button"
                  className="ficha"
                  aria-current={a.autorizacao_id === selecionada}
                  onClick={() => onSelecionar(a)}
                >
                  <span className="ficha-id mono">{a.autorizacao_id}</span>
                  <span className={`etiqueta st-${a.status}`}>{STATUS[a.status]}</span>
                  <span className="ficha-hora mono">{dataHora(a.event_ts)}</span>
                  <span className="ficha-meta">
                    {procedimento(a.procedimento)} · <span className="mono">{a.prestador_id}</span> ·{' '}
                    <span className="mono">{a.beneficiario_id}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
