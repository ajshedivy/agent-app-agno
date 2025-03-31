## Agent App

This repo contains the code for a production-grade agentic system built with:

1. A Streamlit UI
2. A FastAPI server
3. A Postgres database with the PgVector extension.

You can run the agent app in 2 environments:

1. A development environment running locally on docker
2. A production environment running on AWS ECS

## Agent Integration
This repo has two prebuilt agents that can be used out of the box with OpenAI: 
- `Sage`: A knowledge agent that uses Agentic RAG to deliver context-rich answers from a knowledge base.
- `Scholar`: A research agent that uses DuckDuckGo (and optionally Exa) to deliver in-depth answers about any topic.

### Db2i Agent (in Progress)
TODO:
- Update MCPTools to use official MCP tools package
- Add support for other models, including ollama, watsonx, and others
- System admin support in UI
- deploy on Power


## Setup

1. [Install uv](https://docs.astral.sh/uv/#getting-started) for managing the python environment.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install dependencies:

```sh
./scripts/dev_setup.sh
```

3. Activate virtual environment

```
source .venv/bin/activate
```

## Run application locally using docker or podman

1. Install [docker desktop](https://www.docker.com/products/docker-desktop), or [Podmand desktop](https://podman.io/) if you prefer.

2. Export API keys

Required: Set `OLLAMA_API_BASE` or the `OPENAI_API_KEY` environment variable

```sh
export OPENAI_API_KEY=***
```

```sh
export OLLAMA_API_BASE=http://OLLAMA_URL:11434
```
> Note: you can use Ollama running locally on your host machine:
> ```sh
> export OLLAMA_API_BASE="http://host.docker.internal:11434"
> ```


Optional: Set the `EXA_API_KEY` if you'd like to use Exa search

```sh
export EXA_API_KEY=***
```
---
### Build the Development Images

1. Build the container images locally:

    ```sh
    ag ws up --env dev --infra docker --type image --force
    ```

2. Start/Restart containers:

    ```sh
    ag ws restart --env dev --infra docker --type container
    ```

- This will run 3 containers:
  - Streamlit on [localhost:8501](http://localhost:8501)
  - FastAPI on [localhost:8000](http://localhost:8000/docs)
  - Postgres on  [localhost:5432](http://localhost:5432)
- Open [localhost:8501](http://localhost:8501) to view the Streamlit App.
- Open [localhost:8000/docs](http://localhost:8000/docs) to view the FastAPI docs.

4. Stop the workspace using:

    ```sh
    ag ws down
    ```

## More Information

Learn more about this application and how to customize it in the [Agno Workspaces](https://docs.agno.com/workspaces) documentaion
