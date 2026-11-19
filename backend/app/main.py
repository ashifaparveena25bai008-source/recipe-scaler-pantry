"""API for Recipe Scaler & Pantry Inventory."""
import os
from contextlib import asynccontextmanager
from typing import Any

from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from .models import Conversion, PantryItem, Recipe, ScaleRequest, ShoppingItem

load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "recipe_pantry")
client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

SEED_RECIPES = [
    {"name": "Creamy Tuscan pasta", "description": "A weeknight pasta with tomatoes, spinach and parmesan.", "base_servings": 4, "prep_minutes": 10, "cook_minutes": 20, "tags": ["Dinner", "Italian", "Vegetarian"], "groups": [{"name": "Pasta", "ingredients": [{"name": "Pasta", "quantity": 320, "unit": "g"}, {"name": "Cherry tomatoes", "quantity": 250, "unit": "g"}, {"name": "Heavy cream", "quantity": 200, "unit": "ml"}, {"name": "Baby spinach", "quantity": 100, "unit": "g"}, {"name": "Parmesan", "quantity": 60, "unit": "g"}, {"name": "Garlic cloves", "quantity": 3, "unit": "pcs"}]}, {"name": "To finish", "ingredients": [{"name": "Olive oil", "quantity": 1, "unit": "tbsp", "optional": True}]}], "instructions": [{"step": 1, "text": "Cook the pasta in salted water until al dente. Reserve a cup of pasta water."}, {"step": 2, "text": "Warm olive oil in a pan. Add tomatoes and garlic, then cook until softened."}, {"step": 3, "text": "Stir in cream and spinach. Simmer until the spinach wilts."}, {"step": 4, "text": "Toss with pasta and parmesan, loosening with pasta water as needed."}]},
    {"name": "Lemon herb roast chicken", "description": "Golden roast chicken with lemon and rosemary.", "base_servings": 4, "prep_minutes": 15, "cook_minutes": 60, "tags": ["Dinner", "Mediterranean"], "groups": [{"name": "For the chicken", "ingredients": [{"name": "Whole chicken", "quantity": 1.6, "unit": "kg"}, {"name": "Lemon", "quantity": 2, "unit": "pcs"}, {"name": "Rosemary", "quantity": 3, "unit": "sprigs"}, {"name": "Olive oil", "quantity": 3, "unit": "tbsp"}, {"name": "Garlic cloves", "quantity": 5, "unit": "pcs"}]}], "instructions": [{"step": 1, "text": "Heat the oven to 220°C / 425°F."}, {"step": 2, "text": "Pat the chicken dry. Rub with olive oil, salt and pepper."}, {"step": 3, "text": "Fill the cavity with lemon and rosemary. Roast until the thickest part reaches 74°C / 165°F."}, {"step": 4, "text": "Rest for 15 minutes before carving."}]},
    {"name": "Blueberry oat pancakes", "description": "Soft, fluffy pancakes with juicy blueberries.", "base_servings": 2, "prep_minutes": 10, "cook_minutes": 10, "tags": ["Breakfast", "Vegetarian"], "groups": [{"name": "Batter", "ingredients": [{"name": "All-purpose flour", "quantity": 150, "unit": "g"}, {"name": "Oat milk", "quantity": 180, "unit": "ml"}, {"name": "Blueberries", "quantity": 125, "unit": "g"}, {"name": "Eggs", "quantity": 2, "unit": "pcs"}, {"name": "Maple syrup", "quantity": 2, "unit": "tbsp"}]}], "instructions": [{"step": 1, "text": "Whisk flour, oat milk and eggs until just combined."}, {"step": 2, "text": "Fold in half the blueberries."}, {"step": 3, "text": "Cook small ladles of batter in a warm, lightly oiled pan until bubbles appear; flip and cook through."}, {"step": 4, "text": "Serve with remaining blueberries and maple syrup."}]},
]
SEED_PANTRY = [
    {"ingredient": "pasta", "quantity": 500, "unit": "g", "category": "Dry goods", "low_stock_at": 150},
    {"ingredient": "cherry tomatoes", "quantity": 180, "unit": "g", "category": "Produce", "low_stock_at": 100},
    {"ingredient": "heavy cream", "quantity": 250, "unit": "ml", "category": "Dairy", "low_stock_at": 100},
    {"ingredient": "baby spinach", "quantity": 70, "unit": "g", "category": "Produce", "low_stock_at": 50},
    {"ingredient": "parmesan", "quantity": 100, "unit": "g", "category": "Dairy", "low_stock_at": 30},
    {"ingredient": "garlic cloves", "quantity": 8, "unit": "pcs", "category": "Produce", "low_stock_at": 3},
    {"ingredient": "olive oil", "quantity": 120, "unit": "ml", "category": "Pantry", "low_stock_at": 30},
    {"ingredient": "all-purpose flour", "quantity": 400, "unit": "g", "category": "Baking", "low_stock_at": 100},
    {"ingredient": "oat milk", "quantity": 300, "unit": "ml", "category": "Dairy alternatives", "low_stock_at": 100},
    {"ingredient": "eggs", "quantity": 4, "unit": "pcs", "category": "Dairy", "low_stock_at": 2},
    {"ingredient": "maple syrup", "quantity": 60, "unit": "ml", "category": "Pantry", "low_stock_at": 20},
]
SEED_CONVERSIONS = [
    {"ingredient": "olive oil", "from_unit": "tbsp", "to_unit": "ml", "factor": 15},
    {"ingredient": "maple syrup", "from_unit": "tbsp", "to_unit": "ml", "factor": 15},
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.recipes.create_index("name", unique=True)
    await db.pantry.create_index("ingredient", unique=True)
    await db.conversions.create_index([("ingredient", 1), ("from_unit", 1), ("to_unit", 1)], unique=True)
    await db.shopping.create_index("ingredient")
    if await db.recipes.count_documents({}) == 0:
        await db.recipes.insert_many(SEED_RECIPES)
    if await db.pantry.count_documents({}) == 0:
        await db.pantry.insert_many(SEED_PANTRY)
    for conversion in SEED_CONVERSIONS:
        key = {key: conversion[key] for key in ("ingredient", "from_unit", "to_unit")}
        await db.conversions.update_one(key, {"$setOnInsert": conversion}, upsert=True)
    yield
    client.close()


app = FastAPI(title="Recipe Scaler & Pantry Inventory", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","), allow_methods=["*"], allow_headers=["*"])


def serialize(document: dict[str, Any]) -> dict[str, Any]:
    document["id"] = str(document.pop("_id"))
    return document


def scaled(recipe: dict[str, Any], servings: int) -> dict[str, Any]:
    factor = servings / recipe["base_servings"]
    for group in recipe.get("groups", []):
        for ingredient in group.get("ingredients", []):
            ingredient["quantity"] = round(ingredient["quantity"] * factor, 3)
    recipe["servings"] = servings
    recipe["scale_factor"] = round(factor, 3)
    return recipe


@app.get("/api/health")
async def health():
    await db.command("ping")
    return {"status": "ok", "database": DATABASE_NAME}


@app.get("/api/recipes")
async def list_recipes():
    return [serialize(recipe) async for recipe in db.recipes.find().sort("name", 1)]


@app.post("/api/recipes", status_code=201)
async def create_recipe(value: Recipe):
    document = value.model_dump(exclude={"id"})
    try:
        result = await db.recipes.insert_one(document)
    except Exception as exc:
        if "duplicate key" in str(exc).lower():
            raise HTTPException(409, "A recipe with this name already exists") from exc
        raise
    return serialize(await db.recipes.find_one({"_id": result.inserted_id}))


@app.get("/api/recipes/{recipe_id}")
async def get_recipe(recipe_id: str):
    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(400, "Invalid recipe id")
    recipe = await db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    return serialize(recipe)


@app.put("/api/recipes/{recipe_id}")
async def update_recipe(recipe_id: str, value: Recipe):
    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(400, "Invalid recipe id")
    query = {"_id": ObjectId(recipe_id)}
    await db.recipes.replace_one(query, value.model_dump(exclude={"id"}))
    recipe = await db.recipes.find_one(query)
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    return serialize(recipe)


@app.delete("/api/recipes/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: str):
    if not ObjectId.is_valid(recipe_id) or not (await db.recipes.delete_one({"_id": ObjectId(recipe_id)})).deleted_count:
        raise HTTPException(404, "Recipe not found")


@app.post("/api/recipes/{recipe_id}/scale")
async def scale_recipe(recipe_id: str, value: ScaleRequest):
    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(400, "Invalid recipe id")
    recipe = await db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    return scaled(serialize(recipe), value.servings)


@app.get("/api/pantry")
async def list_pantry():
    return [serialize(item) async for item in db.pantry.find().sort("ingredient", 1)]


@app.post("/api/pantry", status_code=201)
async def save_pantry(value: PantryItem):
    document = value.model_dump(exclude={"id"})
    document["ingredient"] = document["ingredient"].strip().lower()
    await db.pantry.update_one({"ingredient": document["ingredient"]}, {"$set": document}, upsert=True)
    return serialize(await db.pantry.find_one({"ingredient": document["ingredient"]}))


@app.delete("/api/pantry/{name}", status_code=204)
async def delete_pantry(name: str):
    await db.pantry.delete_one({"ingredient": name.lower()})


@app.get("/api/conversions")
async def list_conversions():
    return [serialize(item) async for item in db.conversions.find().sort([("ingredient", 1), ("from_unit", 1)])]


@app.post("/api/conversions", status_code=201)
async def save_conversion(value: Conversion):
    document = value.model_dump()
    document["ingredient"] = document["ingredient"].strip().lower()
    key = {key: document[key] for key in ("ingredient", "from_unit", "to_unit")}
    await db.conversions.update_one(key, {"$set": document}, upsert=True)
    return serialize(await db.conversions.find_one(key))


async def convert(name: str, amount: float, source: str, target: str):
    if source == target:
        return amount
    row = await db.conversions.find_one({"ingredient": name, "from_unit": source, "to_unit": target})
    if row:
        return amount * row["factor"]
    row = await db.conversions.find_one({"ingredient": name, "from_unit": target, "to_unit": source})
    return amount / row["factor"] if row else None


async def recipe_needs(recipe: dict, servings: int):
    needs: dict[str, dict[str, Any]] = {}
    for group in recipe.get("groups", []):
        for ingredient in group.get("ingredients", []):
            if ingredient.get("optional"):
                continue
            name = ingredient["name"].strip().lower()
            stock = await db.pantry.find_one({"ingredient": name})
            target_unit = stock["unit"] if stock else ingredient["unit"]
            quantity = await convert(name, ingredient["quantity"] * servings / recipe["base_servings"], ingredient["unit"], target_unit)
            if quantity is None:
                needs.setdefault(name, {"ingredient": name, "required": 0, "unit": target_unit, "available": stock["quantity"] if stock else 0, "available_unit": target_unit, "reason": f"Add a conversion from {ingredient['unit']} to {target_unit}"})
            else:
                row = needs.setdefault(name, {"ingredient": name, "required": 0, "unit": target_unit, "available": stock["quantity"] if stock else 0, "available_unit": target_unit})
                row["required"] += quantity
    return needs


@app.get("/api/recipes/{recipe_id}/availability")
async def recipe_availability(recipe_id: str, servings: int = 1):
    if not ObjectId.is_valid(recipe_id) or servings < 1:
        raise HTTPException(400, "Provide a valid recipe id and a positive serving count")
    recipe = await db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    needs = await recipe_needs(recipe, servings)
    shortages = [dict(item, required=round(item["required"], 3)) for item in needs.values() if item.get("reason") or item["required"] > item["available"]]
    return {"available": not shortages, "servings": servings, "shortages": shortages}


@app.post("/api/recipes/{recipe_id}/deduct")
async def deduct_pantry(recipe_id: str, value: ScaleRequest):
    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(400, "Invalid recipe id")
    recipe = await db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    needs = await recipe_needs(recipe, value.servings)
    shortages = [dict(item, required=round(item["required"], 3)) for item in needs.values() if item.get("reason") or item["required"] > item["available"]]
    if shortages:
        return {"deducted": False, "shortages": shortages}
    deducted: list[tuple[str, float]] = []
    for name, item in needs.items():
        if item["required"]:
            result = await db.pantry.update_one({"ingredient": name, "quantity": {"$gte": item["required"]}}, {"$inc": {"quantity": -item["required"]}})
            if result.modified_count != 1:
                for deducted_name, quantity in deducted:
                    await db.pantry.update_one({"ingredient": deducted_name}, {"$inc": {"quantity": quantity}})
                current = await db.pantry.find_one({"ingredient": name})
                return {"deducted": False, "shortages": [{"ingredient": name, "required": round(item["required"], 3), "unit": item["unit"], "available": current["quantity"] if current else 0, "available_unit": item["unit"], "reason": "Pantry stock changed; refresh and try again"}]}
            deducted.append((name, item["required"]))
    return {"deducted": True, "servings": value.servings}


@app.get("/api/shopping-list")
async def list_shopping():
    return [serialize(item) async for item in db.shopping.find().sort("ingredient", 1)]


@app.post("/api/shopping-list", status_code=201)
async def add_shopping(value: ShoppingItem):
    document = value.model_dump(exclude={"id"})
    document["ingredient"] = document["ingredient"].strip()
    result = await db.shopping.insert_one(document)
    return serialize(await db.shopping.find_one({"_id": result.inserted_id}))


@app.patch("/api/shopping-list/{item_id}")
async def toggle_shopping(item_id: str):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(400, "Invalid item id")
    query = {"_id": ObjectId(item_id)}
    item = await db.shopping.find_one(query)
    if not item:
        raise HTTPException(404, "Shopping item not found")
    await db.shopping.update_one(query, {"$set": {"checked": not item.get("checked", False)}})
    return serialize(await db.shopping.find_one(query))


@app.delete("/api/shopping-list/{item_id}", status_code=204)
async def remove_shopping(item_id: str):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(400, "Invalid item id")
    await db.shopping.delete_one({"_id": ObjectId(item_id)})
