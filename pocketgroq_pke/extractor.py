"""
Core implementation of procedural knowledge extraction with PDF support and visualization.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import PyPDF2
import graphviz
from pocketgroq import GroqProvider

from .types import Procedure, Step

class ProceduralExtractor:
    """
    Extracts structured procedural knowledge from text or PDF using PocketGroq.
    Includes visualization capabilities.
    """
    def __init__(self, groq_provider: GroqProvider, model: str = "llama3-8b-8192", temperature: float = 0.1):
        """Initialize extractor with optional model customization."""
        self.groq = groq_provider
        self.model = model
        self.temperature = temperature

        # Load extraction prompt template
        template_path = Path(__file__).parent / "templates" / "extraction.txt"
        if not template_path.exists():
            raise FileNotFoundError(f"Extraction template not found at {template_path}")
        with open(template_path) as f:
            self.extraction_prompt = f.read()

    def extract_text_from_pdf(self, pdf_path: Union[str, Path]) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            FileNotFoundError: If PDF file not found
            PyPDF2.PdfReadError: If PDF is corrupted or unreadable
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        try:
            text_content = []
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text_content.append(page.extract_text())
                    
            return "\n".join(text_content)
            
        except PyPDF2.PdfReadError as e:
            raise PyPDF2.PdfReadError(f"Failed to read PDF {pdf_path}: {str(e)}")

    async def extract_procedure_from_file(self, file_path: Union[str, Path]) -> Procedure:
        """
        Extract procedure from a text or PDF file.
        
        Args:
            file_path: Path to input file (.txt or .pdf)
            
        Returns:
            Extracted Procedure object
            
        Raises:
            ValueError: If file type not supported
            FileNotFoundError: If file not found
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if file_path.suffix.lower() == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
        return await self.extract_procedure(text)

    def visualize(self, procedure: Procedure, output_path: Union[str, Path, None] = None) -> Path:
        """
        Create a graphical visualization of the procedure.
        
        Args:
            procedure: Procedure object to visualize
            output_path: Optional path for output file. If not provided,
                        will use procedure title with .pdf extension.
                        
        Returns:
            Path to generated visualization file
            
        Raises:
            OSError: If file cannot be written
            graphviz.ExecutableNotFound: If Graphviz is not installed
        """
        # Create graph
        dot = graphviz.Digraph(comment=procedure.title)
        dot.attr(rankdir='TB')  # Top to bottom layout
        
        # Add procedure node
        proc_id = self._safe_id(procedure.title)
        dot.node(proc_id, procedure.title, shape='box', style='filled', fillcolor='lightblue')
        
        # Add steps with their components
        prev_step = None
        for i, step in enumerate(procedure.steps):
            step_id = f"{proc_id}_step{i+1}"
            
            # Step node
            dot.node(step_id, step.text, shape='box')
            dot.edge(proc_id, step_id)
            
            # Link to previous step
            if prev_step:
                dot.edge(prev_step, step_id, dir='forward')
                
            # Add actions, objects and equipment
            for j, action in enumerate(step.actions):
                action_id = f"{step_id}_action{j}"
                dot.node(action_id, action, shape='ellipse', style='filled', fillcolor='lightgreen')
                dot.edge(step_id, action_id)
                
                # Link action to direct object if available
                if j < len(step.direct_objects):
                    obj_id = f"{step_id}_obj{j}"
                    dot.node(obj_id, step.direct_objects[j], shape='diamond')
                    dot.edge(action_id, obj_id)
                    
            # Add equipment
            for j, equip in enumerate(step.equipment):
                equip_id = f"{step_id}_equip{j}"
                dot.node(equip_id, equip, shape='hexagon', style='filled', fillcolor='lightyellow')
                dot.edge(step_id, equip_id)
                
            prev_step = step_id

        # Handle output path
        if not output_path:
            output_path = Path(f"{self._safe_id(procedure.title)}.pdf")
        else:
            output_path = Path(output_path)
            if not output_path.suffix:
                output_path = output_path.with_suffix('.pdf')
                
        # Render graph
        try:
            dot.render(str(output_path.with_suffix('')), format='pdf', cleanup=True)
            return output_path
        except graphviz.ExecutableNotFound:
            raise graphviz.ExecutableNotFound(
                "Graphviz executable not found. Please install Graphviz: "
                "https://graphviz.org/download/"
            )
        

    def _extract_title_from_text(self, text: str) -> str:
        """Extract title from input text."""
        # Try to find "How to" format
        how_to_match = re.match(r'^[Hh]ow to[^:]+:', text)
        if how_to_match:
            return how_to_match.group(0).rstrip(':').strip()
        
        # Try first line ending in colon
        first_line = text.split('\n')[0].strip()
        if first_line.endswith(':'):
            return first_line.rstrip(':').strip()
            
        # Fallback to first line
        return first_line

    async def extract_procedure(self, text: str) -> Procedure:
        """
        Extract procedural knowledge from text.

        Args:
            text: Input text describing a procedure

        Returns:
            Procedure object containing structured steps
            
        Raises:
            ValueError: If text appears invalid or extraction fails
            Exception: For other extraction errors
        """
        if not text.strip():
            raise ValueError("Input text cannot be empty")

        # Pre-extract title for prompt
        title = self._extract_title_from_text(text)
            
        # Prepare extraction prompt
        prompt = (
            self.extraction_prompt + 
            f"\nTitle: {title}\n\n" +
            "Text to analyze:\n" + text
        )
        
        try:
            # Get LLM extraction
            response = await self.groq.generate(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=2048,
                async_mode=True
            )
            
            # Parse into structured format
            procedure = self._parse_extraction_response(response, fallback_title=title)
            return procedure
            
        except Exception as e:
            raise Exception(f"Extraction failed: {str(e)}")

    def _parse_extraction_response(self, response: str, fallback_title: str = "") -> Procedure:
        """Parse LLM response into structured Procedure object."""
        lines = response.strip().split('\n')
        
        # Get title
        title = fallback_title  # Use fallback by default
        for line in lines:
            if line.startswith('title:'):
                extracted_title = line.split(':', 1)[1].strip()
                if extracted_title:  # Only use if non-empty
                    title = extracted_title
                break

        # Extract steps
        steps = []
        current_step = None
        
        for line in lines:
            line = line.strip()
            
            # New step starts with number
            if re.match(r'^\d+\.', line):
                if current_step:
                    steps.append(current_step)
                current_step = Step(
                    text="",
                    actions=[],
                    direct_objects=[],
                    equipment=[],
                    time_info=None
                )
                
            if not current_step:
                continue
                
            # Parse step components
            if 'text:' in line:
                current_step.text = line.split(':', 1)[1].strip()
            elif 'actions:' in line:
                current_step.actions = self._parse_list(line.split(':', 1)[1])
            elif 'direct_objects:' in line:
                current_step.direct_objects = self._parse_list(line.split(':', 1)[1])
            elif 'equipment:' in line:
                current_step.equipment = self._parse_list(line.split(':', 1)[1]) 
            elif 'time:' in line:
                time_info = line.split(':', 1)[1].strip()
                current_step.time_info = time_info if time_info != "null" else None
                
        # Add final step
        if current_step:
            steps.append(current_step)
            
        if not steps:
            raise ValueError("Failed to extract any procedure steps")
            
        return Procedure(title=title, steps=steps)

    def _parse_list(self, text: str) -> List[str]:
        """Parse comma-separated list from text, handling brackets and whitespace."""
        text = text.strip().strip('[]')
        if not text:
            return []
        return [item.strip() for item in text.split(',') if item.strip()]
        
    def generate_kg(self, procedure: Procedure) -> str:
        """
        Generate RDF knowledge graph in Turtle format.
        
        Args:
            procedure: Extracted procedure to convert to RDF

        Returns:
            String containing RDF in Turtle format
        """
        # Base prefix definitions
        turtle = """
        @prefix p-plan: <http://purl.org/net/p-plan#> .
        @prefix khub-proc: <https://knowledge.c-innovationhub.com/k-hub/procedure#> .
        @prefix frapo: <http://purl.org/cerif/frapo/> .
        @prefix time: <http://www.w3.org/2006/time#> .
        @prefix po: <http://example.org/procedural#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        
        """
        
        # Create procedure
        proc_id = self._safe_id(procedure.title)
        turtle += f"""
        :{proc_id} a p-plan:Plan ;
            rdfs:label "{procedure.title}" .
        """
        
        # Add steps
        prev_step = None
        for i, step in enumerate(procedure.steps):
            step_id = f"{proc_id}_step{i+1}"
            
            # Basic step info
            turtle += f"""
            :{step_id} a p-plan:Step ;
                rdfs:label "{step.text}" ;
            """
            
            # Link to procedure
            turtle += f"    po:hasStep :{proc_id} ;\n"
            
            # Add actions and objects
            for j, (action, obj) in enumerate(zip(step.actions, step.direct_objects)):
                action_id = f"{step_id}_action{j+1}"
                obj_id = f"{step_id}_obj{j+1}"
                
                turtle += f"""
                po:hasAction :{action_id} ;
                po:hasDirectObjectOfAction :{obj_id} ;
                """
                
            # Add equipment
            for j, equip in enumerate(step.equipment):
                equip_id = f"{step_id}_equip{j+1}"
                turtle += f"    frapo:usesEquipment :{equip_id} ;\n"
                
            # Add time info if present    
            if step.time_info:
                time_id = f"{step_id}_time"
                turtle += f"    time:hasTime :{time_id} ;\n"
                
            # Link to previous step
            if prev_step:
                turtle += f"    p-plan:precededBy :{prev_step} ;\n"
                
            turtle += "    .\n"
            prev_step = step_id
            
        return turtle

    def _safe_id(self, text: str) -> str:
        """Convert text to safe ID for RDF."""
        return re.sub(r'[^a-zA-Z0-9]', '_', text.lower())

    def save_kg(self, procedure: Procedure, filepath: Union[str, Path, None] = None) -> Path:
        """
        Generate and save RDF knowledge graph to file.
        
        Args:
            procedure: Extracted procedure to convert to RDF
            filepath: Optional path where to save the file. If not provided,
                     will generate filename from procedure title.
        
        Returns:
            Path object pointing to saved file
        
        Raises:
            OSError: If file cannot be written
            Exception: For other errors during RDF generation
        """
        # Generate filename from procedure title
        safe_title = self._safe_id(procedure.title)
        
        # Use provided path or default to current directory
        if filepath:
            target_path = Path(filepath)
            if target_path.is_dir() or str(target_path) == '.':
                # If filepath is a directory, use generated filename in that directory
                target_path = target_path / f"{safe_title}.ttl"
            elif not target_path.suffix:
                # If no extension provided, add .ttl
                target_path = target_path.with_suffix('.ttl')
            elif target_path.suffix != '.ttl':
                # If wrong extension, replace with .ttl
                target_path = target_path.with_suffix('.ttl')
        else:
            # Default to current directory with generated filename
            target_path = Path(f"{safe_title}.ttl")
            
        # Create directory if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Generate RDF
            kg = self.generate_kg(procedure)
            
            # Save to file
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(kg)
                
            return target_path
            
        except OSError as e:
            raise OSError(f"Failed to save knowledge graph to {target_path}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating knowledge graph: {str(e)}")