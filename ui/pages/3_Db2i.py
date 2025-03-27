import asyncio

from agents.db2i_agent import db2i_agent_session, get_db2i_agent, get_server_params
import nest_asyncio
import streamlit as st
from agno.agent import Agent
from agno.tools.streamlit.components import check_password
from agno.utils.log import logger
from agno.tools.mcp import MCPTools
from agents.sage import get_sage
from ui.css import CUSTOM_CSS
from ui.utils import (
    about_agno,
    add_message,
    display_tool_calls,
    example_inputs,
    initialize_agent_session_state,
    knowledge_widget,
    selected_model,
    session_selector,
    utilities_widget,
)

def get_connection_details():
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    connection_details = {
        "host": os.getenv("DB2I_HOST"),
        "user": os.getenv("DB2I_USER"),
        "password": os.getenv("DB2I_PASSWORD"),
        "port": os.getenv("DB2I_PORT", 8075),
        "schema": os.getenv("DB2I_SCHEMA"),
    }

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
    global mcp_tools
    ####################################################################
    # Initialize User and Session State
    ####################################################################
    user_id = st.sidebar.text_input(":technologist: Username", value="Ava")

    ####################################################################
    # Model selector
    ####################################################################
    model_id = await selected_model()

    #####################################################################
    # System selection
    ####################################################################
    # TODO

    ####################################################################
    # Initialize Agent
    ####################################################################
    
    db2i: Agent
    if (
        agent_name not in st.session_state
        or st.session_state[agent_name]["agent"] is None
        or st.session_state.get("selected_model") != model_id
    ):
        logger.debug("Initializing new agent")
        db2i = await get_db2i_agent(model_id=model_id, user_id=user_id, use_env=True)
        st.session_state[agent_name]["agent"] = db2i
        st.session_state["selected_model"] = model_id
    else:
        db2i = st.session_state[agent_name]["agent"]
        logger.debug(f"Using existing agent: {db2i}")
        
    server_params = get_server_params(use_env=True)
    logger.debug(f"Server params: {server_params}")
    # async with MCPTools(server_params=server_params) as mcp_tools:
        # logger.debug(f"Loaded MCP tools: {mcp_tools}")
        # db2i.tools.append(mcp_tools)

    ####################################################################
    # Load Agent Session from the database
    ####################################################################
    try:
        st.session_state[agent_name]["session_id"] = db2i.load_session()
    except Exception:
        st.warning("Could not create Agent session, is the database running?")
        return

    ####################################################################
    # Load agent runs (i.e. chat history) from memory is messages is empty
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
    if prompt := st.chat_input("✨ How can I help, bestie?"):
        await add_message(agent_name, "user", prompt)

    ####################################################################
    # Show example inputs
    ####################################################################
    # TODO
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
            # Create container for tool calls
            tool_calls_container = st.empty()
            resp_container = st.empty()
            with st.spinner(":thinking_face: Thinking..."):
                response = ""
                try:
                    # Run the agent and stream the response
                    run_response = await db2i.arun(user_message, stream=True)
                    async for resp_chunk in run_response:
                        # Display tool calls if available
                        if resp_chunk.tools and len(resp_chunk.tools) > 0:
                            display_tool_calls(tool_calls_container, resp_chunk.tools)

                        # Display response
                        if resp_chunk.content is not None:
                            response += resp_chunk.content
                            resp_container.markdown(response)

                    # Add the response to the messages
                    if db2i.run_response is not None:
                        await add_message(
                            agent_name, "assistant", response, db2i.run_response.tools
                        )
                    else:
                        await add_message(agent_name, "assistant", response)
                except Exception as e:
                    logger.error(f"Error during agent run: {str(e)}", exc_info=True)
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    await add_message(agent_name, "assistant", error_message)
                    st.error(error_message)

    ####################################################################
    # Knowledge widget
    ####################################################################
    # TODO
    # await knowledge_widget(agent_name, db2i)

    ####################################################################
    # Session selector
    ####################################################################
    await session_selector(agent_name, db2i, get_sage, user_id, model_id)

    ####################################################################
    # About section
    ####################################################################
    # TODO
    # await utilities_widget(agent_name, db2i)


async def body2() -> None:
    ####################################################################
    # Initialize User and Session State
    ####################################################################
    user_id = st.sidebar.text_input(":technologist: Username", value="Ava")
    st.session_state["username"] = user_id

    ####################################################################
    # Model selector
    ####################################################################
    model_id = await selected_model()
    
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize agent_memory to store complete conversation with tool calls
    if "agent_memory" not in st.session_state:
        st.session_state.agent_memory = []
        
    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "tool_calls" in message and message["tool_calls"]:
                display_tool_calls(st.empty(), message["tool_calls"])
            st.markdown(message["content"])
            
    # Handle user input
    if prompt := st.chat_input("How can I help you with your database?"):
        # Add user message to chat history for display
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Add to agent memory
        st.session_state.agent_memory.append({"role": "user", "content": prompt})
        
        # Display user message in the chat
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Process with the agent
        with st.chat_message("assistant"):
            tool_calls_container = st.empty()
            response_container = st.empty()
            
            with st.spinner("Processing your request..."):
                try:
                    # Use the context manager to ensure proper lifecycle management
                    async with db2i_agent_session(
                        model_id=model_id,
                        user_id=user_id,
                        session_id=st.session_state.get("session_id"),  # Maintain consistent session ID
                        debug_mode=True,
                        use_env=True
                    ) as agent:
                        # Reconstruct previous conversation in the agent's memory
                        # We need to manually add each message to the agent's memory
                        logger.debug(f"Adding {len(st.session_state.agent_memory)} previous messages to agent memory")
                        
                        # We only need to add previous messages, not the current user message
                        for i, msg in enumerate(st.session_state.agent_memory[:-1]):  # Skip the last user message
                            # Add each previous message with its tool calls if they exist
                            tool_calls = msg.get("tool_calls", [])
                            
                            # To be super clear about which messages are from history
                            prefixed_content = msg["content"]
                            if i == 0:  # Only add prefix to the first message
                                prefixed_content = "[Previous conversation] " + prefixed_content
                                
                            # Use the agent's built-in method to add a message to its memory
                        
                        # Process the current message
                        response = ""
                        tool_calls = []
                        
                        # Stream the response
                        logger.debug(f"Running agent with prompt: {prompt}")
                        run_response = await agent.arun(prompt, stream=True)
                        async for resp_chunk in run_response:
                            # Handle tool calls
                            if resp_chunk.tools and len(resp_chunk.tools) > 0:
                                tool_calls = resp_chunk.tools
                                display_tool_calls(tool_calls_container, tool_calls)
                                
                            # Update response text
                            if resp_chunk.content is not None:
                                response += resp_chunk.content
                                response_container.markdown(response)
                        
                        # Store the agent's final response with tool calls
                        assistant_response = {
                            "role": "assistant",
                            "content": response,
                            "tool_calls": tool_calls
                        }
                        
                        # Add to agent memory
                        st.session_state.agent_memory.append(assistant_response)
                        
                        # Add to visible messages
                        st.session_state.messages.append(assistant_response)
                        
                        # Save the session ID for future continuity
                        st.session_state["session_id"] = agent.session_id
                        logger.debug(f"Saved session ID: {agent.session_id}")
                        
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    response_container.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })
                    st.session_state.agent_memory.append({
                        "role": "assistant", 
                        "content": error_msg
                    })
                    logger.error(f"Error during agent execution: {str(e)}", exc_info=True)

async def main():
    await initialize_agent_session_state(agent_name)
    await header()
    await body()


if __name__ == "__main__":
    if check_password():
        asyncio.run(main())
