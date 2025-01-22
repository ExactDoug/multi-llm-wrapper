from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="brave-search-aggregator",
    version="0.1.0",
    author="Exact Technology Partners",
    author_email="dmortensen@exactpartners.com",
    description="A sophisticated web search knowledge aggregator using Brave Search",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/exactdoug/multi-llm-wrapper",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "aiohttp>=3.8.0",
        "python-dotenv>=0.19.0",
        "pydantic>=2.0.0",
        "beautifulsoup4>=4.9.0",
        "tenacity>=8.0.0",
        "opencensus-ext-azure>=1.1.0",
        "azure-identity>=1.12.0",
        "azure-keyvault-secrets>=4.7.0",
        "azure-storage-blob>=12.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "pylint>=2.17.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "brave-search-aggregator=brave_search_aggregator.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/exactdoug/multi-llm-wrapper/issues",
        "Source": "https://github.com/exactdoug/multi-llm-wrapper",
    },
)
