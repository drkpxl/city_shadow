# Use Node image as base
FROM node:18-slim

# Install Python and pip for the CLI script
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Node dependencies
COPY package*.json ./
RUN npm install --production

# Install Python dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose the port defined by the env file
ENV PORT=3123
EXPOSE $PORT

# Default command
CMD ["npm", "start"]
