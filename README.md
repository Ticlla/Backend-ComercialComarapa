# Comercial Comarapa - Backend API

REST API for inventory management system built with FastAPI and Supabase.

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- [Hatch](https://hatch.pypa.io/) package manager
- [Supabase](https://supabase.com/) account and project

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/comercialcomarapa/backend-cc.git
   cd backend-cc
   ```

2. **Install Hatch** (if not already installed)
   ```bash
   pip install hatch
   ```

3. **Create environment and install dependencies**
   ```bash
   hatch env create
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env with your Supabase credentials
   # Get these from: https://supabase.com/dashboard/project/_/settings/api
   ```

5. **Run the development server**
   ```bash
   hatch run dev
   ```

6. **Open API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📁 Project Structure

```
BackEnd-CC/
├── pyproject.toml              # Hatch configuration & dependencies
├── README.md                   # This file
├── .env.example                # Environment template
│
├── src/
│   └── comercial_comarapa/     # Main package
│       ├── main.py             # FastAPI application
│       ├── config.py           # Settings (pydantic-settings)
│       ├── api/v1/             # API routers
│       ├── models/             # Pydantic schemas
│       ├── services/           # Business logic
│       ├── db/                 # Database layer
│       └── core/               # Utilities
│
├── tests/                      # Test suite
└── Documentation/              # Project documentation
```

## 🛠️ Development Commands

| Command | Description |
|---------|-------------|
| `hatch run dev` | Start development server with auto-reload |
| `hatch run start` | Start production server |
| `hatch run lint` | Run Ruff linter |
| `hatch run format` | Format code with Ruff |
| `hatch run fix` | Auto-fix linting issues |
| `hatch run test` | Run test suite |
| `hatch run test-cov` | Run tests with coverage report |
| `hatch shell` | Activate virtual environment |

## 🔧 Configuration

All configuration is done via environment variables. See `.env.example` for available options.

### Required Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Supabase anonymous key |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment name |
| `DEBUG` | `true` | Enable debug mode |
| `PORT` | `8000` | Server port |
| `CORS_ORIGINS` | `localhost:3000,5173` | Allowed CORS origins |

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

1. Create a new Supabase project
2. Run the schema from `Documentation/database/schema.sql`
3. Get your API keys from project settings

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

