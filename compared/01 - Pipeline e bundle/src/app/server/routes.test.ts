import { beforeAll, describe, expect, test } from 'vitest';

let routes: typeof import('./routes');
beforeAll(async () => {
  delete process.env.PG_SCHEMA;
  process.env.AGENT_APP = 'agent-bricks-acarneiro';
  routes = await import('./routes');
});

test('schema do Postgres sai do nome do app do agente', () => {
  expect(routes.SCHEMA).toBe('acarneiro');
});

describe('toChat', () => {
  test('resposta final e tools de uma invocação completa', () => {
    const r = routes.toChat({
      status: 'completed',
      output: {
        output: [
          { type: 'ai', content: '' },
          { type: 'tool', name: 'genie_agent_ask', content: [] },
          { type: 'tool', name: 'genie_agent_ask', content: [] },
          { type: 'ai', content: '**11** em análise' },
        ],
      },
    });
    expect(r).toEqual({ status: 'completed', resposta: '**11** em análise', tools: ['genie_agent_ask'] });
  });

  test('em andamento: sem resposta', () => {
    expect(routes.toChat({ status: 'queued' })).toEqual({ status: 'queued', resposta: null, tools: [] });
  });
});
