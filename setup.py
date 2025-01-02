from setuptools import setup, find_packages

setup(
    name="network_react_agent",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "langchain>=0.3.13",
        "langchain-community>=0.3.13",
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
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A ReAct agent for network operations",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)