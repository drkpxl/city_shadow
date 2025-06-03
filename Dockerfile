# Use the OpenSCAD nightly image based on Debian Bookworm
FROM openscad/openscad:latest

# Install Node.js (version 20)
RUN apt-get update && \
    apt-get install -y ca-certificates curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    NODE_MAJOR=20 && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install nodejs -y

# Install Python and pip
RUN apt-get install -y python3 python3-pip

# Install system dependencies for GeoPandas and related libraries
RUN apt-get update && apt-get install -y gdal-bin libgdal-dev libgeos-dev python3-gdal python3-rtree --no-install-recommends

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Copy requirements.txt
COPY requirements.txt ./

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the application port (default to 3000 if not set in .env)
ARG PORT=3000
ENV PORT=${PORT}
EXPOSE ${PORT}

# Start the application
CMD ["npm", "start"]
