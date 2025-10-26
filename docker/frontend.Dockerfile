FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy application files
COPY frontend/ .

ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV development

EXPOSE 3000

CMD ["npm", "run", "dev"]
