const express = require("express");
const multer = require("multer");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const { v4: uuidv4 } = require("uuid");

const app = express();
const port = process.env.PORT || 3000;

// Set view engine to EJS
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

// Serve static files from public and output directories
app.use(express.static(path.join(__dirname, "public")));
app.use("/uploads", express.static("uploads"));
app.use("/outputs", express.static("outputs"));

// Ensure uploads and outputs directories exist
const uploadsDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}
const outputsDir = path.join(__dirname, "outputs");
if (!fs.existsSync(outputsDir)) {
  fs.mkdirSync(outputsDir);
}

// Setup Multer for file uploads
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, "uploads/");
  },
  filename: function (req, file, cb) {
    // Generate a unique filename to avoid collisions
    const uniqueSuffix = Date.now() + "-" + uuidv4();
    cb(null, uniqueSuffix + "-" + file.originalname);
  },
});
const upload = multer({ storage: storage });

// GET home page – upload form
app.get("/", (req, res) => {
  res.render("index");
});

// POST /upload – handle file upload and invoke the Python tool
app.post("/upload", upload.single("geojson"), (req, res) => {
  if (!req.file) {
    return res.status(400).send("No file uploaded.");
  }

  // Generate a unique output base name (without extension)
  const outputBase = "output-" + Date.now();
  const outputPath = path.join(outputsDir, outputBase + ".scad");

  // Build arguments for the Python tool:
  // Basic required arguments: input and output file.
  const args = [
    path.join(__dirname, "geojson_to_shadow_city.py"),
    path.join(__dirname, req.file.path),
    outputPath,
  ];

  // Basic options
  if (req.body.size) args.push("--size", req.body.size);
  if (req.body.height) args.push("--height", req.body.height);
  if (req.body.style) args.push("--style", req.body.style);
  if (req.body.detail) args.push("--detail", req.body.detail);
  if (req.body["merge-distance"])
    args.push("--merge-distance", req.body["merge-distance"]);
  if (req.body["cluster-size"])
    args.push("--cluster-size", req.body["cluster-size"]);
  if (req.body["height-variance"])
    args.push("--height-variance", req.body["height-variance"]);
  if (req.body["road-width"]) args.push("--road-width", req.body["road-width"]);
  if (req.body["water-depth"])
    args.push("--water-depth", req.body["water-depth"]);
  if (req.body["min-building-area"])
    args.push("--min-building-area", req.body["min-building-area"]);
  if (req.body.debug === "on") args.push("--debug");

  // Preprocessing options
  if (req.body.preprocess === "on") args.push("--preprocess");
  if (req.body["crop-distance"])
    args.push("--crop-distance", req.body["crop-distance"]);
  // Expecting four separate fields for crop bbox
  if (
    req.body.crop_bbox1 &&
    req.body.crop_bbox2 &&
    req.body.crop_bbox3 &&
    req.body.crop_bbox4
  ) {
    args.push(
      "--crop-bbox",
      req.body.crop_bbox1,
      req.body.crop_bbox2,
      req.body.crop_bbox3,
      req.body.crop_bbox4
    );
  }

  // Export options
  if (req.body.export) args.push("--export", req.body.export);
  if (req.body["output-stl"]) args.push("--output-stl", req.body["output-stl"]);
  if (req.body["no-repair"] === "on") args.push("--no-repair");
  if (req.body.force === "on") args.push("--force");

  // Preview and Integration options
  if (req.body["preview-size-width"] && req.body["preview-size-height"]) {
    args.push(
      "--preview-size",
      req.body["preview-size-width"],
      req.body["preview-size-height"]
    );
  }
  if (req.body["preview-file"])
    args.push("--preview-file", req.body["preview-file"]);
  if (req.body.watch === "on") args.push("--watch");
  if (req.body["openscad-path"])
    args.push("--openscad-path", req.body["openscad-path"]);

  // Log the arguments for debugging
  console.log("Running Python command with args:", args.join(" "));

  // Spawn the Python process
  const pythonProcess = spawn("python3", args);

  let stdoutData = "";
  let stderrData = "";

  pythonProcess.stdout.on("data", (data) => {
    stdoutData += data.toString();
  });

  pythonProcess.stderr.on("data", (data) => {
    stderrData += data.toString();
  });

  pythonProcess.on("close", (code) => {
    if (code !== 0) {
      console.error(`Python process exited with code ${code}`);
      console.error(stderrData);
      return res.status(500).send("Error processing file: " + stderrData);
    }

    // Determine the names of the generated output files.
    // For example, if outputPath is "outputs/output-123456789.scad",
    // it will create:
    //   - outputs/output-123456789_main.scad
    //   - outputs/output-123456789_frame.scad
    //   - outputs/output-123456789.scad.log
    const mainScad = outputBase + "_main.scad";
    const frameScad = outputBase + "_frame.scad";
    const logFile = outputBase + ".scad.log";

    // Render the result page with download links
    res.render("result", {
      mainScad: "/outputs/" + mainScad,
      frameScad: "/outputs/" + frameScad,
      logFile: "/outputs/" + logFile,
      stdout: stdoutData,
      stderr: stderrData,
    });
  });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
