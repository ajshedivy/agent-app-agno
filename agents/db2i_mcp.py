import asyncio
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_path = "/Users/adamshedivy/Documents/IBM/sandbox/oss/ai/db2i-ai/db2i-agents/examples/mcp/db2i-mcp-server"


async def run_agent(message: str) -> None:
    """Run the filesystem agent with the given message."""

    # MCP parameters for the Filesystem server accessed via `npx`
    server_params = StdioServerParameters(
        command="/Users/adamshedivy/.local/bin/uv",
        args=[
            "--directory",
            server_path,
            "run",
            "db2i-mcp-server",
        ],
    )

    # Create a client session to connect to the MCP server
    async with MCPTools(server_params=server_params) as mcp_tools:
        agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            tools=[mcp_tools],
            instructions=dedent(
                """\
                You are a Db2i Database assistant. Help users answer questions about the database.
                here are the tools you can use:
                - `list-usable-tables`: List the tables in the database.
                - `describe-table`: Describe a table in the database.
                - `run-sql-query`: Run a SQL query on the database.
                
                When a user asks a question, you can use the tools to answer it. Follow these steps:
                1. Identify the user's question and determine if it can be answered using the tools.
                2. always call `list-usable-tables` first to get the list of tables in the database.
                3. Once you have the list of tables, you can use `describe-table` to get more information about a specific table.
                4. If an SQL query is needed, use the table references and column information from `list-usable-tables` and `describe-table` to construct the query.
                    a. DO NOT HALLUCINATE table names or column names.
                5. Use `run-sql-query` to execute the SQL query and get the results.
                6. Format the results in a user-friendly way and return them to the user.

                \
            """
            ),
            markdown=True,
            show_tool_calls=True,
        )

        # Run the agent
        await agent.aprint_response(message, stream=True)


# Example usage
if __name__ == "__main__":
    # Basic example - exploring project license
    asyncio.run(run_agent("which employee has the highest salary?"))
