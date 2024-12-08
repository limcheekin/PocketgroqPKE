# PocketgroqPKE - Procedural Knowledge Extractor

An extension for PocketGroq that extracts structured procedural knowledge from text and PDFs, generates RDF knowledge graphs, and creates visualizations.

## Overview

This extension adds procedural knowledge extraction capabilities to PocketGroq, allowing you to:

- Extract step-by-step procedures from unstructured text or PDF files
- Identify actions, direct objects, equipment, and temporal information
- Generate RDF knowledge graphs using standard procedural ontologies
- Create PDF visualizations of extracted procedures
- Convert RDF/TTL to human-readable markdown
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

The demo offers several options:
1. Built-in example: Making coffee
2. Built-in example: Cleaning a monitor
3. Built-in example: Planting a tree
0. Enter your own text
F. Load from file (PDF or TXT)

For each option, the demo will:
- Extract the procedural knowledge
- Display the structured steps
- Generate an RDF knowledge graph
- Create a PDF visualization
- Save both the RDF (.ttl) and visualization (.pdf) files

## Usage In Your Code

### Basic Text Extraction

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
```

### PDF Input and Visualization

```python
# Extract from PDF
procedure = await extractor.extract_procedure_from_file("document.pdf")

# Generate and save visualization
viz_path = extractor.visualize(procedure)
print(f"Visualization saved to: {viz_path}")

# Generate and save RDF
rdf_path = extractor.save_kg(procedure)
print(f"Knowledge graph saved to: {rdf_path}")
```

### Converting TTL to Markdown

The RDF/TTL knowledge graphs can be converted to human-readable markdown format:

```python
# Read TTL file
with open("procedure.ttl", "r") as f:
    ttl_content = f.read()

# Create markdown file with same base name
base_name = Path("procedure.ttl").stem
md_path = f"{base_name}.md"

with open(md_path, "w") as f:
    f.write("# " + procedure.title + "\n\n")
    f.write("## Steps\n\n")
    for i, step in enumerate(procedure.steps, 1):
        f.write(f"{i}. {step.text}\n\n")
```

## Repository Structure

```
PocketgroqPKE/
├── pocketgroq_pke/
│   ├── __init__.py
│   ├── extractor.py    # Main extraction logic
│   ├── types.py        # Data classes for procedures/steps
│   └── templates/      # Extraction prompt templates
│       └── extraction.txt
├── examples/           # Example usage scripts
│   ├── basic_usage.py
│   ├── batch_processing.py
│   ├── custom_prompts.py
│   └── rdf_output.py
├── demo.py            # Interactive demo script
├── README.md
└── setup.py
```

## Requirements

- Python 3.7+
- PocketGroq base package
- Groq API key with access to Llama models
- PyPDF2 for PDF processing
- Graphviz for visualization generation

## Error Handling

The extractor includes robust error handling:

```python
try:
    procedure = await extractor.extract_procedure(text)
except ValueError as e:
    print(f"Invalid input: {e}")
except PyPDF2.PdfReadError as e:
    print(f"PDF reading error: {e}")
except graphviz.ExecutableNotFound:
    print("Graphviz not installed")
except Exception as e:
    print(f"Extraction failed: {e}")
```

Common errors:
- Missing/invalid API key
- Rate limiting
- Invalid input text format
- PDF parsing errors
- Network connectivity issues
- Missing Graphviz installation

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

## Visualization

The visualization feature creates PDF files that show:
- Overall procedure structure
- Step sequence and relationships
- Actions and their direct objects
- Equipment used in each step
- Temporal information when available

The generated PDFs use different shapes and colors to distinguish between:
- Steps (boxes)
- Actions (green ellipses)
- Direct objects (diamonds)
- Equipment (yellow hexagons)

## License

MIT License - See LICENSE file for details.
