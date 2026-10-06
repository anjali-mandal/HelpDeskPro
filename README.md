# HelpDeskPro

Internal IT support and incident management platform.

## Local development

Start the API:

```powershell
cd backend
uvicorn app.main:app --reload --port 8010
```

Start the frontend in another terminal:

```powershell
cd frontend
npm run dev
```

The API uses the in-process SLA monitor by default. Redis is optional. If Redis is running, enable the Celery scheduler in the backend terminal before starting the API:

```powershell
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
celery -A app.celery_app worker --beat --pool=solo --loglevel=info
```

When `REDIS_URL` is set, the API does not start a second SLA monitor. Run the API in a separate terminal with the same environment variable.

## AI suggestions

Without a key, `/ai/suggest` uses the built-in rule engine. For Gemini suggestions, set:

```powershell
$env:GEMINI_API_KEY = "your-key"
$env:GEMINI_MODEL = "gemini-3.7-flash"
```

The AI only suggests category, priority, and troubleshooting steps. Engineers retain final control.

Demo accounts are seeded on an empty database:

| Role | Email | Password |
| --- | --- | --- |
| Employee | employee@helpdeskpro.com | employee123 |
| Engineer | engineer@helpdeskpro.com | engineer123 |
| Manager | manager@helpdeskpro.com | manager123 |
| Admin | admin@helpdeskpro.com | admin123 |