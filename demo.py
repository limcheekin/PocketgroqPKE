#!/usr/bin/env python3
"""
Demo script for PocketgroqPKE - Procedural Knowledge Extractor.
Demonstrates extraction of procedures from text and RDF generation.
"""
import asyncio
import os
import sys
from pathlib import Path
from pocketgroq import GroqProvider
from pocketgroq_pke import ProceduralExtractor

# Example procedures of varying complexity
EXAMPLES = {
    "coffee": """
    How to Make Pour-Over Coffee:
    First, heat water to 200°F (93°C). While waiting, place filter in dripper and rinse with hot water.
    Add 2 tablespoons of freshly ground coffee to the filter.
    When water is ready, pour a small amount over the grounds and wait 30 seconds for blooming.
    Slowly pour remaining water in circular motion until you've used 12 oz total.
    Remove filter and serve coffee immediately.
    """,
    
    "monitor": """
    How to Clean a Computer Monitor:
    Turn off the monitor and unplug it from power source.
    Wait 5 minutes for the screen to completely cool down.
    Using a soft microfiber cloth, gently wipe the screen in circular motions.
    For stubborn spots, slightly dampen cloth with distilled water.
    Allow screen to fully dry before plugging back in.
    """,
    
    "tree": """
    How to Plant a Bare Root Tree:
    Soak the tree roots in water for 4-6 hours before planting.
    Dig a hole twice as wide as the root spread and as deep as the root ball.
    Create a small mound in the hole center to spread roots over.
    Position tree and carefully spread roots outward.
    Backfill with soil while checking tree stays straight.
    Water thoroughly and add 3 inches of mulch around base.
    """
}

async def main():
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY environment variable not set")
        sys.exit(1)
        
    # Initialize
    print("Initializing PocketgroqPKE...\n")
    groq = GroqProvider()
    extractor = ProceduralExtractor(groq)
    
    # Let user choose an example
    print("Available examples:")
    for i, (name, _) in enumerate(EXAMPLES.items(), 1):
        print(f"{i}. {name}")
    print("\nOr:")
    print("0. Enter your own text")
    print("F. Load from file (PDF or TXT)")
    
    choice = input("\nSelect an option (0-3 or F): ").strip().upper()
    
    try:
        # Handle file input
        if choice == "F":
            filepath = input("\nEnter file path: ").strip()
            print(f"\nProcessing file: {filepath}")
            print("-" * 60)
            procedure = await extractor.extract_procedure_from_file(filepath)
            print(f"Extracted procedure from: {Path(filepath).name}")
            print("-" * 60)
            
        # Handle text input    
        else:
            if choice == "0":
                print("\nEnter your procedure text (end with two blank lines):")
                lines = []
                empty_lines = 0
                while empty_lines < 2:
                    line = input()
                    if not line:
                        empty_lines += 1
                    else:
                        empty_lines = 0
                    lines.append(line)
                text = "\n".join(lines[:-2])  # Remove final empty lines
            else:
                try:
                    text = list(EXAMPLES.values())[int(choice)-1]
                except (IndexError, ValueError):
                    print("Invalid choice. Using coffee example.")
                    text = EXAMPLES["coffee"]
            
            print("\nProcessing text...")
            print("-" * 60)
            print(text.strip())
            print("-" * 60)
            
            procedure = await extractor.extract_procedure(text)
        
        # Display extracted information
        print("\nExtracted Procedure:")
        print(f"Title: {procedure.title}\n")
        
        for i, step in enumerate(procedure.steps, 1):
            print(f"Step {i}: {step.text}")
            print(f"  Actions: {', '.join(step.actions)}")
            print(f"  Objects: {', '.join(step.direct_objects)}")
            print(f"  Equipment: {', '.join(step.equipment)}")
            if step.time_info:
                print(f"  Time: {step.time_info}")
            print()
            
        # Generate and display RDF
        print("Generated RDF Knowledge Graph:")
        print("-" * 60)
        kg = extractor.generate_kg(procedure)
        print(kg)
        print("-" * 60)

        # Save both RDF and visualization
        rdf_path = extractor.save_kg(procedure)
        viz_path = extractor.visualize(procedure)
        
        print(f"\nFiles saved:")
        print(f"- Knowledge graph (TTL): {rdf_path}")
        print(f"- Visualization (PDF): {viz_path}")
        
    except Exception as e:
        print(f"\nError during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())