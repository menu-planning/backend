# Use a standard Python image that includes common build tools
FROM python:3.12-alpine

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install uv using pip
RUN pip install uv

# Copy only the dependency files first to leverage Docker's layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv pip sync pyproject.toml --no-cache --system

# Now copy all your application code and configuration files
COPY alembic.ini railway.json ./
COPY migrations/ ./migrations/
COPY src/ ./src/

# The startCommand from your railway.json will be used by Railway to run the app.
# No CMD is needed if you keep the startCommand in railway.json.