from setuptools import setup, find_packages

setup(
    name="multi-llm-wrapper",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "litellm>=1.22.0",
        "pytest>=7.4.0",
        "pytest-asyncio>=0.23.0",
        "python-dotenv>=1.0.0",
        "typing-extensions>=4.8.0",
    ],
    python_requires=">=3.8",
)
