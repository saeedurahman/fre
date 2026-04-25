# Grocery Distribution Backend

Production-oriented FastAPI backend for a grocery distribution mobile app where retailers place orders directly without salesperson visits.

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy (async)
- Alembic
- Pydantic v2
- JWT (admin/client roles)
- Cloudinary
- bcrypt (passlib)

## Project Structure

```text
app/
├── main.py
├── database.py
├── core/
├── auth/
├── clients/
├── products/
├── orders/
└── admin/
```

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and update values.
4. Ensure PostgreSQL is running and database exists.
5. Run migrations:
   - `python -m alembic upgrade head`
6. Start API server:
   - `uvicorn app.main:app --reload`

## Migrations

- Create migration:
  - `python -m alembic revision --autogenerate -m "message"`
- Apply migrations:
  - `python -m alembic upgrade head`
- Rollback one migration:
  - `python -m alembic downgrade -1`

## Environment Variables

- `DATABASE_URL`: async SQLAlchemy PostgreSQL URL.
- `JWT_SECRET`: JWT signing secret.
- `JWT_ALGORITHM`: JWT algorithm (e.g. `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: access token expiry in minutes.
- `ALLOWED_ORIGINS`: comma-separated CORS origins.
- `CLOUDINARY_CLOUD_NAME`: Cloudinary cloud name.
- `CLOUDINARY_API_KEY`: Cloudinary API key.
- `CLOUDINARY_API_SECRET`: Cloudinary API secret.

## API Endpoints

### Health / Summary

- `GET /health`
- `GET /api/v1/health`
- `GET /api/v1/`

### Auth

- `POST /api/v1/auth/admin/login`
- `POST /api/v1/auth/client/login`

### Products

- `POST /api/v1/admin/products`
- `GET /api/v1/admin/products`
- `GET /api/v1/admin/products/{product_id}`
- `PATCH /api/v1/admin/products/{product_id}`
- `DELETE /api/v1/admin/products/{product_id}`
- `GET /api/v1/products`
- `GET /api/v1/products/{product_id}`

### Clients / Locations

- `POST /api/v1/admin/clients`
- `GET /api/v1/admin/clients`
- `GET /api/v1/admin/clients/{client_id}`
- `PATCH /api/v1/admin/clients/{client_id}`
- `POST /api/v1/admin/clients/{client_id}/locations`
- `PATCH /api/v1/admin/clients/{client_id}/locations/{location_id}`
- `DELETE /api/v1/admin/clients/{client_id}/locations/{location_id}`
- `GET /api/v1/me`
- `GET /api/v1/me/locations`

### Orders

- `POST /api/v1/orders`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `GET /api/v1/admin/orders`
- `GET /api/v1/admin/orders/{order_id}`
- `PATCH /api/v1/admin/orders/{order_id}/status`
