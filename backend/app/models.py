from typing import Optional
from pydantic import BaseModel, Field

class Ingredient(BaseModel):
 name: str = Field(min_length=1, max_length=100)
 quantity: float = Field(ge=0)
 unit: str = Field(min_length=1, max_length=24)
 optional: bool = False

class IngredientGroup(BaseModel):
 name: str = Field(min_length=1, max_length=100)
 ingredients: list[Ingredient] = Field(default_factory=list)

class Instruction(BaseModel):
 step: int = Field(ge=1)
 text: str = Field(min_length=1, max_length=2000)
 duration_minutes: Optional[int] = Field(default=None, ge=0)

class Recipe(BaseModel):
 id: Optional[str] = None
 name: str = Field(min_length=1, max_length=120)
 description: str = Field(default="", max_length=1000)
 base_servings: int = Field(gt=0, le=1000)
 prep_minutes: int = Field(default=0, ge=0)
 cook_minutes: int = Field(default=0, ge=0)
 groups: list[IngredientGroup] = Field(default_factory=list)
 instructions: list[Instruction] = Field(default_factory=list)
 tags: list[str] = Field(default_factory=list)

class PantryItem(BaseModel):
 id: Optional[str] = None
 ingredient: str = Field(min_length=1, max_length=100)
 quantity: float = Field(ge=0)
 unit: str = Field(min_length=1, max_length=24)
 category: str = Field(default="Other", max_length=60)
 low_stock_at: float = Field(default=0, ge=0)

class Conversion(BaseModel):
 ingredient: str = Field(min_length=1, max_length=100)
 from_unit: str = Field(min_length=1, max_length=24)
 to_unit: str = Field(min_length=1, max_length=24)
 factor: float = Field(gt=0)

class ShoppingItem(BaseModel):
 id: Optional[str] = None
 ingredient: str = Field(min_length=1, max_length=100)
 quantity: float = Field(ge=0)
 unit: str = Field(min_length=1, max_length=24)
 checked: bool = False

class ScaleRequest(BaseModel):
 servings: int = Field(gt=0, le=1000)
