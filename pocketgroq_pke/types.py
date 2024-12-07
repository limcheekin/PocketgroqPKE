"""
Data classes for procedural knowledge extraction.
"""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Step:
    """
    Represents a single step in a procedure.

    Attributes:
        text: The complete text description of the step
        actions: List of verbs representing actions to be performed
        direct_objects: List of objects being acted upon
        equipment: List of items needed to perform the action
        time_info: Optional temporal information about the step
    """
    text: str
    actions: List[str]
    direct_objects: List[str]
    equipment: List[str]
    time_info: Optional[str] = None

@dataclass
class Procedure:
    """
    Represents a complete procedure with sequential steps.

    Attributes:
        title: Title or name of the procedure
        steps: Ordered list of procedural steps
    """
    title: str
    steps: List[Step]
