# Use a slim base image with Python
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# Set working dir
WORKDIR /app

# Copy project files
COPY . .

RUN mkdir -p /config


# Install dependencies
RUN uv sync --locked

# Run the app
CMD ["uv", "run", "python", "-m", "gamebot.main"]
