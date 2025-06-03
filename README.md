# TerrainForge3D

Transform GeoJSON map data into 3D printable city models with artistic styling and real-time preview generation.

Manifold on Debian https://lists.openscad.org/empathy/thread/D6KV3ZLXHLBHSITSQ5GPUZUKHURU4ABE

## Features

- **Real-time 3D Preview**: See your city model update live as you adjust parameters
- **Multiple Artistic Styles**: Choose from modern, classic, minimal, or block-combine styles
- **Comprehensive Feature Support**: Buildings, roads, water bodies, parks, bridges, and more
- **STL Export**: Generate print-ready STL files for 3D printing
- **Job Management**: Robust processing with progress tracking and concurrent request handling
- **Live Progress Updates**: Real-time console output and progress percentage via WebSockets

## Architecture

TerrainForge3D uses a modern web-based architecture:

- **Frontend**: Express.js server with EJS templates and Socket.io for real-time updates
- **Backend**: Python-based 3D generation engine with modular feature processors
- **Job Queue**: UUID-based job tracking with process isolation and timeout protection
- **File Management**: Organized temporary file structure with automatic cleanup

### Job Management System

The application uses a sophisticated job management system that provides:

- **UUID Tracking**: Each conversion job gets a unique identifier
- **Process Isolation**: Maximum concurrent process limits prevent system overload
- **Real-time Updates**: Socket.io broadcasts progress and console output
- **Structured Storage**: Jobs are organized in `/temp/{username}/{jobId}/` directories
- **Comprehensive Logging**: All output is logged to files for debugging
- **Automatic Cleanup**: Old jobs are removed after 24 hours

## Installation

### Prerequisites

- Python 3.8+
- Node.js 14+
- OpenSCAD (for preview and STL generation)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/TerrainForge3D.git
cd TerrainForge3D
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Install Node.js dependencies:

```bash
npm install
```

4. Start the server:

```bash
npm start
```

5. Open your browser to `http://localhost:3000`

## Usage

1. **Upload GeoJSON**: Use the web interface to upload your GeoJSON file
2. **Configure Parameters**:
   - **Size**: Model dimensions in millimeters
   - **Height**: Maximum building height
   - **Style**: Choose artistic style (modern, classic, minimal, block-combine)
   - **Detail Level**: Control model complexity (0-2)
   - **Other Options**: Road width, water depth, bridge settings, etc.
3. **Preview**: Watch the live preview update as you change settings
4. **Generate**: Click "Render Final Model" to create STL files
5. **Download**: Download the generated SCAD and STL files

## API Endpoints

- `POST /uploadFile` - Upload GeoJSON file
- `POST /preview` - Generate preview with current settings
- `POST /render` - Generate final STL files
- `GET /job/:jobId` - Check job status

## WebSocket Events

The server emits the following Socket.io events:

- `job-output` - Real-time console output from the conversion process
- `job-progress` - Progress percentage updates
- `job-completed` - Job completion notification
- `job-failed` - Job failure notification

## Configuration Options

### Basic Options

- `size` - Model size in mm (default: 200)
- `height` - Maximum height in mm (default: 20)
- `style` - Artistic style: modern, classic, minimal, block-combine
- `detail` - Detail level 0-2 (default: 1.0)

### Building Options

- `merge-distance` - Distance threshold for merging buildings
- `cluster-size` - Size threshold for building clusters
- `height-variance` - Height variation 0-1
- `min-building-area` - Minimum building area in m²

### Infrastructure Options

- `road-width` - Road width in mm
- `water-depth` - Water depth in mm
- `bridge-height` - Bridge deck height above base
- `bridge-thickness` - Bridge deck thickness
- `support-width` - Bridge support radius

### Preprocessing Options

- `preprocess` - Enable preprocessing
- `crop-distance` - Crop distance in meters
- `crop-bbox` - Bounding box for cropping

## Development

### Project Structure

```
TerrainForge3D/
├── server.js              # Express server with Socket.io
├── geojson_to_shadow_city.py  # Main Python converter
├── lib/
│   ├── jobManager.js      # Job management system
│   ├── processManager.js  # Process isolation and queue
│   ├── converter.py       # Core conversion logic
│   ├── preprocessor.py    # GeoJSON preprocessing
│   ├── feature_processor/ # Feature-specific processors
│   ├── style/            # Artistic styling system
│   └── preview/          # OpenSCAD integration
├── views/
│   └── index.ejs         # Web interface
├── public/
│   └── css/
│       └── style.css     # Styling
└── temp/                 # Temporary job files
```

### Adding New Features

To add support for new GeoJSON features:

1. Create a new processor in `lib/feature_processor/`
2. Inherit from `BaseFeatureProcessor`
3. Implement the `process()` method
4. Register in `feature_processor.py`

### Testing

Run the test suite:

```bash
node test-job-system.js
```

## Docker Deployment

The project includes a Docker setup for running the service and a Redis instance.
To build and run everything with Docker:

```bash
docker-compose up -d --build
```

Volume permissions can be corrected by running:

```bash
docker compose exec app /app/scripts/fix-permissions.sh
```

The Redis service listens on the port specified by `REDIS_PORT` in the `.env`
file. The Node.js application will use the `REDIS_URL` variable defined there.

The Dockerfile installs OpenSCAD via apt which provides the `Manifold` backend
needed for fast STL generation. Verify that the installed version is 2021.01 or
newer when deploying on your own base image.

## Future Enhancements

- [ ] Authentication system for user management
- [ ] OSM data caching for faster processing
- [ ] 3MF export with color information
- [ ] Docker support for easy deployment
- [ ] Individual roof style selection
- [ ] Map-based bounding box selection

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
