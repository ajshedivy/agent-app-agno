import asyncio

import nest_asyncio
import streamlit as st
from agno.agent import Agent
from agno.tools.streamlit.components import check_password
from agno.utils.log import logger

from agents.db2i_agent import db2i_agent_session, get_db2i_agent
from ui.css import CUSTOM_CSS
from ui.utils import (
    add_message,
    create_system,
    display_tool_calls,
    initialize_agent_session_state,
    selected_model,
    session_selector,
    system_selector,
    utilities_widget,
)


def get_connection_details():
    """Get connection details from session state or environment variables."""
    # Check if we have a selected system in session state
    if (
        hasattr(st.session_state, "selected_system")
        and st.session_state.selected_system
    ):
        system = st.session_state.selected_system
        connection_details = {
            "host": system["host"],
            "user": system["user"],
            "password": system["password"],
            "port": system["port"],
            "schema": system["schema"],
        }
        return connection_details

    # Fallback to environment variables
    import os

    from dotenv import load_dotenv

    load_dotenv()
    connection_details = {
        "host": os.getenv("HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("PASSWORD"),
        "port": os.getenv("PORT", 8075),
        "schema": os.getenv("SCHEMA"),
    }
    return connection_details


nest_asyncio.apply()

st.set_page_config(
    page_title="Db2i: The Db2i Agent",
    page_icon="📁",
    layout="wide",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
agent_name = "db2i"


async def header():
    st.markdown("<h1 class='heading'>Db2i</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subheading'>A Db2i agent uses a MCP server to gather relevant database knowledge.</p>",
        unsafe_allow_html=True,
    )


async def body() -> None:
    ####################################################################
    # Initialize User and Session State
    ####################################################################
    user_id = st.sidebar.text_input(":technologist: Username", value="Ava")

    ####################################################################
    # System Connection UI Components
    ####################################################################
    # Add a system creator form
    await create_system()

    # Add a system selector dropdown
    await system_selector()

    # Display selected system information
    if "selected_system" in st.session_state and st.session_state.selected_system:
        system = st.session_state.selected_system
        st.sidebar.success(f"Connected to: {system['host']}:{system['port']}")
    else:
        st.sidebar.warning(
            "No system selected. Please select or create a system connection."
        )

    ####################################################################
    # Model selector
    ####################################################################
    model_id = await selected_model()

    ####################################################################
    # Initialize Agent (without tools initially)
    ####################################################################
    db2i: Agent
    if (
        agent_name not in st.session_state
        or st.session_state[agent_name]["agent"] is None
        or st.session_state.get("selected_model") != model_id
    ):
        logger.info("---*--- Creating Db2i Agent ---*---")
        db2i = get_db2i_agent(model_id=model_id, user_id=user_id, use_env=True)
        st.session_state[agent_name]["agent"] = db2i
        st.session_state["selected_model"] = model_id
    else:
        db2i = st.session_state[agent_name]["agent"]

    ####################################################################
    # Load Agent Session from the database
    ####################################################################
    try:
        st.session_state[agent_name]["session_id"] = db2i.load_session()
    except Exception:
        st.warning("Could not create Agent session, is the database running?")
        return

    ####################################################################
    # Load agent runs (i.e. chat history) from memory if messages is empty
    ####################################################################
    if db2i.memory:
        agent_runs = db2i.memory.runs
        if len(agent_runs) > 0:
            # If there are runs, load the messages
            logger.debug("Loading run history")
            # Clear existing messages
            st.session_state[agent_name]["messages"] = []
            # Loop through the runs and add the messages to the messages list
            for agent_run in agent_runs:
                if agent_run.message is not None:
                    await add_message(
                        agent_name,
                        agent_run.message.role,
                        str(agent_run.message.content),
                    )
                if agent_run.response is not None:
                    await add_message(
                        agent_name,
                        "assistant",
                        str(agent_run.response.content),
                        agent_run.response.tools,
                    )

    ####################################################################
    # Get user input
    ####################################################################
    if prompt := st.chat_input("✨ How can I help with your database, bestie?"):
        await add_message(agent_name, "user", prompt)

    ####################################################################
    # Show example inputs
    ####################################################################
    # TODO: Implement database-specific example inputs
    # await example_inputs(agent_name)

    ####################################################################
    # Display agent messages
    ####################################################################
    for message in st.session_state[agent_name]["messages"]:
        if message["role"] in ["user", "assistant"]:
            _content = message["content"]
            if _content is not None:
                with st.chat_message(message["role"]):
                    # Display tool calls if they exist in the message
                    if "tool_calls" in message and message["tool_calls"]:
                        display_tool_calls(st.empty(), message["tool_calls"])
                    st.markdown(_content)

    ####################################################################
    # Generate response for user message
    ####################################################################
    last_message = (
        st.session_state[agent_name]["messages"][-1]
        if st.session_state[agent_name]["messages"]
        else None
    )
    if last_message and last_message.get("role") == "user":
        user_message = last_message["content"]
        logger.info(f"Responding to message: {user_message}")
        with st.chat_message("assistant"):
            tool_calls_container = st.empty()
            resp_container = st.empty()
            with st.spinner(":thinking_face: Thinking..."):
                response = ""
                try:
                    # Get current session ID from Streamlit state
                    current_session_id = st.session_state[agent_name].get("session_id")
                    logger.info(f"Using session ID: {current_session_id}")

                    connection_details = get_connection_details()

                    # Create temporary agent with existing session ID
                    async with db2i_agent_session(
                        model_id=model_id,
                        user_id=user_id,
                        session_id=current_session_id,  # Pass existing session ID for continuity
                        debug_mode=True,
                        connection_details=connection_details,
                        use_env=False if connection_details else True,
                    ) as temp_agent:
                        # Process the request with temporary agent that has full context
                        run_response = await temp_agent.arun(user_message, stream=True)
                        async for resp_chunk in run_response:
                            # Display tool calls if available
                            if resp_chunk.tools and len(resp_chunk.tools) > 0:
                                display_tool_calls(
                                    tool_calls_container, resp_chunk.tools
                                )

                            # Display response
                            if resp_chunk.content is not None:
                                response += resp_chunk.content
                                resp_container.markdown(response)

                        # Save the response to chat history in Streamlit
                        if temp_agent.run_response is not None:
                            await add_message(
                                agent_name,
                                "assistant",
                                response,
                                temp_agent.run_response.tools,
                            )
                        else:
                            await add_message(agent_name, "assistant", response)

                        # Update session ID in case it changed
                        # (This maintains continuity for the next query)
                        st.session_state[agent_name][
                            "session_id"
                        ] = temp_agent.session_id

                except Exception as e:
                    logger.error(f"Error during agent run: {str(e)}", exc_info=True)
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    await add_message(agent_name, "assistant", error_message)
                    st.error(error_message)

    ####################################################################
    # Knowledge widget
    ####################################################################
    # TODO: Implement database-specific knowledge widget
    # await knowledge_widget(agent_name, db2i)

    ####################################################################
    # Session selector
    ####################################################################
    await session_selector(agent_name, db2i, get_db2i_agent, user_id, model_id)

    ####################################################################
    # About section
    ####################################################################
    # TODO: Implement database-specific utilities widget
    await utilities_widget(agent_name, db2i)


async def main():
    await initialize_agent_session_state(agent_name)
    await header()
    await body()


if __name__ == "__main__":
    if check_password():
        asyncio.run(main())
