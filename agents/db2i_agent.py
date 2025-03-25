from agno.agent import Agent
from tools.db2i import Db2iTools
from dotenv import load_dotenv
import os


def load_connection():
    """Load database connection details from environment variables"""
    connection_details = {
        "host": os.getenv("HOST"),
        "user": os.getenv("DB_USER"),
        "port": os.getenv("PORT", 8075),
        "password": os.getenv("PASSWORD"),
        # "schema": os.getenv("SCHEMA"),
    }
    return connection_details


load_dotenv()
details = load_connection()

tools = Db2iTools(
    schema="SAMPLE", db_details=details, run_sql_query=False
)
for tool in tools.functions:
    print(tool)

async def main():

    agent = Agent(tools=[tools], show_tool_calls=True, debug_mode=True)
    response = await agent.arun("List the tables in the SAMPLE database")
    # print(response.to_json())
    agent.print_response("List the tables in my schema and return", markdown=True)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())