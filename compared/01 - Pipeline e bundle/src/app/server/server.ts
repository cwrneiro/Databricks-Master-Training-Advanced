// App da Vida+ Saúde: status das autorizações (synced table), observações do atendente (Lakebase) e chat com o agente.
import { createApp, lakebase, server } from '@databricks/appkit';
import { setupRoutes } from './routes';

createApp({
  plugins: [lakebase(), server()],
  onPluginsReady(appkit) {
    setupRoutes(appkit);
  },
}).catch(console.error);
