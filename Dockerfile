# InsightBoard - Business Analytics Dashboard SaaS

A production-grade business analytics dashboard platform with customizable widgets, real-time data connectors, report generation, scheduled reports, team sharing, and rich data visualizations including charts, graphs, maps, and tables.

## Architecture

- **Backend**: Django 5.x + Django REST Framework
- **Frontend**: React 18 + Redux Toolkit + Recharts/D3.js
- **Database**: PostgreSQL 16
- **Cache / Message Broker**: Redis 7
- **Task Queue**: Celery 5.x with Redis broker
- **Reverse Proxy**: Nginx
- **Containerization**: Docker + Docker Compose

## Features

- **Customizable Dashboards**: Drag-and-drop widget grid with resizable panels
- **Data Connectors**: PostgreSQL, MySQL, REST API, CSV/Excel upload, Google Sheets
- **Widget Library**: Line charts, bar charts, pie charts, metric cards, data tables, geographic maps
- **Visual Query Builder**: Build data queries without writing SQL
- **Report Generation**: Export dashboards and widgets to PDF and Excel
- **Scheduled Reports**: Cron-based automatic report delivery via email
- **Metric Alerts**: Threshold and anomaly-based alerting with email/webhook notifications
- **Team Collaboration**: Organization and team-based sharing with role permissions
- **Real-time Updates**: WebSocket-powered live metric streaming
- **Multi-tenancy**: Organization-scoped data isolation

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Setup

1. Clone the repository:

```bash
git clone https://github.com/your-org/insightboard.git
cd insightboard
```

2. Copy the environment file and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

3. Build and start all services:

```bash
docker compose up --build -d
```

4. Run database migrations:

```bash
docker compose exec backend python manage.py migrate
```

5. Create a superuser:

```bash
docker compose exec backend python manage.py createsuperuser
```

6. Access the application:

- Frontend: http://localhost
- Backend API: http://localhost/api/
- Admin Panel: http://localhost/admin/
- API Docs: http://localhost/api/docs/

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Running Celery Workers

```bash
cd backend
celery -A config worker -l info
celery -A config beat -l info
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/auth/register/` | POST | User registration |
| `/api/v1/auth/login/` | POST | JWT login |
| `/api/v1/auth/refresh/` | POST | Refresh JWT token |
| `/api/v1/dashboards/` | GET, POST | List/create dashboards |
| `/api/v1/dashboards/:id/` | GET, PUT, DELETE | Dashboard detail |
| `/api/v1/dashboards/:id/widgets/` | GET, POST | Dashboard widgets |
| `/api/v1/datasources/` | GET, POST | Data sources |
| `/api/v1/datasources/:id/query/` | POST | Execute query |
| `/api/v1/visualizations/` | GET, POST | Visualizations |
| `/api/v1/reports/` | GET, POST | Reports |
| `/api/v1/reports/:id/export/` | POST | Export report |
| `/api/v1/alerts/` | GET, POST | Metric alerts |

## Project Structure

```
insightboard/
  backend/
    config/           # Django project settings
    apps/
      accounts/       # User, Organization, Team models
      dashboards/     # Dashboard, Widget, Layout models
      datasources/    # DataSource, Connection, Query models
      visualizations/ # Chart configs and visualization models
      reports/        # Report generation and scheduling
      alerts/         # Metric alerting system
    utils/            # Shared utilities
  frontend/
    src/
      api/            # API client modules
      components/     # React components
      pages/          # Page-level components
      store/          # Redux store and slices
      hooks/          # Custom React hooks
      styles/         # Global styles
  nginx/              # Nginx configuration
```

## Environment Variables

See `.env.example` for the complete list of environment variables.

## Testing

```bash
# Backend tests
docker compose exec backend python manage.py test

# Frontend tests
docker compose exec frontend npm test
```

## License

MIT License. See LICENSE for details.
