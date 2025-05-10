#!/usr/bin/env python3
"""
Context Management Demo - Demonstrates the advanced context management system.

This example shows how to leverage the context management system for handling:
1. Token optimization with large source documents
2. Smart chunking and context window management
3. Context compression and prioritization
4. Handling long conversations with history

Usage:
    python context_management_demo.py

Requirements:
    - Set OPENAI_API_KEY in environment variables or .env file
    - Install required packages from requirements.txt
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.research.adapters import SourceType, SourceResult
from src.research.synthesizer import GPT4Synthesizer, SynthesisType
from src.research.synthesizer.context_management import ContextManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("context_management_demo")


# Sample long research data (deliberately verbose to demonstrate chunking)
SAMPLE_SOURCE_RESULTS = [
    SourceResult(
        title="Climate Change: Comprehensive Analysis",
        content="""Climate change is a significant and complex global phenomenon characterized by long-term shifts in temperatures and weather patterns. These changes can be natural, but since the 1800s, human activities have been the main driver of climate change, primarily due to the burning of fossil fuels like coal, oil, and gas, which produces heat-trapping gases.

Global warming is the long-term heating of Earth's climate system observed since the pre-industrial period due to human activities, primarily fossil fuel burning, which increases heat-trapping greenhouse gas levels in Earth's atmosphere. The term is frequently used interchangeably with climate change, though the latter refers to both human- and naturally-produced warming and the effects it has on our planet.

Evidence for rapid climate change includes:
1. Rising Global Temperatures: The Earth's average surface temperature has risen about 1.1°C since the late 19th century, driven largely by increased carbon dioxide and other human-made emissions. Most of the warming occurred in the past 40 years, with the seven most recent years being the warmest.
2. Warming Oceans: The oceans have absorbed much of this increased heat, with the top 100 meters of ocean showing warming of more than 0.33°C since 1969.
3. Shrinking Ice Sheets: The Greenland and Antarctic ice sheets have decreased in mass. Data from NASA's Gravity Recovery and Climate Experiment show Greenland lost an average of 286 billion tons of ice per year between 1993 and 2016.
4. Glacial Retreat: Glaciers are retreating almost everywhere around the world — including in the Alps, Himalayas, Andes, Rockies, Alaska and Africa.
5. Decreased Snow Cover: Satellite observations reveal that the amount of spring snow cover in the Northern Hemisphere has decreased over the past five decades and the snow is melting earlier.
6. Sea Level Rise: Global sea level rose about 8 inches in the last century. The rate in the last two decades, however, is nearly double that of the last century.
7. Declining Arctic Sea Ice: Both the extent and thickness of Arctic sea ice has declined rapidly over the last several decades.
8. Extreme Weather Events: The number of record high temperature events in the United States has been increasing, while the number of record low temperature events has been decreasing, since 1950.
9. Ocean Acidification: Since the beginning of the Industrial Revolution, the acidity of surface ocean waters has increased by about 30%. This increase is the result of humans emitting more carbon dioxide into the atmosphere and hence more being absorbed into the oceans.

The Intergovernmental Panel on Climate Change (IPCC), which includes more than 1,300 scientists from the United States and other countries, forecasts a temperature rise of 2.5 to 10 degrees Fahrenheit over the next century. According to the IPCC, the extent of climate change effects on individual regions will vary over time and with the ability of different societal and environmental systems to mitigate or adapt to change.

The IPCC predicts that increases in global mean temperature of less than 1.8 to 5.4 degrees Fahrenheit (1 to 3 degrees Celsius) above 1990 levels will produce beneficial impacts in some regions and harmful ones in others. Net annual costs will increase over time as global temperatures increase.

Some of the long-term effects of climate change include:
- Changing precipitation patterns
- More droughts and heat waves
- Stronger and more intense hurricanes
- Rising sea levels
- Arctic likely to become ice-free

The Paris Agreement, adopted in 2015, aims to strengthen the global response to the threat of climate change by keeping a global temperature rise this century well below 2 degrees Celsius above pre-industrial levels and to pursue efforts to limit the temperature increase even further to 1.5 degrees Celsius.

Mitigating climate change will require a substantial and sustained reduction in greenhouse gas emissions, which can be achieved through:
- Transitioning to renewable energy sources like solar and wind power
- Improving energy efficiency
- Reducing deforestation and promoting reforestation
- Developing more sustainable agricultural practices
- Implementing carbon pricing mechanisms
- Adopting more sustainable transportation systems
- Reducing consumption and waste

Adaptation efforts to prepare for and respond to the effects of climate change include:
- Building sea walls and elevating infrastructure to prepare for sea level rise
- Developing drought-resistant crops
- Creating more efficient irrigation systems
- Restoring ecosystems that provide natural protection from extreme weather
- Improving emergency response systems for extreme weather events
- Developing more resilient communities through urban planning

The scientific consensus is that climate change is real, primarily caused by human activities, and poses significant risks to human society and the natural environment. However, with concerted global action, the worst impacts of climate change can still be avoided or mitigated.""",
        source="Scientific Research Institute",
        source_type=SourceType.ACADEMIC,
        url="https://example.com/climate-analysis",
        metadata={"year": 2023, "peer_reviewed": True}
    ),
    SourceResult(
        title="Climate Change Impacts on Global Ecosystems",
        content="""Climate change is having profound effects on ecosystems worldwide, altering biodiversity patterns, species distributions, and ecological processes. These impacts vary across different biomes and ecosystems, with some more vulnerable than others.

Terrestrial Ecosystems:
Forests, which cover approximately 30% of Earth's land surface, play a crucial role in the global carbon cycle by sequestering carbon dioxide. Climate change affects forests through:
- Shifting geographic ranges of species
- Changes in phenology (timing of seasonal activities)
- Altered growth rates and biomass accumulation
- Increased frequency and intensity of disturbances like wildfires, droughts, and pest outbreaks

For example, in boreal forests, warming temperatures are leading to northward expansion of tree species, while in tropical forests, increased drought stress is causing higher tree mortality and reduced carbon sequestration. The Amazon rainforest, which contains about 10% of the world's biodiversity, is particularly vulnerable to climate change and deforestation pressures, with some models suggesting potential "tipping points" where large portions could transition to savanna.

Grasslands and savannas, covering approximately 40% of Earth's land surface, are experiencing shifts in plant species composition due to changes in precipitation patterns and rising CO2 levels. These shifts can affect grazing animals and the human communities that depend on them.

Mountain ecosystems are seeing upslope migration of species as temperatures warm, with alpine species particularly at risk as they have nowhere higher to migrate. Some mountain plant species could face extinction as their habitat disappears.

Arctic tundra is warming more rapidly than most other regions on Earth. This warming is leading to:
- Thawing permafrost, which releases stored carbon
- Expansion of shrubs into previously shrub-free areas
- Changes in animal migration patterns and breeding times
- Altered nutrient cycling

Marine Ecosystems:
Oceans, which cover more than 70% of Earth's surface, are experiencing:
- Warming waters, with marine heatwaves becoming more frequent
- Ocean acidification due to absorption of CO2
- Deoxygenation in some regions
- Rising sea levels affecting coastal habitats

Coral reefs, often called "rainforests of the sea" due to their biodiversity, are particularly vulnerable to climate change. Warming ocean temperatures lead to coral bleaching events, where corals expel their symbiotic algae and often die as a result. Major bleaching events have affected reefs worldwide, including the Great Barrier Reef, where more than 50% of corals have died in some regions since 2016.

Ocean acidification is affecting organisms that build calcium carbonate shells or skeletons, such as corals, mollusks, and some plankton species. This has implications for marine food webs and ecosystem function.

Sea level rise is threatening coastal ecosystems such as mangroves, salt marshes, and seagrass beds, which provide important habitat, protect coastlines from storms, and sequester "blue carbon."

Freshwater Ecosystems:
Lakes, rivers, and wetlands are experiencing:
- Warming waters, leading to changes in thermal stratification in lakes
- Altered flow regimes and increased flooding or drought
- Changes in ice cover duration in cold regions
- Shifts in species composition and invasive species spread

Freshwater biodiversity is declining at faster rates than terrestrial or marine biodiversity, with climate change compounding other stressors such as pollution, habitat degradation, and water extraction.

Biodiversity Impacts:
Climate change is affecting biodiversity through multiple mechanisms:
- Range shifts: Many species are moving to higher elevations or latitudes as temperatures warm
- Phenological changes: The timing of seasonal events (flowering, migration, breeding) is shifting, potentially creating mismatches between species
- Direct physiological stress: Some species face direct threats from temperature extremes, drought, or other climate-related factors
- Disruption of ecological relationships: Changes in one species can affect others through predator-prey relationships, competition, or mutualism

Some species can adapt to climate change through genetic changes, behavioral flexibility, or migration, but many cannot adapt quickly enough to keep pace with rapid climate change. Extinction risks are increased, particularly for species that:
- Have narrow climate tolerances
- Have poor dispersal abilities
- Are already threatened by other factors
- Have important ecological interactions with species that are negatively affected

Ecosystem Services Impacts:
Climate change affects the ecosystem services that humans depend on:
- Provisioning services: Food production, timber, fresh water
- Regulating services: Carbon sequestration, flood control, water purification
- Supporting services: Nutrient cycling, soil formation
- Cultural services: Recreation, aesthetic enjoyment, cultural identity

For example, climate-driven changes in pollinator distributions and activity periods can affect crop pollination and food security. Changes in forest composition can affect timber production and non-timber forest products.

Feedback Loops:
Many ecosystem impacts of climate change can create feedback loops that either amplify or dampen climate change:
- Positive feedbacks (amplifying): For example, thawing permafrost releases methane and CO2, further warming the climate
- Negative feedbacks (dampening): For example, increased plant growth in some regions may increase carbon sequestration

Understanding these complex ecosystem responses to climate change is crucial for developing effective mitigation and adaptation strategies.""",
        source="Environmental Research Journal",
        source_type=SourceType.ACADEMIC,
        url="https://example.org/ecosystem-impacts",
        metadata={"year": 2024, "peer_reviewed": True}
    ),
    SourceResult(
        title="Economic Implications of Climate Change",
        content="""Climate change presents one of the most significant economic challenges of the 21st century, with far-reaching implications for global markets, industries, financial systems, and human welfare. This document examines the complex economic dimensions of climate change, including costs, opportunities, policy approaches, and transition strategies.

Economic Costs of Climate Change:
The economic impacts of climate change are diverse and unevenly distributed across regions, sectors, and populations. According to the Stern Review (2006), without action, the overall costs of climate change could be equivalent to losing 5% of global GDP each year. More recent estimates from the Network for Greening the Financial System suggest that unmitigated climate change could reduce global GDP by up to 25% by 2100.

Direct physical costs include:
- Damage to infrastructure and property from extreme weather events
- Agricultural losses from changing weather patterns and water availability
- Healthcare costs related to heat stress, vector-borne diseases, and air pollution
- Reduced labor productivity due to heat stress
- Costs of adapting infrastructure to sea level rise and extreme weather

Indirect economic impacts include:
- Supply chain disruptions
- Displacement of populations and associated costs
- Financial market instability and stranded assets
- National security implications and conflict
- Biodiversity loss affecting ecosystem services

These costs are not evenly distributed. Developing countries, particularly those in tropical regions, are expected to face disproportionate impacts despite having contributed less to historical emissions. Within countries, vulnerable populations often face greater exposure to climate risks and have fewer resources to adapt.

Climate Finance and Investment:
Addressing climate change requires significant financial resources. The International Energy Agency estimates that reaching net-zero emissions by 2050 will require annual clean energy investment to more than triple by 2030 to around $4 trillion.

Key areas for climate finance include:
- Renewable energy infrastructure
- Energy efficiency improvements
- Clean transportation systems
- Climate-resilient agriculture
- Carbon removal technologies
- Climate adaptation infrastructure

Sources of climate finance include:
- Public finance (government budgets, development banks)
- Private investment (corporations, financial institutions, venture capital)
- Green bonds and climate-aligned bonds
- Climate funds (e.g., Green Climate Fund)
- Carbon markets

The financial sector is increasingly recognizing climate risks and opportunities. Many institutional investors are incorporating climate considerations into investment decisions, driven by both financial materiality and growing client demand for sustainable investments.

Economic Policy Approaches:
Economic policies to address climate change broadly fall into two categories: carbon pricing and non-pricing policies.

Carbon pricing mechanisms include:
- Carbon taxes, which set a direct price on carbon emissions
- Cap-and-trade systems, which set an emissions limit and allow trading of permits
- Carbon border adjustments, which apply carbon prices to imports

These approaches aim to internalize the external costs of greenhouse gas emissions and incentivize low-carbon alternatives. As of 2023, over 65 carbon pricing initiatives have been implemented worldwide, covering about 23% of global emissions.

Non-pricing policies include:
- Regulations and standards (e.g., energy efficiency standards, renewable portfolio standards)
- Subsidies and incentives for clean energy and technology
- Public investment in R&D and infrastructure
- Information and voluntary programs

Most economists agree that a mix of policy approaches is necessary, with carbon pricing as a cornerstone supplemented by targeted regulations and investments to address specific market failures.

Structural Economic Transformation:
Addressing climate change requires fundamental transformations in energy systems, industrial processes, transportation, buildings, and land use. This transition creates both challenges and opportunities.

Key economic transitions include:
- Decarbonizing electricity generation through renewable energy expansion
- Electrifying transportation, heating, and industrial processes
- Improving energy and resource efficiency
- Shifting to circular economy models
- Transforming agricultural and food systems
- Developing carbon removal approaches

These transitions will create new industries and jobs while disrupting existing ones. Studies suggest that the net employment effect of climate policies is likely positive, though significant workforce transitions will be required.

Just Transition Considerations:
The concept of a "just transition" recognizes the importance of ensuring that the shift to a low-carbon economy is equitable and leaves no one behind.

Economic considerations for a just transition include:
- Worker retraining and support for affected communities
- Addressing energy poverty and ensuring affordable access to clean energy
- International support for developing countries' transition efforts
- Ensuring equitable distribution of transition costs and benefits

Economic Integration with Adaptation:
In addition to mitigation efforts, substantial investment in climate adaptation is necessary. The Global Commission on Adaptation estimates that investing $1.8 trillion globally from 2020 to 2030 in adaptation measures could generate $7.1 trillion in total benefits.

Economic aspects of adaptation include:
- Infrastructure resilience investments
- Climate-smart agriculture development
- Water management systems
- Early warning systems for extreme weather
- Health system preparedness

Innovation and Growth Opportunities:
The climate transition presents significant opportunities for innovation and economic growth:
- Clean energy technologies
- Low-carbon materials and manufacturing
- Climate-smart agriculture and food systems
- Circular economy business models
- Nature-based solutions
- Digital technologies for climate applications

Countries and companies that lead in these areas may gain competitive advantages in the emerging low-carbon economy.

Conclusion:
The economic dimensions of climate change are complex and far-reaching. While the transition to a low-carbon economy presents substantial costs and disruptions, it also offers opportunities for innovation, job creation, and more sustainable economic development. Effective economic policies can help manage this transition while reducing emissions and building resilience. Delay in action typically increases both the physical costs of climate impacts and the eventual costs of transition.""",
        source="Global Economic Policy Institute",
        source_type=SourceType.WEBSITE,
        url="https://example.net/climate-economics",
        metadata={"year": 2023}
    ),
]


async def demonstrate_context_management():
    """Demonstrate the context management system functionality."""
    logger.info("Starting context management system demo...")
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OPENAI_API_KEY found in environment variables or .env file.")
        logger.error("Please set the API key and try again.")
        return
    
    # Part 1: Demonstrate standalone context manager
    logger.info("\n=== Part 1: Standalone Context Manager ===")
    await demo_standalone_context_manager()
    
    # Part 2: Demonstrate integrated context management with GPT4Synthesizer
    logger.info("\n=== Part 2: Integrated Context Management ===")
    await demo_integrated_context_management(api_key)
    
    logger.info("\nContext management demo completed!")


async def demo_standalone_context_manager():
    """Demonstrate the standalone context manager functionality."""
    # Initialize context manager with different compression levels
    for compression_level in [0, 2]:
        logger.info(f"\nTesting context manager with compression level {compression_level}")
        
        # Create context manager
        context_mgr = ContextManager(
            model="gpt-4o",
            response_tokens=1000,
            compression_level=compression_level
        )
        
        # Display initial token availability
        logger.info(f"Initial available tokens: {context_mgr.available_tokens}")
        
        # Add system prompt
        system_prompt = "You are a helpful research assistant that analyzes climate change information."
        added = context_mgr.add_system_prompt(system_prompt)
        logger.info(f"Added system prompt: {added}")
        logger.info(f"Available tokens after system prompt: {context_mgr.available_tokens}")
        
        # Add sources and track how many were added
        sources_added = context_mgr.add_sources(
            sources=SAMPLE_SOURCE_RESULTS,
            max_tokens=80000  # Generous limit to see how many can fit
        )
        logger.info(f"Sources added: {sources_added} out of {len(SAMPLE_SOURCE_RESULTS)}")
        logger.info(f"Available tokens after adding sources: {context_mgr.available_tokens}")
        
        # Count and display windows
        window_count = len(context_mgr.context_windows)
        total_tokens = sum(w.token_count for w in context_mgr.context_windows)
        logger.info(f"Total context windows: {window_count}")
        logger.info(f"Total tokens in context: {total_tokens}")
        
        # Add user query
        user_query = "What are the key economic impacts of climate change and how do they relate to ecosystem changes?"
        added = context_mgr.add_user_input(user_query, priority=90)
        logger.info(f"Added user query: {added}")
        logger.info(f"Available tokens after user query: {context_mgr.available_tokens}")
        
        # Build messages for API
        messages = context_mgr.build_messages()
        logger.info(f"Built {len(messages)} messages for API request")
        
        # Demonstrate compression
        if compression_level > 0:
            logger.info("\nDemonstrating context compression...")
            tokens_before = sum(w.token_count for w in context_mgr.context_windows)
            tokens_freed = context_mgr.compress_context()
            tokens_after = sum(w.token_count for w in context_mgr.context_windows)
            
            logger.info(f"Compression freed {tokens_freed} tokens")
            logger.info(f"Tokens before: {tokens_before}, after: {tokens_after}")
            logger.info(f"Windows before compression: {window_count}, after: {len(context_mgr.context_windows)}")
        
        # Clear context
        context_mgr.clear_context(preserve_system=True)
        logger.info(f"After clearing context (preserving system prompt):")
        logger.info(f"Context windows remaining: {len(context_mgr.context_windows)}")
        logger.info(f"Available tokens: {context_mgr.available_tokens}")
        logger.info(f"Context history entries: {len(context_mgr.context_history)}")


async def demo_integrated_context_management(api_key):
    """Demonstrate context management integrated with GPT4Synthesizer."""
    # Create synthesizers with different compression levels
    for compression_level in [1, 3]:
        logger.info(f"\nTesting GPT4Synthesizer with compression level {compression_level}")
        
        # Initialize the synthesizer with context management
        synthesizer = GPT4Synthesizer(
            api_key=api_key,
            model="gpt-4o",
            temperature=0.3,
            max_tokens=1000,
            context_compression_level=compression_level
        )
        
        logger.info(f"Model: {synthesizer.model}, Max tokens: {synthesizer.max_tokens}")
        logger.info(f"Initial token limit: {synthesizer.context_manager.token_limit}")
        
        # Track timing
        start_time = datetime.now()
        
        # Run synthesis with large source dataset
        query = "What are the economic impacts of climate change, particularly in relation to ecosystem changes?"
        
        try:
            # Use the SynthesisType that would stress the context system the most
            result = await synthesizer.synthesize(
                query=query,
                source_results=SAMPLE_SOURCE_RESULTS,
                synthesis_type=SynthesisType.COMPREHENSIVE
            )
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            if result:
                logger.info(f"Synthesis completed successfully in {elapsed_time:.2f} seconds!")
                logger.info(f"Title: {result.title}")
                logger.info(f"Sources used: {result.sources_used}")
                logger.info(f"Number of sections: {len(result.sections)}")
                
                # Save the result
                output_file = f"context_management_result_c{compression_level}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, "w") as f:
                    json.dump(result.to_dict(), f, indent=2)
                
                logger.info(f"Result saved to {output_file}")
                
                # Display a brief preview
                content_preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
                logger.info(f"Preview: {content_preview}")
            else:
                logger.error("Synthesis failed to produce a result")
        
        except Exception as e:
            logger.error(f"Error during synthesis: {e}")


if __name__ == "__main__":
    asyncio.run(demonstrate_context_management()) 