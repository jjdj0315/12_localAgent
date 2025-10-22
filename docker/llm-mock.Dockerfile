FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY llm-service/requirements-mock.txt .
RUN pip install --no-cache-dir -r requirements-mock.txt

# Copy mock server
COPY llm-service/mock_server.py .

EXPOSE 8001

CMD ["python", "mock_server.py"]
