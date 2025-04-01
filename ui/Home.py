import asyncio

import nest_asyncio
import streamlit as st
from agno.tools.streamlit.components import check_password

from ui.css import CUSTOM_CSS
from ui.utils import about_agno, footer

nest_asyncio.apply()

st.set_page_config(
    page_title="My Agents",
    page_icon=":orange_heart:",
    layout="wide",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


async def header():
    st.markdown("<h1 class='heading'>My Agents</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subheading'>Welcome to the Agno Agents platform! We've provided some sample agents to get you started.</p>",
        unsafe_allow_html=True,
    )


async def body():
    st.markdown("### Available Agents")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
        <div style="padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;">
            <h3>Sage</h3>
            <p>A knowledge agent that uses Agentic RAG to deliver context-rich answers from a knowledge base.</p>
            <p>Perfect for exploring your own knowledge base.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Launch Sage", key="sage_button"):
            st.switch_page("pages/1_Sage.py")

    with col2:
        st.markdown(
            """
        <div style="padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;">
            <h3>Scholar</h3>
            <p>A research agent that uses DuckDuckGo (and optionally Exa) to deliver in-depth answers about any topic.</p>
            <p>Perfect for exploring general knowledge from the web.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Launch Scholar", key="scholar_button"):
            st.switch_page("pages/2_Scholar.py")
    with col3:
        st.markdown(
            """
        <div style="padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;">
            <h3>Db2i</h3>
            <p>A database agent for Db2 for i that uses Mapepire to securely connect to your database to help answer questions about the provided schema.</p>
            <p>Perfect for exploring your database.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Launch Db2i", key="db2i_button"):
            st.switch_page("pages/3_Db2i.py")


async def main():
    await header()
    await body()
    await footer()


if __name__ == "__main__":
    if check_password():
        asyncio.run(main())
