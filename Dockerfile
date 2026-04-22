FROM python:3.11-slim

WORKDIR /app

# Install dependencies before copying code to cache layers
COPY client-email-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . .

# Change to the application directory
WORKDIR /app/client-email-agent

# Expose port (Hugging Face expects port 7860 by default)
EXPOSE 7860

# Run gunicorn on the Hugging Face expected port
CMD ["gunicorn", "API:app", "--bind", "0.0.0.0:7860"]
