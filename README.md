# Recipe Scaler & Pantry Inventory

A full stack kitchen app for scaling recipes, tracking pantry stock, converting ingredient units, and keeping a shopping list in sync with what you have.

## Features

- **Nested recipes:** ingredient groups, optional ingredients, ordered instructions, time, servings, and tags are stored in MongoDB documents.
- **Recipe scaling:** change serving count and ingredient amounts recalculate from the recipe's base serving count.
- **Pantry inventory:** track quantities, units, categories, and low stock alerts.
- **Ingredient conversions:** define ingredient-specific relationships (for example, 1 tbsp olive oil = 15 ml) used when comparing recipes with pantry stock.
- **Cook action:** checks all required ingredients, reports shortages, and deducts pantry stock when enough is available.
- **Shopping list:** add shortages, add items directly, check off purchased items, and remove items.
- **Demo data:** first startup seeds three recipes, pantry staples, and sample conversion rules into an empty database.
- **API docs:** interactive OpenAPI docs at `/docs`.

## Quick start with Docker

Requirements: Docker Desktop with Compose.

```bash
docker compose up --build
```

Open the app at [http://localhost:5173](http://localhost:5173) and API docs at [http://localhost:8000/docs](http://localhost:8000/docs). The first start may take a little while as the frontend dependencies are installed and demo data is seeded.

Stop services with `Ctrl+C`. To stop and remove the local database volume too, run `docker compose down -v`.

## Run without Docker

Requirements: Python 3.11+, Node.js 20+, npm, and MongoDB 7+.

1. Copy `.env.example` to `.env` and set `MONGODB_URL` if MongoDB is not on the default local address.
2. In a terminal:

   ```bash
   cd backend
   python -m venv .venv
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. In another terminal:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. Open [http://localhost:5173](http://localhost:5173).

Set `VITE_API_URL` if the API is hosted somewhere other than `http://localhost:8000/api`.

## Project layout

```text
backend/
  app/
    main.py       FastAPI routes, MongoDB setup, seed data, scaling and stock logic
    models.py     Pydantic request models and validation
frontend/
  src/
    main.tsx      React app and API-connected screens
    style.css     Responsive kitchen dashboard styling
```

## Main API routes

| Method | Route | Use |
| --- | --- | --- |
| GET / POST | `/api/recipes` | List or add nested recipes |
| GET / PUT / DELETE | `/api/recipes/{id}` | Read, update, or remove a recipe |
| POST | `/api/recipes/{id}/scale` | Return serving-adjusted quantities |
| GET | `/api/recipes/{id}/availability?servings=4` | Compare scaled requirements with pantry stock |
| POST | `/api/recipes/{id}/deduct` | Check and deduct stock for a serving count |
| GET / POST / DELETE | `/api/pantry` | List, upsert, or remove pantry items |
| GET / POST | `/api/conversions` | List or upsert ingredient-specific unit conversions |
| GET / POST | `/api/shopping-list` | List or add shopping items |
| PATCH / DELETE | `/api/shopping-list/{id}` | Check off or remove a shopping item |

## MongoDB collections

- `recipes`: one document per recipe, with nested `groups[].ingredients[]` and `instructions[]`.
- `pantry`: one record per normalized ingredient name.
- `conversions`: conversion factor per ingredient and ordered unit pair. Reverse conversion is calculated automatically.
- `shopping`: individual shopping list rows.

Ingredient units are deliberately ingredient-specific: volume-to-mass conversions depend on the ingredient. Add only conversion factors that make sense for the food and units you use.

## Configuration

See `.env.example`. `MONGODB_DATABASE`, `MONGODB_URL`, and `CORS_ORIGINS` configure the API. `VITE_API_URL` configures the frontend API base URL. Demo data is inserted only when the corresponding recipes or pantry collection is empty.

## License

MIT. See [LICENSE](LICENSE).
