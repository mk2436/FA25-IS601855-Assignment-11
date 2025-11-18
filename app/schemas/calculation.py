"""
Calculation Pydantic Schemas

This module defines Pydantic schemas for validating calculation data at the
API boundary. Pydantic provides automatic validation, serialization, and
documentation generation for FastAPI.

Key Concepts:
- Schemas define the shape of data coming in/out of the API
- Validation happens automatically before data reaches your code
- Field validators provide custom validation logic
- Model validators can validate across multiple fields
- ConfigDict controls schema behavior and documentation

Design Pattern: Data Transfer Objects (DTOs)
These schemas act as DTOs, defining contracts between API and clients.
"""

from enum import Enum
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    model_validator
)
from typing import Optional
from uuid import UUID
from datetime import datetime


class CalculationType(str, Enum):
    """
    Enumeration of valid calculation types.
    
    Using an Enum provides:
    1. Type safety: Only valid values can be used
    2. Auto-completion: IDEs can suggest valid values
    3. Documentation: Automatically appears in OpenAPI spec
    4. Validation: Pydantic automatically rejects invalid values
    
    Inheriting from str makes this a string enum, so values serialize
    naturally as strings in JSON.
    """
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"


class CalculationBase(BaseModel):
    """
    Base schema for calculation data.
    
    This schema defines the common fields that all calculation requests share.
    It's used as a base for more specific schemas (Create, Update, Read).
    
    Design Pattern: DRY (Don't Repeat Yourself) — common fields and validators
    are defined once and re-used in other schemas.
    """
    a: float = Field(
        ...,
        description="First numeric operand for the calculation",
        examples=[10.5]
    )
    b: float = Field(
        ...,
        description="Second numeric operand for the calculation",
        examples=[3.0]
    )
    type: CalculationType = Field(
        ...,
        description="Type of calculation to perform",
        examples=["addition"]
    )

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        """
        Validate and normalize the calculation type.
        
        This validator ensures that the type is a string and converts it to
        lowercase for case-insensitive comparison. It runs BEFORE Pydantic's
        standard validation (mode="before").
        
        Args:
            v: The value to validate
            
        Returns:
            The normalized (lowercase) type value
            
        Raises:
            ValueError: If the type is not a valid calculation type
        """
        if isinstance(v, str):
            v = v.lower()
        allowed = {e.value for e in CalculationType}
        if v not in allowed:
            raise ValueError(
                f"Type must be one of: {', '.join(sorted(allowed))}"
            )
        return v

    @field_validator("a", "b", mode="before")
    @classmethod
    def validate_operand_exists_and_float(cls, v):
        """
        Validate that the operand exists and is a valid float.

        This runs BEFORE Pydantic's standard validation.

        Args:
            v: The value to validate

        Returns:
            The validated value

        Raises:
            ValueError: If the input is None or not a valid float
        """
        if v is None:
            raise ValueError("Both operands 'a' and 'b' must be provided")
        if not isinstance(v, (float, int)):
            raise ValueError("Input should be a valid float")
        return v


    @model_validator(mode="after")
    def validate_operands(self) -> "CalculationBase":
        """
        Cross-field validation for operands.
        
        Business Rules:
        2. Division cannot have a zero divisor ('b')
        
        This demonstrates LBYL (Look Before You Leap) by validating before
        attempting the operation.
        
        Returns:
            self: The validated model instance
            
        Raises:
            ValueError: If validation fails
        """
        
        # Check for division by zero
        if self.type == CalculationType.DIVISION and self.b == 0:
            raise ValueError("Cannot divide by zero")
        
        return self


    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {"a": 10.5, "b": 3.0, "type": "addition"},
                {"a": 100.0, "b": 2.0, "type": "division"}
            ]
        }
    )


class CalculationCreate(CalculationBase):
    """
    Schema for creating a new Calculation.
    
    This schema is used when a client wants to create a calculation.
    It includes the user_id to associate the calculation with a user.
    
    In a real application, the user_id would typically come from the
    authenticated user's session rather than the request body.
    """
    user_id: UUID = Field(
        ...,
        description="UUID of the user who owns this calculation",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "a": 10.5,
                "b": 3.0,
                "type": "addition",
                "user_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


class CalculationUpdate(BaseModel):
    """
    Schema for updating an existing Calculation.
    
    This schema allows clients to update the operands of an existing
    calculation. All fields are optional since partial updates are allowed.
    
    Note: The calculation type cannot be changed after creation. If you need
    a different type, create a new calculation.
    """
    a: Optional[float] = Field(
        None,
        description="Updated first numeric operand",
        examples=[42.0]
    )
    b: Optional[float] = Field(
        None,
        description="Updated second numeric operand",
        examples=[7.0]
    )

    type: Optional[CalculationType] = Field(
        None,
        description="Type of calculation to perform",
        examples=["addition"]
    )


    @model_validator(mode="after")
    def validate_operands(self) -> "CalculationUpdate":
        """
        Validate updated operands.

        Business Rules:
        1. Both operands must be provided.
        2. Division cannot have a zero divisor (`b`).

        Raises:
            ValueError: If validation fails.
        """
        # Ensure both operands are provided
        if self.a is None or self.b is None:
            raise ValueError("Both operands 'a' and 'b' must be provided for update")

        # Prevent division by zero
        if getattr(self, "type", None) == CalculationType.DIVISION and self.b == 0:
            raise ValueError("Cannot divide by zero")

        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"a": 42.0, "b": 7.0}}
    )


class CalculationRead(CalculationBase):
    """
    Schema for reading a Calculation from the database.
    
    This schema includes all the fields that are returned when reading
    a calculation, including database-generated fields like id, timestamps,
    and the computed result.
    
    The from_attributes=True config allows this schema to be populated from
    ORM instances using model.from_orm(db_calculation).
    """
    id: UUID = Field(
        ...,
        description="Unique UUID of the calculation",
        examples=["123e4567-e89b-12d3-a456-426614174999"]
    )
    user_id: UUID = Field(
        ...,
        description="UUID of the user who owns this calculation",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    result: float = Field(
        ...,
        description="Result of the calculation",
        examples=[13.5]
    )
    created_at: datetime = Field(
        ...,
        description="Time when the calculation was created"
    )
    updated_at: datetime = Field(
        ...,
        description="Time when the calculation was last updated"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174999",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "a": 10.5,
                "b": 3.0,
                "type": "addition",
                "result": 13.5,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }
    )
