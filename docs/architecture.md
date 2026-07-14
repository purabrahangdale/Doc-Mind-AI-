# DocMind AI Architecture Documentation

This directory contains design and architecture documents for DocMind AI.

## Project Structure Overview

The project is split into:
1. `frontend/` - React SPA powered by Vite and Tailwind CSS.
2. `backend/` - FastAPI ASGI application.

## Development Workflows

- Frontend and backend run concurrently in development.
- CORS is enabled on the backend to allow requests from the frontend origin `http://localhost:5173`.
