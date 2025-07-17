# Use a slim base image with Python
FROM python:3.13-slim

# Install uv (no need to install pip or virtualenv)
RUN apt-get update && apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH (installed to ~/.cargo/bin)
ENV PATH="/root/.cargo/bin:$PATH"

# Set working dir
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN uv pip install .

# Run the app
CMD ["uv", "run", "python", "-m", "gamebot.main"]
