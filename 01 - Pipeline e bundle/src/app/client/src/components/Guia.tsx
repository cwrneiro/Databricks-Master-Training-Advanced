import { useEffect, useState } from 'react';
import { STATUS, api, dataHoraAno, procedimento, type Autorizacao, type Observacao } from '../lib/api';

interface Props {
  guia: Autorizacao | null;
  onPerguntar: (texto: string) => void;
}

export function Guia({ guia, onPerguntar }: Props) {
  const [obs, setObs] = useState<Observacao[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [texto, setTexto] = useState('');
  const [salvando, setSalvando] = useState(false);
  const id = guia?.autorizacao_id;

  useEffect(() => {
    if (!id) return;
    let vivo = true;
    setObs(null);
    setErro(null);
    api<Observacao[]>(`/api/autorizacoes/${id}/observacoes`)
      .then((r) => vivo && setObs(r))
      .catch((e: Error) => vivo && setErro(e.message));
    return () => {
      vivo = false;
    };
  }, [id]);

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    if (!id || !texto.trim()) return;
    setSalvando(true);
    setErro(null);
    try {
      const nova = await api<Observacao>(`/api/autorizacoes/${id}/observacoes`, { method: 'POST', body: { texto } });
      setObs((o) => [nova, ...(o ?? [])]);
      setTexto('');
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setSalvando(false);
    }
  }

  if (!guia)
    return (
      <section className="folha guia" aria-labelledby="guia-titulo">
        <h2 id="guia-titulo" className="faixa-titulo">Guia aberta</h2>
        <p className="aviso guia-vazia">
          Nenhuma guia aberta.
          <span>Busque pelo número ou escolha uma guia no fichário.</span>
        </p>
      </section>
    );

  return (
    <section id="guia" className="folha guia" aria-labelledby="guia-titulo">
      <h2 id="guia-titulo" className="faixa-titulo">Guia aberta · {guia.autorizacao_id}</h2>
      <div className="rolagem guia-corpo">
        <div className="guia-cabeca">
          <div>
            <h3>Guia de autorização prévia</h3>
            <p className="rotulo">Vida+ Saúde · central de autorizações</p>
          </div>
          {/* key por status: o carimbo bate de novo quando a situação muda */}
          <div key={`${guia.autorizacao_id}-${guia.status}`} className={`carimbo st-${guia.status}`} role="img" aria-label={`Situação: ${STATUS[guia.status]}`}>
            {STATUS[guia.status]}
          </div>
        </div>

        <div className="campos">
          <Campo n={1} rotulo="Número da guia" valor={guia.autorizacao_id} mono />
          <Campo n={2} rotulo="Último evento" valor={dataHoraAno(guia.event_ts)} mono />
          <Campo n={3} rotulo="Situação" valor={STATUS[guia.status]} />
          <div className="campos-faixa">Beneficiário e prestador</div>
          <Campo n={4} rotulo="Beneficiário" valor={guia.beneficiario_id} mono largo />
          <Campo n={5} rotulo="Prestador solicitante" valor={guia.prestador_id} mono largo />
          <div className="campos-faixa">Procedimento solicitado</div>
          <Campo n={6} rotulo="Procedimento" valor={procedimento(guia.procedimento)} inteiro />
          <div className="campos-faixa">Observações do atendente</div>
          <div className="campo campo-inteiro">
            <span className="rotulo">7 - Observações</span>
            {erro && <p className="aviso aviso-erro" role="alert">{erro}</p>}
            {!erro && !obs && <p className="linha-espera" aria-label="Carregando observações" />}
            {obs && obs.length === 0 && <p className="obs-vazia">Sem observações nesta guia.</p>}
            {obs?.map((o) => (
              <div key={o.id} className="obs">
                <p>{o.texto}</p>
                <span className="obs-autor">
                  {o.autor} · <span className="mono">{dataHoraAno(o.criado_em)}</span>
                </span>
              </div>
            ))}
          </div>
          <form className="campo campo-inteiro" onSubmit={(e) => void salvar(e)}>
            <label className="rotulo" htmlFor="nova-obs">8 - Nova observação</label>
            <textarea
              id="nova-obs"
              value={texto}
              maxLength={2000}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="O que o prestador disse nesta ligação"
            />
            <div className="acoes">
              <button
                type="button"
                className="botao botao-claro"
                onClick={() =>
                  onPerguntar(
                    `Sobre a guia ${guia.autorizacao_id} (${procedimento(guia.procedimento)}, ${STATUS[guia.status].toLowerCase()}): `,
                  )
                }
              >
                Perguntar ao agente
              </button>
              <button type="submit" className="botao" disabled={salvando || !texto.trim()}>
                {salvando ? 'Salvando…' : 'Salvar observação'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}

function Campo(p: { n: number; rotulo: string; valor: string; mono?: boolean; largo?: boolean; inteiro?: boolean }) {
  return (
    <div className={`campo${p.largo ? ' campo-largo' : ''}${p.inteiro ? ' campo-inteiro' : ''}`}>
      <span className="rotulo">
        {p.n} - {p.rotulo}
      </span>
      <span className={`campo-valor${p.mono ? ' mono' : ''}`}>{p.valor}</span>
    </div>
  );
}
