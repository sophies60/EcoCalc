import streamlit as st
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from agent import graphiti_agent, GraphitiDependencies
from graphiti_core import Graphiti
import re

# Load environment variables
load_dotenv()

# Initialize Neo4j connection
neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
neo4j_password = os.getenv('NEO4J_PASSWORD')

# Page configuration
st.set_page_config(
    page_title="Energy Cost Calculator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .appliance-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
    }
    .appliance-card.selected {
        background-color: #e8f0fe;
        border-color: #4299e1;
    }
    .time-input {
        width: 100%;
        margin-top: 0.5rem;
    }
    .result-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff;
        margin-top: 1rem;
        font-family: monospace;
        white-space: pre-wrap;
        line-height: 1.2;
        font-size: 0.9rem;
    }
    
    .result-section {
        margin: 0.5rem 0;
        padding: 0.5rem;
    }
    
    .analogy-item {
        margin: 0.75rem 0;
        padding: 0.5rem;
        background-color: #f8fafc;
        border-radius: 0.25rem;
    }
    
    .analogy-number {
        color: #666;
        margin-right: 0.5rem;
        font-weight: bold;
    }
    
    .result-section {
        margin-bottom: 0.5rem;
    }
    
    .analogy-item {
        margin: 0.5rem 0;
        padding: 0.5rem;
        background-color: #f8fafc;
        border-radius: 0.25rem;
    }
    
    .analogy-number {
        color: #666;
        margin-right: 0.5rem;
    }
    .analogy-item {
        padding: 0.75rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .analogy-item:last-child {
        border-bottom: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "selected_appliance" not in st.session_state:
    st.session_state.selected_appliance = "Fridge"
if "usage_time" not in st.session_state:
    st.session_state.usage_time = 3
if "time_unit" not in st.session_state:
    st.session_state.time_unit = "hours"
if "results" not in st.session_state:
    st.session_state.results = None

# Initialize Graphiti client
graphiti_client = Graphiti(neo4j_uri, neo4j_user, neo4j_password)

# Main content area
st.title("⚡ Energy Cost Calculator")

# Create the form with widgets
with st.form("energy_form"):
    # Appliance selection
    appliance = st.selectbox(
        "Select an Appliance",
        [
            "Fridge",
            "Heater",
            "TV",
            "Air Conditioner",
            "Laptop",
            "Microwave"
        ],
        key="appliance_selector",
        index=0
    )

    # Time input
    time = st.number_input(
        "Daily Usage Time",
        min_value=0,
        value=st.session_state.usage_time,
        step=1,
        key="usage_time"
    )

    # Time unit selection
    unit = st.selectbox(
        "Time Unit",
        ["hours/day", "minutes/day"],
        key="time_unit",
        index=0
    )

    # Submit button
    submitted = st.form_submit_button("Calculate")

    if submitted:
        # Prepare the query using form values
        query = f"""
        I use my {appliance.lower()} for {time} {unit}. 
        What is the energy consumption and cost? Please provide all 5 physical analogies.
        """
        
        # Initialize dependencies
        deps = GraphitiDependencies(graphiti_client=graphiti_client)
        
        # Run the agent
        async def run_agent():
            # Get the response directly
            response = await graphiti_agent.run(
                query,
                deps=deps
            )
            return response
        
        # Run the agent and store results
        st.session_state.results = asyncio.run(run_agent())
        st.rerun()

# Display results if available
if st.session_state.results:
    try:
        # Get the actual text content from the AgentRunResult
        content = st.session_state.results.output if hasattr(st.session_state.results, 'output') else str(st.session_state.results)
        
        # Remove all newlines and extra whitespace
        # First replace multiple newlines with a single space
        content = re.sub(r'\n+', ' ', content)
        # Then remove extra spaces
        content = re.sub(r'\s+', ' ', content)
        
        # Display the content in a card layout with monospace font
        st.markdown("""
        <div class='result-card'>
            <h3>Results</h3>
            <div class='result-content' style='font-family: monospace;'>
                {}
            </div>
        </div>
        """.format(content), unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying results: {str(e)}")

# Footer with energy saving tips
st.markdown("""
<style>
    .footer {
        margin-top: 2rem;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='footer'>", unsafe_allow_html=True)

    
st.markdown("</div>", unsafe_allow_html=True)

# Footer with energy saving tips
st.markdown("""
<style>
    .footer {
        margin-top: 2rem;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='footer'>", unsafe_allow_html=True)
st.markdown("<h4>Energy Saving Tips</h4>", unsafe_allow_html=True)
st.markdown("""
- Turn off appliances when not in use
- Use energy-efficient appliances
- Set thermostats to optimal temperatures
- Use power strips to easily turn off multiple devices
- Regularly maintain your appliances
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
