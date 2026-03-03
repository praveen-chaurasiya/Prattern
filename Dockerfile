FROM python:3.11-slim

# Install Node.js 20
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies (server-only, no GUI packages like customtkinter)
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

# Web frontend build
COPY web/package.json web/package-lock.json* web/
RUN cd web && npm install

COPY web/ web/
RUN cd web && VITE_API_BASE_URL='' npm run build

# Copy backend code
COPY . .

# Fail-fast: verify all imports resolve at build time
RUN python -c "from prattern.api.server import app; print('Server imports OK')"

# Start server
CMD uvicorn prattern.api.server:app --host 0.0.0.0 --port ${PORT:-8000}
