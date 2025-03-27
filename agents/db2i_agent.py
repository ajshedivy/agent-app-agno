from contextlib import asynccontextmanager
from textwrap import dedent
from typing import Any, AsyncGenerator, Dict, Union
from agno.agent import Agent
from agno.tools.mcp import MCPTools
from agno.storage.agent.postgres import PostgresAgentStorage
from db.session import db_url
from dotenv import load_dotenv
from agno.models.openai import OpenAIChat
from mcp import StdioServerParameters
import os

load_dotenv()
server_path = "/app/agents/db2i-agents/examples/mcp/db2i-mcp-server"


def get_server_params(
    server_path: str = server_path, connection_details: Dict[str, Any] = None, use_env: bool = False
) -> StdioServerParameters:
    
    if use_env:
        return StdioServerParameters(
            command="/usr/local/bin/uv",
            args=[
                "--directory",
                server_path,
                "run",
                "db2i-mcp-server",
                "--use-env"
            ],
        )

    server_params = StdioServerParameters(
        command="uv",
        args=[
            "--directory",
            server_path,
            "run",
            "db2i-mcp-server",
            "--host",
            connection_details["host"],
            "--user",
            connection_details["user"],
            "--password",
            connection_details["password"],
            "--port",
            connection_details.get("port", 8075),
            "--schema",
            connection_details["schema"],
        ],
    )
    return server_params


def create_db2i_agent(
    model_id: str = "gpt-4o",
    user_id: str = None,
    session_id: str = None,
    tools = None,
    debug_mode: bool = True,
) -> Agent:
    """
    Create a Db2i agent with the specified configuration.
    This function centralizes agent creation logic for reuse.
    
    Args:
        model_id: The model ID to use
        user_id: The user ID
        session_id: The session ID
        tools: List of tools to add to the agent
        debug_mode: Whether to enable debug mode
        
    Returns:
        Agent: Configured Db2i agent
    """
    additional_context = ""
    if user_id:
        additional_context += "<context>"
        additional_context += f"You are interacting with the user: {user_id}"
        additional_context += "</context>"
    
    # Use empty list if tools is None
    if tools is None:
        tools = []
    
    return Agent(
        name="Db2i Agent",
        agent_id="db2i-agent",
        model=OpenAIChat(id=model_id),
        user_id=user_id,
        session_id=session_id,
        tools=tools,
        storage=PostgresAgentStorage(table_name="db2i_sessions", db_url=db_url),
        instructions=dedent(
            """\
                You are a Db2i Database assistant. Help users answer questions about the database.
                here are the tools you can use:
                - `list-tables`: List the tables in the database.
                - `describe-table`: Describe a table in the database.
                - `run-sql`: Run a SQL query on the database.
                
                When a user asks a question, you can use the tools to answer it. Follow these steps:
                1. Identify the user's question and determine if it can be answered using the tools.
                2. always call `list-tables` first to get the list of tables in the database.
                3. Once you have the list of tables, you can use `describe-table` to get more information about a specific table.
                4. If an SQL query is needed, use the table references and column information from `list-tables` and `describe-table` to construct the query.
                    a. DO NOT HALLUCINATE table names or column names.
                    b. The query MUST follow valid Db2i SQL syntax
                    c. think carefully about the query you are constructing and how the logic of the query works. Take your time.
                5. Use `run-sql` to execute the SQL query and get the results.
                6. Format the results in a user-friendly way and return them to the user.

                \
            """
        ),
        add_context=additional_context,
        add_history_to_messages=True,
        num_history_responses=3,
        show_tool_calls=True,
        debug_mode=debug_mode,
        markdown=True,
    )


@asynccontextmanager
async def db2i_agent_session(
    model_id: str = "gpt-4o",
    user_id: str = None,
    session_id: str = None,
    debug_mode: bool = True,
    connection_details: Dict[str, Any] = None,
    use_env: bool = False
) -> AsyncGenerator[Agent, None]:
    """
    Context manager that creates and yields a Db2i agent with MCP tools.
    
    Usage:
        async with db2i_agent_session(model_id="gpt-4o", use_env=True) as agent:
            response = await agent.arun("What tables are available?")
    
    Args:
        model_id (str): The model ID to use for the agent.
        user_id (str): The user ID for the agent.
        session_id (str): The session ID for the agent.
        debug_mode (bool): Whether to enable debug mode.
        connection_details (Dict[str, Any]): Connection details for the Db2i database.
        use_env (bool): Whether to use environment variables for connection details.

    Yields:
        Agent: A configured Db2i agent with initialized MCP tools.
    """
    server_params = get_server_params(
        server_path=server_path, connection_details=connection_details, use_env=use_env
    )

    # Create MCPTools as a context manager to ensure proper cleanup
    async with MCPTools(server_params=server_params) as mcp_tools:
        # Create agent with the active MCP tools
        agent = create_db2i_agent(
            model_id=model_id,
            user_id=user_id,
            session_id=session_id,
            tools=[mcp_tools],
            debug_mode=debug_mode
        )

        try:
            yield agent
        finally:
            # Additional cleanup if needed when the context manager exits
            pass


def get_db2i_agent(
    model_id: str = "gpt-4o",
    user_id: str = None,
    session_id: str = None,
    debug_mode: bool = True,
    connection_details: Dict[str, Any] = None,
    use_env: bool = False
) -> Agent:
    """
    Get a Db2i agent with the specified model ID and connection details,
    without active MCP tools (these must be added later).

    Args:
        model_id (str): The model ID to use for the agent.
        user_id (str): The user ID for the agent.
        session_id (str): The session ID for the agent.
        debug_mode (bool): Whether to enable debug mode.
        connection_details (Dict[str, Any]): Connection details for the Db2i database.
        use_env (bool): Whether to use environment variables.

    Returns:
        Agent: A configured Db2i agent without MCP tools.
    """
    # Create agent with empty tools list - MCP tools must be added at runtime
    return create_db2i_agent(
        model_id=model_id,
        user_id=user_id,
        session_id=session_id,
        tools=[],  # No tools initially
        debug_mode=debug_mode
    )