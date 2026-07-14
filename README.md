# DocMind AI - Production-Ready Scaffolding

DocMind AI is a production-ready web application built with a modern React 19 frontend and a fast Python-based FastAPI backend.

## Tech Stack

### Frontend
- **React 19**: Modern UI component library.
- **Vite**: Rapid frontend build tool.
- **Tailwind CSS v4**: Utility-first CSS framework (configured with the Vite plugin).
- **Axios**: Promised-based HTTP client for API requests.
- **React Router DOM**: Declarative routing.

### Backend
- **FastAPI**: Modern, high-performance web framework for Python APIs.
- **Uvicorn**: Lightning-fast ASGI server implementation.
- **Python 3.11+**: Core programming language.

---

## Folder Structure

```text
DocMind-AI/
├── frontend/             # Frontend application directory
│   ├── src/              # React source files
│   │   ├── assets/       # Static assets (images, icons)
│   │   ├── components/   # Reusable UI components
│   │   ├── pages/        # Router view pages (e.g., Home.jsx)
│   │   ├── layouts/      # Layout wrapper components
│   │   ├── services/     # Axios API configuration & services
│   │   ├── hooks/        # Custom React hooks
│   │   ├── context/      # React context providers
│   │   ├── styles/       # Tailwind & custom CSS styles
│   │   ├── App.jsx       # Main App router wrapper
│   │   └── main.jsx      # React entry mount script
│   └── package.json      # Frontend package configuration
├── backend/              # Backend application directory
│   ├── app/
│   │   └── main.py       # FastAPI application entrypoint
│   └── requirements.txt  # Python package requirements
├── docs/                 # Documentation folder
├── .gitignore            # Version control ignore configuration
└── README.md             # Project documentation
```

---

## Getting Started

### Prerequisites
- [Node.js](https://nodejs.org/) (v18 or higher recommended)
- [Python](https://www.python.org/) (v3.11 or higher)

### Setup & Running the Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the development server:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
   The backend API will run on [http://localhost:8000](http://localhost:8000).

### Setup & Running the Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The application will run on [http://localhost:5173](http://localhost:5173). Open it in your browser.
