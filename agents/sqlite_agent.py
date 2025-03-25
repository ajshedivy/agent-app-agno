from agno.agent import Agent
from agno.tools.sql import SQLTools

db_url = "sqlite:////Users/adamshedivy/Documents/sqlite/chinook.db"

agent = Agent(tools=[SQLTools(db_url=db_url)], debug_mode=True)
# agent.print_response("List the tables in the database", markdown=True)
response = agent.run("List the tables in the database")
print(response.to_json())