 # PocketgroqPKE - Procedural Knowledge Extractor

An extension for PocketGroq that extracts structured procedural knowledge from text and generates RDF knowledge graphs.

## Overview

This extension adds procedural knowledge extraction capabilities to PocketGroq, allowing you to:

- Extract step-by-step procedures from unstructured text
- Identify actions, direct objects, equipment, and temporal information
- Generate RDF knowledge graphs using standard procedural ontologies
- Leverage async support for better performance

## Setup

1. Clone the repository:
```bash
git clone https://github.com/jgravelle/PocketgroqPKE.git
cd PocketgroqPKE
```

2. Set up your environment:
```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
python setup.py develop
```

3. Set your Groq API key:
```bash
export GROQ_API_KEY=your-key-here
# On Windows: set GROQ_API_KEY=your-key-here
```

## Quick Demo

Run the included demo script:
```bash
python demo.py
```

This will process a sample procedure and show both the extracted steps and generated RDF.

## Usage In Your Code

```python
from pocketgroq import GroqProvider
from pocketgroq_pke import ProceduralExtractor

# Initialize
groq = GroqProvider()  # Uses GROQ_API_KEY from environment
extractor = ProceduralExtractor(groq)

# Example text
text = """
How to make coffee:
1. Fill kettle with water and boil
2. Add 2 tablespoons of coffee to french press
3. Once water is boiling, wait 30 seconds
4. Pour water over coffee and steep for 4 minutes
5. Press down the plunger and serve
"""

# Extract procedure
procedure = await extractor.extract_procedure(text)

# Print structured output
for i, step in enumerate(procedure.steps, 1):
    print(f"\nStep {i}: {step.text}")
    print(f"Actions: {', '.join(step.actions)}")
    print(f"Objects: {', '.join(step.direct_objects)}")
    print(f"Equipment: {', '.join(step.equipment)}")
    if step.time_info:
        print(f"Time: {step.time_info}")

# Generate knowledge graph
kg = extractor.generate_kg(procedure)
print("\nRDF Knowledge Graph:")
print(kg)
```

## Repository Structure

```
PocketgroqPKE/
├── pocketgroq_pke/
│   ├── __init__.py
│   ├── extractor.py    # Main extraction logic
│   └── types.py        # Data classes for procedures/steps
├── demo.py             # Interactive demo script
├── README.md
└── setup.py
```

## Requirements

- Python 3.7+
- PocketGroq base package
- Groq API key with access to Llama models

## Error Handling

The extractor includes robust error handling:

```python
try:
    procedure = await extractor.extract_procedure(text)
except Exception as e:
    print(f"Extraction failed: {e}")
```

Common errors:
- Missing/invalid API key
- Rate limiting
- Invalid input text format
- Network connectivity issues

## RDF Schema

The generated knowledge graphs use these ontologies:
- p-plan: Plans and steps
- frapo: Equipment and resources  
- time: Temporal information
- po: Custom procedural extensions

Example output structure:
```turtle
@prefix p-plan: <http://purl.org/net/p-plan#> .
@prefix frapo: <http://purl.org/cerif/frapo/> .
@prefix time: <http://www.w3.org/2006/time#> .
@prefix po: <http://example.org/procedural#> .

:make_coffee a p-plan:Plan ;
    rdfs:label "How to make coffee" .

:make_coffee_step1 a p-plan:Step ;
    rdfs:label "Fill kettle with water and boil" ;
    po:hasStep :make_coffee ;
    frapo:usesEquipment :kettle .
```

## License

MIT License - See LICENSE file for details.
