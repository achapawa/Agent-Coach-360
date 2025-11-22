# ============================================
# 1. Base image
# ============================================
FROM python:3.11-slim

# Avoid Python writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ============================================
# 2. Set working directory
# ============================================
WORKDIR /app

# ============================================
# 3. Copy dependencies first (better caching)
# ============================================
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ============================================
# 4. Copy entire project
# ============================================
COPY . /app

# ============================================
# 5. Expose port (Cloud Run uses $PORT)
# ============================================
ENV PORT=8080

# ============================================
# 6. Start FastAPI server via Uvicorn
# ============================================
CMD ["uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "8080"]
