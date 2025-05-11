from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="deep-deep-research",
    version="0.1.0",
    author="Deep Deep Research Team",
    author_email="yourname@example.com",
    description="A comprehensive research tool with GPT-4 Turbo synthesis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/deep-deep-research-v2",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
        "beautifulsoup4>=4.10.0",
        "lxml>=4.9.0",
        "python-dotenv>=1.0.0",
        "openai>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ddr=src.cli:main",  # Command-line interface entry point
        ],
    },
) 