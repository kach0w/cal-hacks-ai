.PHONY: redis-up redis-down backend frontend demo-seed test

redis-up:
	docker compose up -d redis

redis-down:
	docker compose down

backend:
	cd backend && pip install -r requirements.txt && \
	  uvicorn safestreets.main:app --reload --app-dir src --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm install && npm run dev

demo-seed:
	cd backend && python scripts/seed_demo_intersection.py

test:
	cd backend && pytest -q
