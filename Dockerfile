FROM node:22-bookworm-slim

# Install system dependencies:
# Python, pip, venv, python-dev for building Python packages
# wget, gnupg for adding OpenSCAD repository
# OpenSCAD itself
# GDAL, GEOS, etc., for GeoPandas
# build-essential, gcc, g++ for compiling (will be removed later)
# curl, ca-certificates (general utilities, may be needed by npm or other tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        wget \
        gnupg \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        # python3-gdal python3-rtree # Let's try installing these via pip first within the venv
        build-essential \
        gcc \
        g++ \
        curl \
        ca-certificates && \
    # Install OpenSCAD from OBS repository
    wget -qO- https://files.openscad.org/OBS-Repository-Key.pub | tee /etc/apt/trusted.gpg.d/obs-openscad-nightly.asc && \
    echo "deb https://download.opensuse.org/repositories/home:/t-paul/Debian_12/ ./" | tee /etc/apt/sources.list.d/openscad.list && \
    apt-get update && \
    apt-get install -y openscad --no-install-recommends && \
    # Clean up apt cache
    rm -rf /var/lib/apt/lists/*

# (Further steps will be added here: creating user, venv, pip install, npm install, etc.)
