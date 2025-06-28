from __future__ import annotations
from typing import Dict, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from rich.markdown import Markdown
from rich.console import Console
from rich.live import Live
import asyncio
import os

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent, RunContext
from graphiti_core import Graphiti

load_dotenv()

# ========== Define dependencies ==========
@dataclass
class GraphitiDependencies:
    """Dependencies for the Graphiti agent."""
    graphiti_client: Graphiti

# ========== Helper function to get model configuration ==========
def get_model():
    """Configure and return the LLM model to use."""
    model_choice = os.getenv('MODEL_CHOICE', 'gpt-4.1-mini')
    api_key = os.getenv('OPENAI_API_KEY')

    return OpenAIModel(model_choice, provider=OpenAIProvider(api_key=api_key))

# ========== Create the Graphiti agent ==========
graphiti_agent = Agent(
    get_model(),
    system_prompt="""You are a helpful energy calculator assistant with access to a knowledge graph containing:
    - Appliance power ratings
    - Energy unit conversions
    - Cost information for NYC electricity
    
    When the user asks you questions about energy consumption or costs:
    1. Search the knowledge graph for relevant information; Search for the appliance and time provided
    2. Calculate costs based on NYC electricity rates ($0.23/kWh)
    3. Provide clear, factual answers with supporting information
    4. Present all the physical analogies to help users understand energy consumption (5 different analogies found in the knowledge graph)
    
    IMPORTANT: Provide your response in HTML format with proper paragraph tags. Use <p> for paragraphs and <br> for line breaks within paragraphs. For example:
    <p>Your fridge has a power usage of 150 watts (W).<br><br>Using it for 3 hours, the energy consumption can be calculated as:</p>
    <p>Energy (kWh) = Power (W) × Time (hours) / 1000<br>= 150 W × 3 hours / 1000<br>= 0.45 kWh</p>
    
    Use <strong> for important values and calculations.

    IMPORTANT: Please also use emojis for a more user-friendly and engaging experience. 

        Please use emojis to enhance the user experience:
    - Use 📊 for calculations and statistics
    - Use 💡 for energy-related concepts
    - Use 🏃‍♂️ for physical activity analogies
    - Use 💰 for cost information
    - Use ⚡ for electricity-related information
    - Use 📈 for comparisons and trends

    IMPORTANT!! Ensure that all analogies are scaled based on the user's calculated power output. 
    
    Place emojis strategically to enhance understanding and engagement, but don't overuse them.

    If you can't find the information needed to answer a question, be honest and say so.
    """,
    deps_type=GraphitiDependencies
)

# ========== Define a result model for Graphiti search ==========
class GraphitiSearchResult(BaseModel):
    """Model representing a search result from Graphiti."""
    uuid: str = Field(description="The unique identifier for this fact")
    fact: str = Field(description="The factual statement retrieved from the knowledge graph")
    valid_at: Optional[str] = Field(None, description="When this fact became valid (if known)")
    invalid_at: Optional[str] = Field(None, description="When this fact became invalid (if known)")
    source_node_uuid: Optional[str] = Field(None, description="UUID of the source node")

# ========== Graphiti search tool ==========
@graphiti_agent.tool
async def search_graphiti(ctx: RunContext[GraphitiDependencies], query: str) -> List[GraphitiSearchResult]:
    """Search the Graphiti knowledge graph with the given query.
    
    Args:
        ctx: The run context containing dependencies
        query: The search query to find information in the knowledge graph
        
    Returns:
        A list of search results containing facts that match the query
    """
    # Access the Graphiti client from dependencies
    graphiti = ctx.deps.graphiti_client
    
    try:
        # Perform the search
        results = await graphiti.search(query)
        
        # Format the results
        formatted_results = []
        for result in results:
            # Handle physical analogies specially
            if '1kWh' in result.fact:
                formatted_result = GraphitiSearchResult(
                    uuid=result.uuid,
                    fact=f"1 kWh is equivalent to {result.fact}",
                    source_node_uuid=result.source_node_uuid if hasattr(result, 'source_node_uuid') else None
                )
            else:
                formatted_result = GraphitiSearchResult(
                    uuid=result.uuid,
                    fact=result.fact,
                    source_node_uuid=result.source_node_uuid if hasattr(result, 'source_node_uuid') else None
                )
            
            # Add temporal information if available
            if hasattr(result, 'valid_at') and result.valid_at:
                formatted_result.valid_at = str(result.valid_at)
            if hasattr(result, 'invalid_at') and result.invalid_at:
                formatted_result.invalid_at = str(result.invalid_at)
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    except Exception as e:
        # Log the error but don't close the connection since it's managed by the dependency
        print(f"Error searching Graphiti: {str(e)}")
        raise

# ========== Main execution function ==========
async def main():
    """Run the Graphiti agent with user queries."""
    print("Graphiti Agent - Powered by Pydantic AI, Graphiti, and Neo4j")
    print("Enter 'exit' to quit the program.")

    # Neo4j connection parameters
    neo4j_uri = os.environ.get('NEO4J_URI', 'neo4j://127.0.0.1:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'unisunis')
    
    # Initialize Graphiti with Neo4j connection
    graphiti_client = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
    
    # Initialize the graph database with graphiti's indices if needed
    try:
        await graphiti_client.build_indices_and_constraints()
        print("Graphiti indices built successfully.")
    except Exception as e:
        print(f"Note: {str(e)}")
        print("Continuing with existing indices...")

    console = Console()
    messages = []
    
    try:
        while True:
            # Get user input
            user_input = input("\n[You] ")
            
            # Check if user wants to exit
            if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                print("Goodbye!")
                break
            
            try:
                # Process the user input and output the response
                print("\n[Assistant]")
                with Live('', console=console, vertical_overflow='visible') as live:
                    # Pass the Graphiti client as a dependency
                    deps = GraphitiDependencies(graphiti_client=graphiti_client)
                    
                    async with graphiti_agent.run_stream(
                        user_input, message_history=messages, deps=deps
                    ) as result:
                        curr_message = ""
                        async for message in result.stream_text(delta=True):
                            curr_message += message
                            live.update(Markdown(curr_message))
                    
                    # Add the new messages to the chat history
                    messages.extend(result.all_messages())
                
            except Exception as e:
                print(f"\n[Error] An error occurred: {str(e)}")
    finally:
        # Close the Graphiti connection when done
        await graphiti_client.close()
        print("\nGraphiti connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        raise
