# Stage 1: build dependencies
FROM node:18-slim AS builder

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Node and Python dependencies
COPY package*.json requirements.txt ./
RUN npm install --production \
    && pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application source
COPY . .

# Stage 2: final image
FROM node:18-slim

# Install Python runtime
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy runtime dependencies from builder
COPY --from=builder /app /app

# Ensure necessary directories exist
RUN mkdir -p uploads outputs

ENV PORT=3123
EXPOSE 3123

CMD ["npm", "start"]
