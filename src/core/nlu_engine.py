"""
Natural Language Understanding Engine
Parses industrial commands and extracts intent + entities
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Intent(Enum):
    """Command intent types"""
    QUERY_INVENTORY = "query_inventory"
    UPDATE_INVENTORY = "update_inventory"
    QUERY_LOCATION = "query_location"
    MOVE_ITEM = "move_item"
    WORK_ORDER_NEXT = "work_order_next"
    WORK_ORDER_COMPLETE = "work_order_complete"
    EQUIPMENT_HELP = "equipment_help"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """Extracted entity from command"""
    type: str
    value: str
    confidence: float = 1.0


@dataclass
class ParsedCommand:
    """Parsed command structure"""
    intent: Intent
    entities: List[Entity]
    raw_text: str
    confidence: float
    
    def get_entity(self, entity_type: str) -> Optional[Entity]:
        """Get first entity of specified type"""
        for entity in self.entities:
            if entity.type == entity_type:
                return entity
        return None
    
    def get_all_entities(self, entity_type: str) -> List[Entity]:
        """Get all entities of specified type"""
        return [e for e in self.entities if e.type == entity_type]


class IndustrialNLU:
    """Natural language understanding for industrial commands"""
    
    def __init__(self, custom_vocabulary: Optional[Dict[str, List[str]]] = None):
        """
        Initialize NLU engine
        
        Args:
            custom_vocabulary: Additional domain-specific terms
        """
        # Regex patterns for entity extraction
        self.patterns = {
            "sku": re.compile(r'\b([A-Z]{2,3}-?\d{4,6})\b'),
            "location": re.compile(r'\b([A-Z]\d{1,2}-\d{1,2})\b'),
            "pallet": re.compile(r'\bpallet\s+(\d+)\b', re.IGNORECASE),
            "quantity": re.compile(r'\b(\d+)\s+units?\b', re.IGNORECASE),
            "number": re.compile(r'\b(\d+)\b'),
        }
        
        # Intent detection keywords
        self.intent_keywords = {
            Intent.QUERY_INVENTORY: [
                "check", "how many", "stock", "count", "inventory for",
                "do we have", "what's the stock", "quantity of"
            ],
            Intent.UPDATE_INVENTORY: [
                "update", "add", "remove", "adjust", "subtract",
                "increase", "decrease", "put in", "take out"
            ],
            Intent.QUERY_LOCATION: [
                "where is", "find", "location of", "locate",
                "where can I find", "which bin", "which rack"
            ],
            Intent.MOVE_ITEM: [
                "move", "transfer", "relocate", "shift"
            ],
            Intent.WORK_ORDER_NEXT: [
                "next task", "what's next", "next job", "next order",
                "what should I do", "my next assignment"
            ],
            Intent.WORK_ORDER_COMPLETE: [
                "mark complete", "finished", "done with", "completed",
                "task done", "mark done"
            ],
            Intent.EQUIPMENT_HELP: [
                "how to", "how do I", "troubleshoot", "manual for",
                "help with", "instructions for"
            ]
        }
        
        # Operation type keywords
        self.operation_keywords = {
            "add": ["add", "put", "insert", "increase", "stock"],
            "remove": ["remove", "take", "subtract", "decrease", "pull"],
        }
        
        # Custom vocabulary
        self.custom_vocab = custom_vocabulary or {}
        
    def parse(self, text: str) -> ParsedCommand:
        """
        Parse command text to extract intent and entities
        
        Args:
            text: Raw command text
            
        Returns:
            ParsedCommand object
        """
        logger.debug(f"Parsing command: '{text}'")
        
        text_lower = text.lower()
        
        # Extract entities
        entities = self._extract_entities(text)
        
        # Detect intent
        intent, confidence = self._detect_intent(text_lower, entities)
        
        logger.info(f"Intent: {intent.value}, Confidence: {confidence:.2f}")
        
        return ParsedCommand(
            intent=intent,
            entities=entities,
            raw_text=text,
            confidence=confidence
        )
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract all entities from text"""
        entities = []
        
        # Extract SKUs
        for match in self.patterns["sku"].finditer(text):
            entities.append(Entity(
                type="sku",
                value=match.group(1),
                confidence=1.0
            ))
        
        # Extract locations (bin/rack identifiers)
        for match in self.patterns["location"].finditer(text):
            entities.append(Entity(
                type="location",
                value=match.group(1),
                confidence=1.0
            ))
        
        # Extract pallet numbers
        for match in self.patterns["pallet"].finditer(text):
            entities.append(Entity(
                type="pallet",
                value=match.group(1),
                confidence=0.9
            ))
        
        # Extract quantities
        qty_match = self.patterns["quantity"].search(text)
        if qty_match:
            entities.append(Entity(
                type="quantity",
                value=qty_match.group(1),
                confidence=1.0
            ))
        else:
            # Fallback to any number
            numbers = self.patterns["number"].findall(text)
            if numbers and not any(e.type == "quantity" for e in entities):
                # Use first number as potential quantity
                entities.append(Entity(
                    type="quantity",
                    value=numbers[0],
                    confidence=0.6
                ))
        
        # Extract operation type
        text_lower = text.lower()
        for operation, keywords in self.operation_keywords.items():
            if any(kw in text_lower for kw in keywords):
                entities.append(Entity(
                    type="operation",
                    value=operation,
                    confidence=0.8
                ))
                break
        
        return entities
    
    def _detect_intent(
        self,
        text: str,
        entities: List[Entity]
    ) -> Tuple[Intent, float]:
        """
        Detect command intent
        
        Args:
            text: Lowercased command text
            entities: Extracted entities
            
        Returns:
            Tuple of (Intent, confidence_score)
        """
        scores = {}
        
        # Score each intent based on keyword matches
        for intent, keywords in self.intent_keywords.items():
            score = 0.0
            matches = 0
            
            for keyword in keywords:
                if keyword in text:
                    matches += 1
                    # Longer keywords get higher weight
                    score += len(keyword.split())
            
            if matches > 0:
                scores[intent] = score / len(keywords)
        
        # If no keyword matches, use heuristics
        if not scores:
            return self._heuristic_intent(text, entities)
        
        # Get highest scoring intent
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent], 1.0)
        
        return best_intent, confidence
    
    def _heuristic_intent(
        self,
        text: str,
        entities: List[Entity]
    ) -> Tuple[Intent, float]:
        """Fallback intent detection using heuristics"""
        
        # Has SKU + location + operation = update
        has_sku = any(e.type == "sku" for e in entities)
        has_location = any(e.type == "location" for e in entities)
        has_operation = any(e.type == "operation" for e in entities)
        has_quantity = any(e.type == "quantity" for e in entities)
        
        if has_sku and has_location and has_operation:
            return Intent.UPDATE_INVENTORY, 0.7
        
        # Has SKU but no operation = query
        if has_sku and not has_operation:
            return Intent.QUERY_INVENTORY, 0.6
        
        # Question about location
        if "where" in text or "location" in text:
            return Intent.QUERY_LOCATION, 0.6
        
        # Task/work order related
        if "task" in text or "order" in text:
            if "next" in text:
                return Intent.WORK_ORDER_NEXT, 0.7
            elif "complete" in text or "done" in text:
                return Intent.WORK_ORDER_COMPLETE, 0.7
        
        return Intent.UNKNOWN, 0.0
    
    def validate_command(self, parsed: ParsedCommand) -> Tuple[bool, Optional[str]]:
        """
        Validate that command has required entities
        
        Args:
            parsed: ParsedCommand to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if parsed.intent == Intent.QUERY_INVENTORY:
            if not parsed.get_entity("sku"):
                return False, "SKU required for inventory query"
        
        elif parsed.intent == Intent.UPDATE_INVENTORY:
            if not parsed.get_entity("sku"):
                return False, "SKU required for inventory update"
            if not parsed.get_entity("quantity"):
                return False, "Quantity required for inventory update"
            if not parsed.get_entity("operation"):
                return False, "Operation (add/remove) required for inventory update"
        
        elif parsed.intent == Intent.QUERY_LOCATION:
            if not (parsed.get_entity("sku") or parsed.get_entity("pallet")):
                return False, "SKU or pallet number required for location query"
        
        elif parsed.intent == Intent.MOVE_ITEM:
            if not parsed.get_entity("location"):
                return False, "Destination location required for move"
        
        return True, None


if __name__ == "__main__":
    # Test the NLU engine
    nlu = IndustrialNLU()
    
    test_commands = [
        "Check stock for SKU AB-12345",
        "Add 50 units of XY-9012 to B7-2",
        "Where is pallet 7823?",
        "What's my next task?",
        "Mark task complete"
    ]
    
    for cmd in test_commands:
        parsed = nlu.parse(cmd)
        print(f"\nCommand: {cmd}")
        print(f"Intent: {parsed.intent.value} (confidence: {parsed.confidence:.2f})")
        print(f"Entities: {[(e.type, e.value) for e in parsed.entities]}")
        
        valid, error = nlu.validate_command(parsed)
        print(f"Valid: {valid}" + (f" - {error}" if error else ""))
