"""
Unit tests for NLU Engine
"""

import pytest
from src.core.nlu_engine import IndustrialNLU, Intent


class TestIndustrialNLU:
    """Test cases for NLU engine"""
    
    @pytest.fixture
    def nlu_engine(self):
        """Create NLU engine for testing"""
        return IndustrialNLU()
    
    def test_initialization(self, nlu_engine):
        """Test NLU engine initialization"""
        assert nlu_engine is not None
        assert nlu_engine.patterns is not None
        assert nlu_engine.intent_keywords is not None
    
    def test_parse_query_inventory(self, nlu_engine):
        """Test parsing inventory query command"""
        command = "Check stock for SKU AB-12345"
        
        parsed = nlu_engine.parse(command)
        
        assert parsed.intent == Intent.QUERY_INVENTORY
        assert len(parsed.entities) > 0
        
        sku = parsed.get_entity("sku")
        assert sku is not None
        assert sku.value == "AB-12345"
    
    def test_parse_update_inventory(self, nlu_engine):
        """Test parsing inventory update command"""
        command = "Add 50 units of XY-9012 to B7-2"
        
        parsed = nlu_engine.parse(command)
        
        assert parsed.intent == Intent.UPDATE_INVENTORY
        
        sku = parsed.get_entity("sku")
        quantity = parsed.get_entity("quantity")
        location = parsed.get_entity("location")
        operation = parsed.get_entity("operation")
        
        assert sku.value == "XY-9012"
        assert quantity.value == "50"
        assert location.value == "B7-2"
        assert operation.value == "add"
    
    def test_parse_location_query(self, nlu_engine):
        """Test parsing location query command"""
        command = "Where is pallet 7823?"
        
        parsed = nlu_engine.parse(command)
        
        assert parsed.intent == Intent.QUERY_LOCATION
        
        pallet = parsed.get_entity("pallet")
        assert pallet is not None
        assert pallet.value == "7823"
    
    def test_parse_work_order(self, nlu_engine):
        """Test parsing work order commands"""
        command1 = "What's my next task?"
        parsed1 = nlu_engine.parse(command1)
        assert parsed1.intent == Intent.WORK_ORDER_NEXT
        
        command2 = "Mark task complete"
        parsed2 = nlu_engine.parse(command2)
        assert parsed2.intent == Intent.WORK_ORDER_COMPLETE
    
    def test_extract_entities_sku(self, nlu_engine):
        """Test SKU extraction"""
        text = "Check AB-12345 and XY-999999"
        entities = nlu_engine._extract_entities(text)
        
        skus = [e for e in entities if e.type == "sku"]
        assert len(skus) == 2
        assert skus[0].value == "AB-12345"
        assert skus[1].value == "XY-999999"
    
    def test_extract_entities_location(self, nlu_engine):
        """Test location extraction"""
        text = "Move to A5-3 from B12-7"
        entities = nlu_engine._extract_entities(text)
        
        locations = [e for e in entities if e.type == "location"]
        assert len(locations) == 2
        assert "A5-3" in [loc.value for loc in locations]
        assert "B12-7" in [loc.value for loc in locations]
    
    def test_validate_command_valid(self, nlu_engine):
        """Test validation of valid commands"""
        command = "Check stock for SKU AB-12345"
        parsed = nlu_engine.parse(command)
        
        is_valid, error = nlu_engine.validate_command(parsed)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_command_missing_sku(self, nlu_engine):
        """Test validation of command missing SKU"""
        command = "Check stock"
        parsed = nlu_engine.parse(command)
        
        is_valid, error = nlu_engine.validate_command(parsed)
        
        assert is_valid is False
        assert error is not None
        assert "SKU required" in error
    
    def test_unknown_intent(self, nlu_engine):
        """Test handling of unknown commands"""
        command = "Hello how are you?"
        parsed = nlu_engine.parse(command)
        
        assert parsed.intent == Intent.UNKNOWN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
