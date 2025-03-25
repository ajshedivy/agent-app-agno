from textwrap import dedent
from agno.agent import Agent
from tools.db2i import SQLTools  # Db2iTools
from dotenv import load_dotenv
import os


load_dotenv()
tools = SQLTools(
    schema=os.getenv("SCHEMA"),
    host=os.getenv("HOST"),
    port=os.getenv("PORT", 8075),
    user=os.getenv("DB_USER"),
    password=os.getenv("PASSWORD"),
)
for tool in tools.functions:
    print(tool)


async def main():

    agent = Agent(
        tools=[tools],
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
        show_tool_calls=True,
        debug_mode=True,
    )
    await agent.aprint_response(
        "what employee has the highest avg salary?", markdown=True
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
