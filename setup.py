from setuptools import setup, find_packages

setup(
    name="network_react_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "requests>=2.31.0",
        "pydantic>=2.5.2",
        "PyYAML>=6.0.1",
        "python-dotenv>=1.0.0",
        "openai>=1.3.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-mock>=3.12.0",
            "requests-mock>=1.11.0",
            "pytest-cov>=4.1.0",
            "pytest-watch>=4.2.0"
        ]
    }
)