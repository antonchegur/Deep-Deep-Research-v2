# Deep Deep Research v2

A comprehensive research tool that integrates multiple data sources and uses GPT-4 Turbo to analyze and synthesize information.

## Overview

Deep Deep Research v2 is designed to enhance research capabilities by:

1. Collecting data from multiple sources (Wikipedia, web searches, academic papers)
2. Retrieving detailed content from the most relevant sources
3. Using GPT-4 Turbo to analyze and synthesize the information
4. Providing structured research results with proper citations

## Features

- **Multi-source Integration**: Combines data from Wikipedia, DuckDuckGo, arXiv, and OpenAI Search
- **Configurable Research Depth**: Choose from quick, standard, or deep research
- **Multiple Synthesis Types**: Options include summaries, comprehensive analysis, comparisons, fact-checking, critiques, and more
- **Multi-language Support**: Research in different languages
- **Asynchronous Processing**: Concurrent API requests for faster results
- **Robust Error Handling**: Graceful handling of API errors and rate limits
- **Customizable**: Easily extend with new data sources or synthesis methods

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key for GPT-4 synthesis
- Dependencies: httpx, beautifulsoup4, lxml, python-dotenv

### Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

### Usage

Run the example script:

```bash
python examples/research_pipeline_demo.py
```

You can also use the individual components:

```python
from src.research.adapters import SourceConfig
from src.research.manager import SourceManager
from src.research.synthesizer import GPT4Synthesizer, SynthesisType
from src.research.pipeline import ResearchPipeline

# Create the pipeline
pipeline = ResearchPipeline()

# Run research
result = await pipeline.research(
    query="What are the latest developments in quantum computing?",
    depth="standard",
    synthesis_type=SynthesisType.LATEST_RESEARCH,
    language="en"
)
```

## API Structure

- `adapters`: Source-specific adapters for data retrieval
- `manager`: Coordinates data collection across sources
- `synthesizer`: Analyzes and synthesizes research data
- `pipeline`: High-level API that combines all components

## Troubleshooting

### Source Adapters

- **Wikipedia**: Fully functional. Handles article searches and content retrieval.
- **arXiv**: Functional for searches and paper retrieval.
- **DuckDuckGo**: Current implementation may encounter HTTP redirect issues. Consider using a browser user-agent or following redirects.
- **OpenAI Search**: Requires proper configuration with the correct OpenAI API model that supports search. The current implementation needs updates for the latest API requirements.

When adapting this system for production use, you may need to implement proper user-agent headers, respect rate limits, and handle CAPTCHA challenges that some sources may present.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for the GPT-4 API
- Wikipedia, DuckDuckGo, and arXiv for their valuable data sources 