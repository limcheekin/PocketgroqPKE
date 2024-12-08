from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pocketgroq_pke",
    version="0.1.0",
    author="jgravelle",
    description="An extension for PocketGroq that extracts structured procedural knowledge from text and PDFs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jgravelle/PocketgroqPKE",
    packages=find_packages(),
    package_data={
        'pocketgroq_pke': ['templates/*.txt'],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pocketgroq>=0.5.5",
        "rdflib>=6.0.0",
        "python-dotenv>=0.19.1",
        "groq>=0.8.0",
        "markdown2>=2.5.0",
        "PyPDF2>=3.0.0",
        "graphviz>=0.20.1"
    ],
    extras_require={
        'dev': [
            'pytest>=7.3.1',
            'pytest-asyncio>=0.21.0'
        ]
    }
)
