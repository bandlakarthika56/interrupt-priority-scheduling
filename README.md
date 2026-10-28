# Intelligent Interrupt Management and Priority Scheduling System

A Streamlit educational simulator for interrupt requests, non-preemptive priority scheduling, FCFS comparison, execution history, timeline visualization, and AI-assisted explanation.

## Files
- `interrupt_priority_scheduling_simulator.ipynb` — Google Colab development notebook
- `app.py` — Streamlit web app
- `requirements.txt` — dependencies
- `README.md` — setup and deployment instructions

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Optional Gemini AI explanation
Set `GEMINI_API_KEY` as an environment variable to enable Gemini-generated analysis. Without a key, the app still runs and provides a built-in explanation. Never commit an API key to GitHub.

## Render deployment
Build command: `pip install -r requirements.txt`

Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

If enabling Gemini, add `GEMINI_API_KEY` under Render Environment settings.

## Assumptions
This is an educational simulation, not a real hardware controller. It uses non-preemptive scheduling and treats all displayed requests as pending at time zero. Execution times are arbitrary simulation units. Priority ties are resolved by arrival order.
