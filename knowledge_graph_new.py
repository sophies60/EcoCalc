import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from logging import INFO

from dotenv import load_dotenv

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF

#################################################
# CONFIGURATION
#################################################
# Set up logging and environment variables for
# connecting to Neo4j database
#################################################

# Configure logging
logging.basicConfig(
    level=INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

load_dotenv()

# Neo4j connection parameters
# Make sure Neo4j Desktop is running with a local DBMS started
neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

if not neo4j_uri or not neo4j_user or not neo4j_password:
    raise ValueError('NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set')


async def main():
    #################################################
    # INITIALIZATION
    #################################################
    # Connect to Neo4j and set up Graphiti indices
    # This is required before using other Graphiti
    # functionality
    #################################################

    # Initialize Graphiti with Neo4j connection
    graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
    

    try:
        # Initialize the graph database with graphiti's indices. This only needs to be done once.
        print("\nInitializing graph database...")
        await graphiti.build_indices_and_constraints()
        print("Graph database initialized successfully!")

        #################################################
        # ADDING EPISODES
        #################################################
        # Episodes are the primary units of information
        # in Graphiti. They can be text or structured JSON
        # and are automatically processed to extract entities
        # and relationships.
        #################################################

        # Example: Add Episodes
        # Episodes list containing both text and JSON episodes
        episodes = [
            # Appliance power ratings
            {
                'content': 'Fridge: 150W',
                'type': EpisodeType.text,
                'description': 'Fridge power consumption',
            },
            {
                'content': 'Heater: 1500W',
                'type': EpisodeType.text,
                'description': 'Heater power consumption',
            },
            {
                'content': 'TV: 100W',
                'type': EpisodeType.text,
                'description': 'TV power consumption',
            },
            {
                'content': 'Air Conditioner: 2000W',
                'type': EpisodeType.text,
                'description': 'Air conditioner power consumption',
            },
            {
                'content': 'Laptop: 60W',
                'type': EpisodeType.text,
                'description': 'Laptop power consumption',
            },
            {
                'content': 'Microwave: 1200W',
                'type': EpisodeType.text,
                'description': 'Microwave power consumption',
            },

            # Unit conversions
            {
                'content': '1W = 0.001kW',
                'type': EpisodeType.text,
                'description': 'Watt to kilowatt conversion',
            },
            {
                'content': '1W = 1J/s',
                'type': EpisodeType.text,
                'description': 'Watt to joule per second conversion',
            },
            {
                'content': '1kWh = 3600000J',
                'type': EpisodeType.text,
                'description': 'Kilowatt-hour to joule conversion',
            },
            {
                'content': '1kWh = 1000Wh',
                'type': EpisodeType.text,
                'description': 'Kilowatt-hour to watt-hour conversion',
            },

            # Time units
            {
                'content': '1h = 60min',
                'type': EpisodeType.text,
                'description': 'Hour to minute conversion',
            },
            {
                'content': '1min = 60s',
                'type': EpisodeType.text,
                'description': 'Minute to second conversion',
            },
            # Cost information
            {
                'content': '1kWh costs $0.23 in NYC',
                'type': EpisodeType.text,
                'description': 'NYC electricity cost',
            },
            {
                'content': '1kWh costs $0.28 in Boston',
                'type': EpisodeType.text,
                'description': 'Boston electricity cost',
            },
            {
                'content': '1kWh costs $0.15 in Chicago',
                'type': EpisodeType.text,
                'description': 'Chicago electricity cost',
            },
            {
                'content': '1kWh costs $0.29 in Los Angeles',
                'type': EpisodeType.text,
                'description': 'Los Angeles electricity cost',
            },
            {
                'content': '1kWh costs $0.30 in San Francisco',
                'type': EpisodeType.text,
                'description': 'San Francisco electricity cost',
            },
            {
                'content': '1kWh costs $0.15 in Houston',
                'type': EpisodeType.text,
                'description': 'Houston electricity cost',
            },
            {
                'content': '1kWh costs $0.17 in Washington DC',
                'type': EpisodeType.text,
                'description': 'Washington DC electricity cost',
            },
            # Energy analogies
            {
                'content': '1kWh = Lifting 100kg 367m',
                'type': EpisodeType.text,
                'description': '1kWh physical analogy - lifting',
            },
            {
                'content': '1kWh = Running 10km',
                'type': EpisodeType.text,
                'description': '1kWh physical analogy - running',
            },
            {
                'content': '1kWh = Cycling 200W for 5h',
                'type': EpisodeType.text,
                'description': '1kWh physical analogy - cycling',
            },
            {
                'content': '1kWh = Climbing 200 flights',
                'type': EpisodeType.text,
                'description': '1kWh physical analogy - climbing',
            },
            {
                'content': '1kWh = 3000 jumping jacks',
                'type': EpisodeType.text,
                'description': '1kWh physical analogy - jumping jacks',
            }
        ]

        # Add episodes to the graph with error handling
        added_episodes = []
        for i, episode in enumerate(episodes):
            try:
                episode_name = f'Energy Calculator Episode {i}'
                episode_type = EpisodeType.text  # Ensure we're using the correct enum value
                
                # Add episode with proper type handling
                await graphiti.add_episode(
                    name=episode_name,
                    episode_body=episode['content']
                    if isinstance(episode['content'], str)
                    else json.dumps(episode['content']),
                    source=episode_type,
                    source_description=episode['description'],
                    reference_time=datetime.now(timezone.utc),
                )
                added_episodes.append(episode_name)
                print(f'Added episode: {episode_name} ({episode_type.value})')
            except Exception as add_error:
                logger.error(f'Error adding episode {i}: {str(add_error)}')
                print(f'Error adding episode {i}: {str(add_error)}')
                continue

        # Verify episodes were added
        if added_episodes:
            print('\nVerifying episodes in graph...')
            try:
                # Verify at least one episode exists
                verify_query = """
                MATCH (n:Episode)
                RETURN count(n)
                """
                result = await graphiti.driver.execute_query(verify_query)
                episode_count = result[0][0]
                print(f'Number of episodes in graph: {episode_count}')
            except Exception as verify_error:
                logger.error(f'Error verifying episodes: {str(verify_error)}')
                print(f'Error verifying episodes: {str(verify_error)}')

        #################################################
        # BASIC SEARCH
        #################################################
        # The simplest way to retrieve relationships (edges)
        # from Graphiti is using the search method, which
        # performs a hybrid search combining semantic
        # similarity and BM25 text retrieval.
        #################################################

        # Verify episodes were added before search
        if not added_episodes:
            print('No episodes were successfully added. Skipping search.')
            return

        # Perform a hybrid search combining semantic similarity and BM25 retrieval
        print("\nSearching for: 'Which appliance uses the most energy?'")
        try:
            results = await graphiti.search('Which appliance uses the most energy?')
            if not results:
                print("No results found in the search")
        except Exception as search_error:
            logger.error(f"Error during search: {str(search_error)}")
            print(f"Error during search: {str(search_error)}")
            results = []

        # Print search results
        print('\nSearch Results:')
        for result in results:
            print(f'UUID: {result.uuid}')
            print(f'Fact: {result.fact}')
            if hasattr(result, 'valid_at') and result.valid_at:
                print(f'Valid from: {result.valid_at}')
            if hasattr(result, 'invalid_at') and result.invalid_at:
                print(f'Valid until: {result.invalid_at}')
            print('---')

        #################################################
        # NODE SEARCH USING SEARCH RECIPES
        #################################################
        # Graphiti provides predefined search recipes
        # optimized for different search scenarios.
        # Here we use NODE_HYBRID_SEARCH_RRF for retrieving
        # nodes directly instead of edges.
        #################################################

        # Example: Perform a node search using _search method with standard recipes
        print(
            '\nPerforming node search using _search method with standard recipe NODE_HYBRID_SEARCH_RRF:'
        )

        # Use a predefined search configuration recipe and modify its limit
        node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        node_search_config.limit = 5  # Limit to 5 results

        # Execute the node search
        node_search_results = await graphiti._search(
            query='Energy consumption tips',
            config=node_search_config,
        )

        # Print node search results
        print('\nNode Search Results:')
        if node_search_results:
            for i, result in enumerate(node_search_results):
                print(f'Node {i+1}:')
                print(f'  UUID: {result[0]}')  # First element is the UUID
                if isinstance(result[1], dict):  # Second element should be a node dictionary
                    node = result[1]
                    print(f'  Name: {node.get("name", "N/A")}')
                    print(f'  Content: {node.get("content", "N/A")}')
                    print(f'  Labels: {node.get("labels", [])}')
                    print(f'  Created At: {node.get("created_at", "N/A")}')
                    print('  Attributes:')
                    for key, value in node.items():
                        if key not in ['uuid', 'name', 'content', 'labels', 'created_at']:
                            print(f'    {key}: {value}')
                else:
                    print('  No node information available')
                print('---')
        else:
            print('No results found')

        #################################################
        # Perform a hybrid search combining semantic similarity and BM25 retrieval
        print("\nSearching for: 'Which appliance uses the most energy?'")
        try:
            results = await graphiti.search('Which appliance uses the most energy?')
            if not results:
                print("No results found in the search")
        except Exception as search_error:
            logger.error(f"Error during search: {str(search_error)}")
            print(f"Error during search: {str(search_error)}")
            results = []

        # Print search results
        print('\nSearch Results:')
        for result in results:
            print(f'UUID: {result.uuid}')
            print(f'Fact: {result.fact}')
            if hasattr(result, 'valid_at') and result.valid_at:
                print(f'Valid from: {result.valid_at}')
            if hasattr(result, 'invalid_at') and result.invalid_at:
                print(f'Valid until: {result.invalid_at}')
            print('---')



        #################################################
        # CLEANUP
        #################################################
        # Always close the connection to Neo4j when
        # finished to properly release resources
        #################################################

        try:
            print("\nCleaning up resources...")
            await graphiti.close()
            print("Connection closed successfully!")
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {str(cleanup_error)}")
            print(f"Error during cleanup: {str(cleanup_error)}")

    except Exception as e:
        logger.error(f"Error during graph initialization: {str(e)}")
        raise


if __name__ == '__main__':
    asyncio.run(main())
