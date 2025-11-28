## Dev Quickstart (local, no Docker yet)

### Backend (FastAPI)
1. cd services/backend
2. python -m pip install --upgrade pip
3. pip install -r requirements.txt
4. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
5. Check http://localhost:8000/health

### Frontend (React + Vite)
1. cd services/frontend
2. npm install
3. npm run dev
4. Open http://localhost:3000

### Upload test
- Use the frontend page to upload a jpg/png/pdf/docx.
- Uploaded files are saved in `services/backend/uploads`.
