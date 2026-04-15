# KPI Selector Full Stack

A full-stack KPI Selector app with:
- **React + Vite frontend** for a polished, professional UI
- **FastAPI backend** for workflow logic, data loading, role recommendation, and optional LLM integration
- **Data folder** containing the uploaded master workbook, generated KPI JSON, and a schema file

## Features

- Step-based workflow with progress tracking
- Office Level -> Vertical -> Daily Work -> Recommended Roles -> Secondary Roles -> Summary
- Open-text daily-work input in a chat-like composer
- Role recommendations based on KPI similarity to the daily-work text
- Optional LLM-powered recommendation pipeline with deterministic fallback
- BA-specific secondary-role flow with re-selectable vertical
- CSV export of the final summary
- Professional, responsive frontend UI

## Repo structure

```
kpi-selector-fullstack/
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── data_loader.py
│   │   ├── llm_service.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── recommendation_service.py
│   │   └── search_service.py
│   ├── scripts/
│   │   └── convert_excel.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── data/
    ├── master_data.xlsx
    ├── kpi_data.json
    └── master_data_schema.json
```

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate       # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:8000` for the API.

## Optional LLM setup

The recommender works in two modes:

1. **LLM mode** if you configure a provider and key
2. **Fallback mode** using KPI similarity scoring if no key is configured

Supported providers:
- `openai`
- `groq`
- `ollama`

Set these in `backend/.env`.

## Notes

- `data/kpi_data.json` is already generated from the uploaded workbook.
- If you replace the workbook, rerun:

```bash
python backend/scripts/convert_excel.py
```

