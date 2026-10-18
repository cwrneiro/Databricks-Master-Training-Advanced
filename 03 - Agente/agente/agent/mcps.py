"""MCP servers to offer the agent — this is where you configure them.

``agent.py`` passes them to ``mcp_tools``, which joins them with the ``agent.toml`` servers and fetches
their tools each request.
"""

from databricks.sdk import WorkspaceClient
from databricks_langchain import DatabricksMCPServer


def build_mcp_servers(schema: str) -> list[DatabricksMCPServer]:
    """O índice de AI Search dos documentos da operadora, no schema do aluno, como tool de busca."""
    w = WorkspaceClient()
    catalog, nome = schema.split(".")
    # MCP de workspace do AI Search (antigo Vector Search). Ainda não há tipo de tool para AI Search no
    # agent.toml; por isso ele entra por código, e o SP do app precisa de SELECT no schema (grant do bundle).
    return [
        DatabricksMCPServer(
            name="documentos",
            url=f"{w.config.host}/api/2.0/mcp/ai-search/{catalog}/{nome}/documentos_idx",
            workspace_client=w,
        ),
    ]
