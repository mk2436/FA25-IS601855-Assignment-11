# tests/integration/test_calculation_schema.py
"""
Integration Tests for Calculation Pydantic Schemas

These tests verify that Pydantic schemas correctly validate calculation data
before it reaches the application logic. This is an important security and
data integrity layer that prevents invalid data from entering the system.

Key Testing Concepts:
1. Valid Data: Ensure schemas accept correct data
2. Invalid Data: Ensure schemas reject incorrect data with clear messages
3. Edge Cases: Test boundary conditions
4. Business Rules: Verify domain-specific validation (e.g., no division by 0)
"""

import pytest
from uuid import uuid4
from pydantic import ValidationError
from app.schemas.calculation import (
    CalculationType,
    CalculationBase,
    CalculationCreate,
    CalculationUpdate,
    CalculationRead
)


# ============================================================================
# Tests for CalculationType Enum
# ============================================================================

def test_calculation_type_enum_values():
    """Test that CalculationType enum has correct values."""
    assert CalculationType.ADDITION.value == "addition"
    assert CalculationType.SUBTRACTION.value == "subtraction"
    assert CalculationType.MULTIPLICATION.value == "multiplication"
    assert CalculationType.DIVISION.value == "division"


# ============================================================================
# Tests for CalculationBase Schema
# ============================================================================

def test_calculation_base_valid_addition():
    """Test CalculationBase with valid addition data."""
    data = {
        "type": "addition",
        "a": 10.5,
        "b": 3
    }
    calc = CalculationBase(**data)
    assert calc.type == CalculationType.ADDITION
    assert calc.a == 10.5
    assert calc.b == 3


def test_calculation_base_valid_subtraction():
    """Test CalculationBase with valid subtraction data."""
    data = {
        "type": "subtraction",
        "a": 20,
        "b": 5.5
    }
    calc = CalculationBase(**data)
    assert calc.type == CalculationType.SUBTRACTION
    assert calc.a == 20
    assert calc.b == 5.5


def test_calculation_base_case_insensitive_type():
    """Test that calculation type is case-insensitive."""
    for type_variant in ["Addition", "ADDITION", "AdDiTiOn"]:
        data = {"type": type_variant, "a": 1, "b": 2}
        calc = CalculationBase(**data)
        assert calc.type == CalculationType.ADDITION


def test_calculation_base_invalid_type():
    """Test that invalid calculation type raises ValidationError."""
    data = {
        "type": "modulus",  # Invalid type
        "a": 10,
        "b": 3
    }
    with pytest.raises(ValidationError) as exc_info:
        CalculationBase(**data)
    
    errors = exc_info.value.errors()
    assert any("Type must be one of" in str(err) for err in errors)


def test_calculation_base_a_and_b_not_floats():
    """Test that non-list inputs raise ValidationError."""
    data = {
        "type": "addition",
        "a": "not a float",
        "b": "not a float"
    }
    with pytest.raises(ValidationError) as exc_info:
        CalculationBase(**data)
    
    errors = exc_info.value.errors()
    assert any("Input should be a valid float" in str(err) for err in errors)


def test_calculation_base_insufficient_inputs():
    """Test that fewer than 2 inputs raises ValidationError."""
    data = {
        "type": "addition",
        "a": 5,
        "b": None
    }
    with pytest.raises(ValidationError) as exc_info:
        CalculationBase(**data)
    
    # Validation error can be from min_length constraint or model validator
    assert len(exc_info.value.errors()) > 0


def test_calculation_base_b_is_none():
    """Test that b is not None raises ValidationError."""
    data = {
        "type": "multiplication",
        "a": 1,
        "b": None
    }
    with pytest.raises(ValidationError) as exc_info:
        CalculationBase(**data)
    
    errors = exc_info.value.errors()
    assert any("b" in str(err) for err in errors)
    assert len(errors) > 0


def test_calculation_base_division_by_zero():
    """
    Test that division by zero is caught by schema validation.
    
    This demonstrates LBYL (Look Before You Leap): We check for the error
    condition before attempting the operation. This is appropriate at the
    API boundary to provide immediate feedback to the client.
    """
    data = {
        "type": "division",
        "a": 100,
        "b": 0
    }
    with pytest.raises(ValidationError) as exc_info:
        CalculationBase(**data)
    
    errors = exc_info.value.errors()
    assert any("Cannot divide by zero" in str(err) for err in errors)


def test_calculation_base_division_by_zero_in_middle():
    """Test that zero in any denominator position is caught."""
    data = {
        "type": "division",
        "a": 100,
        "b": 0
    }
    with pytest.raises(ValidationError) as exc_info:
        CalculationBase(**data)    
    errors = exc_info.value.errors()
    assert any("Cannot divide by zero" in str(err) for err in errors)

# ============================================================================
# Tests for CalculationCreate Schema
# ============================================================================

def test_calculation_create_valid():
    """Test CalculationCreate with valid data."""
    user_id = uuid4()
    data = {
        "type": "multiplication",
        "a": 2,
        "b": 3,
        "user_id": str(user_id)
    }
    calc = CalculationCreate(**data)
    assert calc.type == CalculationType.MULTIPLICATION
    assert calc.a == 2
    assert calc.b == 3
    assert calc.user_id == user_id


def test_calculation_create_missing_user_id():
    """Test that CalculationCreate requires user_id."""
    data = {
        "type": "addition",
        "a": 1,
        "b": 2,
        # Missing user_id
    }
    with pytest.raises(ValidationError) as exc_info:
        CalculationCreate(**data)
    
    errors = exc_info.value.errors()
    assert any("user_id" in str(err) for err in errors)


def test_calculation_create_invalid_user_id():
    """Test that invalid UUID format raises ValidationError."""
    data = {
        "type": "subtraction",
        "a": 10,
        "b": 5,
        "user_id": "not-a-valid-uuid"
    }
    with pytest.raises(ValidationError):
        CalculationCreate(**data)


# ============================================================================
# Tests for CalculationUpdate Schema
# ============================================================================

def test_calculation_update_valid():
    """Test CalculationUpdate with valid data."""
    data = {
        "a": 42,
        "b": 7
    }
    calc = CalculationUpdate(**data)
    assert calc.a == 42
    assert calc.b == 7


def test_calculation_update_insufficient_inputs():
    """Test that CalculationUpdate validates minimum inputs."""
    data = {
        "a": 5,
        "b": None
    }
    with pytest.raises(ValidationError) as exc_info:
        CalculationUpdate(**data)
    
    # Validation error can be from min_length constraint or model validator
    assert len(exc_info.value.errors()) > 0


# ============================================================================
# Tests for CalculationRead Schema
# ============================================================================

def test_calculation_response_valid():
    """Test CalculationRead with all required fields."""
    from datetime import datetime
    
    data = {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "type": "addition",
        "a": 10,
        "b": 5,
        "result": 15.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    calc = CalculationRead(**data)
    assert calc.result == 15.0
    assert calc.type == CalculationType.ADDITION


def test_calculation_response_missing_result():
    """Test that CalculationRead requires result field."""
    from datetime import datetime
    
    data = {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "type": "multiplication",
        "a": 2,
        "b": 3,
        # Missing result
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    with pytest.raises(ValidationError) as exc_info:
        CalculationRead(**data)
    
    errors = exc_info.value.errors()
    assert any("result" in str(err) for err in errors)


# ============================================================================
# Tests for Complex Validation Scenarios
# ============================================================================

def test_multiple_calculations_with_different_types():
    """
    Test that schemas correctly validate multiple calculations of
    different types.
    """
    user_id = uuid4()
    
    calcs_data = [
        {"type": "addition", "a": 1, "b": 2, "user_id": str(user_id)},
        {"type": "subtraction", "a": 10, "b": 3, "user_id": str(user_id)},
        {"type": "multiplication", "a": 2, "b": 3,
         "user_id": str(user_id)},
        {"type": "division", "a": 100, "b": 5, "user_id": str(user_id)},
    ]
    
    calcs = [CalculationCreate(**data) for data in calcs_data]
    
    assert len(calcs) == 4
    assert calcs[0].type == CalculationType.ADDITION
    assert calcs[1].type == CalculationType.SUBTRACTION
    assert calcs[2].type == CalculationType.MULTIPLICATION
    assert calcs[3].type == CalculationType.DIVISION


def test_schema_with_large_numbers():
    """Test that schemas handle large numbers correctly."""
    data = {
        "type": "multiplication",
        "a": 1e10,
        "b": 1e10
    }
    calc = CalculationBase(**data)
    assert isinstance(calc.a, float)
    assert isinstance(calc.b, float)


def test_schema_with_negative_numbers():
    """Test that schemas accept negative numbers."""
    data = {
        "type": "addition",
        "a": -5,
        "b": -10
    }
    calc = CalculationBase(**data)
    assert calc.a == -5
    assert calc.b == -10


def test_schema_with_mixed_int_and_float():
    """Test that schemas accept mixed integers and floats."""
    data = {
        "type": "subtraction",
        "a": 100,
        "b": 23.5
    }
    calc = CalculationBase(**data)
    assert calc.a == 100
    assert calc.b == 23.5
