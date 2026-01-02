# Comercial Comarapa - Backend API

REST API for inventory management system built with FastAPI and PostgreSQL.

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- [Hatch](https://hatch.pypa.io/) package manager
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for local development)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ticlla/Backend-ComercialComarapa.git
   cd Backend-ComercialComarapa
   ```

2. **Install Hatch** (if not already installed)
   ```bash
   pip install hatch
   ```

3. **Start Docker containers** (PostgreSQL + pgAdmin)
   ```bash
   docker-compose up -d
   ```

4. **Run the development server**
   ```bash
   hatch run dev:start
   ```

5. **Open API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - pgAdmin: http://localhost:5050 (admin@comercialcomarapa.com / admin)

## 📁 Project Structure

```
Backend-ComercialComarapa/
├── pyproject.toml              # Hatch configuration & dependencies
├── docker-compose.yml          # Local PostgreSQL + pgAdmin
├── README.md                   # This file
│
├── .env.development            # Development config (Docker)
├── .env.staging                # Staging config (Supabase)
├── .env.production             # Production config (Supabase)
├── .env.example                # Template reference
│
├── src/
│   └── comercial_comarapa/     # Main package
│       ├── main.py             # FastAPI application
│       ├── config.py           # Settings (pydantic-settings)
│       ├── api/v1/             # API routers
│       ├── models/             # Pydantic schemas
│       ├── services/           # Business logic
│       ├── db/                 # Database layer
│       │   ├── database.py     # Dual-mode client (local/Supabase)
│       │   └── supabase.py     # Supabase client
│       └── core/               # Utilities
│
├── tests/                      # Test suite
└── Documentation/              # Project documentation
```

## 🛠️ Development Commands

### Environment-Specific Commands

| Command | Environment | Description |
|---------|-------------|-------------|
| `hatch run dev:start` | Development | Local Docker PostgreSQL (hot-reload) |
| `hatch run stage:start` | Staging | Supabase staging project |
| `hatch run prod:start` | Production | Supabase production (4 workers) |

### Shared Tools

| Command | Description |
|---------|-------------|
| `hatch run lint` | Run Ruff linter |
| `hatch run format` | Format code with Ruff |
| `hatch run fix` | Auto-fix linting issues |
| `hatch run test` | Run test suite |
| `hatch run test-cov` | Run tests with coverage report |
| `hatch shell` | Activate virtual environment |

### Docker Commands

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start PostgreSQL + pgAdmin |
| `docker-compose down` | Stop containers |
| `docker-compose logs -f db` | View database logs |

## 🔧 Configuration

Configuration is managed via environment files. Each Hatch environment loads its corresponding `.env.*` file.

### Environment Files

| File | Purpose | DATABASE_MODE |
|------|---------|---------------|
| `.env.development` | Local Docker PostgreSQL | `local` |
| `.env.staging` | Supabase staging project | `supabase` |
| `.env.production` | Supabase production | `supabase` |
| `.env.*.local` | Personal overrides (git-ignored) | - |

### Key Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_MODE` | Database backend | `local` or `supabase` |
| `DATABASE_URL` | PostgreSQL connection (local mode) | `postgresql://...` |
| `SUPABASE_URL` | Supabase project URL (supabase mode) | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key (supabase mode) | `eyJ...` |
| `APP_ENV` | Environment name | `development` |
| `DEBUG` | Enable debug mode | `true` / `false` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

## 📚 API Endpoints

### Health & Info

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API information |
| `GET` | `/health` | Health check with DB status |

### Products (Phase 1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/products` | List products |
| `GET` | `/api/v1/products/{id}` | Get product |
| `POST` | `/api/v1/products` | Create product |
| `PUT` | `/api/v1/products/{id}` | Update product |
| `DELETE` | `/api/v1/products/{id}` | Delete product |

*See `/docs` for complete API documentation.*

## 🗄️ Database Setup

### Local Development (Docker)

```bash
# Start containers
docker-compose up -d

# Verify database is running
docker-compose ps

# Access pgAdmin at http://localhost:5050
# Email: admin@comercialcomarapa.com
# Password: admin
```

### Supabase (Staging/Production)

1. Create a Supabase project at https://supabase.com
2. Run the schema from `Documentation/database/schema.sql` in SQL Editor
3. Copy API keys from Project Settings > API
4. Update `.env.staging` or `.env.production`

## 🧪 Testing

```bash
# Run all tests
hatch run test

# Run with coverage
hatch run test-cov
```

## 📋 Code Quality

Before committing, always run:

```bash
# Check linting
hatch run lint

# Format code
hatch run format
```

## 📄 License

MIT License - see LICENSE file for details.

## 👥 Contributing

1. Fork the repository
2. Create a feature branch
3. Run `hatch run lint` before committing
4. Submit a pull request

