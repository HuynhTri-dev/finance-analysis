# Finance Analysis Runbook

This runbook provides step-by-step instructions to set up, configure, and run the Finance Analysis application locally. The system consists of a Python FastAPI backend and a Next.js (React) frontend.

## 1. System Requirements
- **Python**: v3.10 or newer (for the backend).
- **Node.js**: v18.x or newer (for the frontend).
- **Package Managers**: `pip` (Python) and `npm` (Node.js).
- **Database**: PostgreSQL (hosted on Neon.tech, as configured in the `.env` file).

## 2. Environment Configuration

### Backend Environment
Create a `.env` file in the `backend/` directory or at the root of the project (ensure your backend reads from the correct location) with the following environment variables:
```env
# API Keys for third-party integrations
VNSTOCK_API_KEY="your_vnstock_api_key_here"

# PostgreSQL — Neon Serverless (Example)
# NOTE: Alembic migrations must use the UNPOOLED URL
DATABASE_URL="postgresql+asyncpg://<user>:<password>@<host>/<dbname>?ssl=require"
DATABASE_URL_UNPOOLED="postgresql+asyncpg://<user>:<password>@<host_unpooled>/<dbname>?ssl=require"
ALEMBIC_DATABASE_URL="postgresql+psycopg2://<user>:<password>@<host_unpooled>/<dbname>?sslmode=require"
```

### Frontend Environment
If needed, create a `.env.local` file in the `frontend/` directory:
```env
NEXT_PUBLIC_API_URL="http://localhost:8001/api"
```

## 3. Backend Setup & Execution

The backend is built with FastAPI and relies on `vnstock` for market data and SQLAlchemy/Alembic for database interactions.

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```
2. **Set up the virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or .venv\Scripts\activate on Windows
   ```
3. **Install dependencies:**
   ```bash
   pip install -U pip
   pip install -r requirements.txt
   ```
   *Note: If you plan to upgrade to the latest vnstock, you can also run `pip install vnstock3 --upgrade`.*

4. **Run Database Migrations (Optional but recommended):**
   ```bash
   alembic upgrade head
   ```

5. **Start the FastAPI Server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```
   The backend will be available at: `http://localhost:8001`
   Swagger UI Documentation: `http://localhost:8001/docs`

## 4. Frontend Setup & Execution

The frontend is a React application powered by Next.js and styled with Tailwind CSS.

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```
2. **Install dependencies:**
   ```bash
   npm install
   ```
3. **Start the Next.js Development Server:**
   ```bash
   npm run dev
   ```
   The frontend will be available at: `http://localhost:3000`

## 5. Known Issues & Troubleshooting

### Frontend Stuck on "Đang tải dữ liệu..." (Loading Data...)
- **Symptom:** The UI hangs indefinitely during the initial data fetch.
- **Cause:** This usually occurs if the FastAPI backend is blocking the main event loop. For instance, if an endpoint is defined with `async def` but calls a slow, synchronous function (like `market_service.get_market_overview()`), it will freeze the server.
- **Fix:** Ensure that any FastAPI router endpoints calling synchronous blocking code are defined with standard `def` (instead of `async def`). This delegates the blocking execution to FastAPI's background thread pool.

### `UnboundLocalError` or `Unexpected keyword argument 'group'` in vnstock
- **Symptom:** API endpoints fetching market data fail or return nulls.
- **Cause:** The project may be using an older legacy version of `vnstock` (e.g., v0.2.x). In these older versions, certain arguments like `group="HOSE"` in `market_top_mover()` are unsupported, and temporary network blocking by data sources (like TCBS/Cloudflare) can cause exceptions to trigger before variables are assigned.
- **Fix:** Avoid passing the `group` keyword if using the legacy version, or upgrade the environment to `vnstock>=4.0.6` (or `vnstock3`) to align with newer data scraping strategies.

### Missing Module Errors (`aiohttp`, `fpdf2`, etc.)
- **Symptom:** Starting the backend or triggering specific endpoints yields `ModuleNotFoundError`.
- **Fix:** Ensure you are activating your virtual environment (`source .venv/bin/activate`) before running the backend. If the module is still missing, manually install it via `pip install <module_name>` and update `requirements.txt`.
