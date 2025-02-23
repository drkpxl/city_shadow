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

// Serve static files
app.use(express.static(path.join(__dirname, "public")));
app.use("/uploads", express.static("uploads"));
app.use("/outputs", express.static("outputs"));

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Ensure uploads/outputs folders exist
const uploadsDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}
const outputsDir = path.join(__dirname, "outputs");
if (!fs.existsSync(outputsDir)) {
  fs.mkdirSync(outputsDir);
}

// Configure Multer storage
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, "uploads/");
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + "-" + uuidv4();
    cb(null, uniqueSuffix + "-" + file.originalname);
  },
});

// Only allow .geojson files
function fileFilter(req, file, cb) {
  const ext = path.extname(file.originalname).toLowerCase();
  if (ext === ".geojson") {
    cb(null, true);
  } else {
    cb(new Error("Invalid file type. Only .geojson files are allowed."));
  }
}

// Create Multer instance with storage + fileFilter
const upload = multer({ storage: storage, fileFilter: fileFilter });

// -------------------------------------
// ROUTES
// -------------------------------------

// Home route
app.get("/", (req, res) => {
  res.render("index");
});

// Endpoint to handle AJAX file upload
app.post("/uploadFile", upload.single("geojson"), (req, res) => {
  // If Multer’s fileFilter rejects the file, req.file will be undefined
  if (!req.file) {
    return res
      .status(400)
      .json({ error: "No valid .geojson file was uploaded." });
  }
  const filePath = path.join(__dirname, req.file.path);
  res.json({ filePath: filePath });
});

// Live preview endpoint
app.post("/preview", (req, res) => {
  const uploadedFile = req.body.uploadedFile;
  if (!uploadedFile) {
    return res.status(400).json({ error: "No uploaded file provided." });
  }
  const outputBase = "preview-" + Date.now() + "-" + uuidv4();
  const outputScad = path.join(outputsDir, outputBase + ".scad");

  let args = [
    path.join(__dirname, "geojson_to_shadow_city.py"),
    uploadedFile,
    outputScad,
    "--export",
    "preview",
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

  // NEW bridging lines
  if (req.body["bridge-height"]) {
    args.push("--bridge-height", req.body["bridge-height"]);
  }
  if (req.body["bridge-thickness"]) {
    args.push("--bridge-thickness", req.body["bridge-thickness"]);
  }
  if (req.body["support-width"]) {
    args.push("--support-width", req.body["support-width"]);
  }

  // Preprocessing
  if (req.body.preprocess === "on") args.push("--preprocess");
  if (req.body["crop-distance"])
    args.push("--crop-distance", req.body["crop-distance"]);
  if (req.body["crop-bbox"]) {
    const bbox = req.body["crop-bbox"]
      .split(",")
      .map((coord) => coord.trim())
      .map(Number);
    if (bbox.length === 4 && bbox.every((num) => !isNaN(num))) {
      args.push(
        "--crop-bbox",
        bbox[0].toString(),
        bbox[1].toString(),
        bbox[2].toString(),
        bbox[3].toString()
      );
    }
  }

  // Preview integration
  if (req.body["preview-size-width"] && req.body["preview-size-height"]) {
    args.push(
      "--preview-size",
      req.body["preview-size-width"],
      req.body["preview-size-height"]
    );
  }
  if (req.body["preview-file"]) {
    args.push("--preview-file", req.body["preview-file"]);
  }
  if (req.body.watch === "on") {
    args.push("--watch");
  }
  if (req.body["openscad-path"]) {
    args.push("--openscad-path", req.body["openscad-path"]);
  }

  console.log("Live preview generation command:", args.join(" "));

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
      console.error("Python preview process exited with code", code);
      console.error(stderrData);
      return res.status(500).json({ error: stderrData });
    }
    const previewMain = outputBase + "_preview_main.png";
    const previewFrame = outputBase + "_preview_frame.png";

    res.json({
      previewMain: "/outputs/" + previewMain,
      previewFrame: "/outputs/" + previewFrame,
      stdout: stdoutData,
      stderr: stderrData,
    });
  });
});

// Final render endpoint
app.post("/render", (req, res) => {
  const uploadedFile = req.body.uploadedFile;
  if (!uploadedFile) {
    return res.status(400).json({ error: "No uploaded file provided." });
  }
  const outputBase = "output-" + Date.now() + "-" + uuidv4();
  const outputPath = path.join(outputsDir, outputBase + ".scad");

  let args = [
    path.join(__dirname, "geojson_to_shadow_city.py"),
    uploadedFile,
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

  // NEW bridging lines
  if (req.body["bridge-height"]) {
    args.push("--bridge-height", req.body["bridge-height"]);
  }
  if (req.body["bridge-thickness"]) {
    args.push("--bridge-thickness", req.body["bridge-thickness"]);
  }
  if (req.body["support-width"]) {
    args.push("--support-width", req.body["support-width"]);
  }

  // Preprocessing
  if (req.body.preprocess === "on") args.push("--preprocess");
  if (req.body["crop-distance"])
    args.push("--crop-distance", req.body["crop-distance"]);
  if (req.body["crop-bbox"]) {
    const bbox = req.body["crop-bbox"]
      .split(",")
      .map((coord) => coord.trim())
      .map(Number);
    if (bbox.length === 4 && bbox.every((num) => !isNaN(num))) {
      args.push(
        "--crop-bbox",
        bbox[0].toString(),
        bbox[1].toString(),
        bbox[2].toString(),
        bbox[3].toString()
      );
    }
  }

  // Export options
  if (req.body.export) args.push("--export", req.body.export);
  if (req.body["output-stl"]) args.push("--output-stl", req.body["output-stl"]);
  if (req.body["no-repair"] === "on") args.push("--no-repair");
  if (req.body.force === "on") args.push("--force");

  // Preview & integration
  if (req.body["preview-size-width"] && req.body["preview-size-height"]) {
    args.push(
      "--preview-size",
      req.body["preview-size-width"],
      req.body["preview-size-height"]
    );
  }
  if (req.body["preview-file"]) {
    args.push("--preview-file", req.body["preview-file"]);
  }
  if (req.body.watch === "on") {
    args.push("--watch");
  }
  if (req.body["openscad-path"]) {
    args.push("--openscad-path", req.body["openscad-path"]);
  }

  console.log("Final render command:", args.join(" "));

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
      console.error("Python final render process exited with code", code);
      console.error(stderrData);
      return res.status(500).json({ error: stderrData });
    }
    const mainScad = outputBase + "_main.scad";
    const frameScad = outputBase + "_frame.scad";
    const logFile = outputBase + ".scad.log";

    let stlFiles = {};
    if (req.body.export === "stl" || req.body.export === "both") {
      const mainStl = outputBase + "_main.stl";
      const frameStl = outputBase + "_frame.stl";
      stlFiles = {
        mainStl: "/outputs/" + mainStl,
        frameStl: "/outputs/" + frameStl,
      };
    }

    res.json({
      mainScad: "/outputs/" + mainScad,
      frameScad: "/outputs/" + frameScad,
      logFile: "/outputs/" + logFile,
      stlFiles: stlFiles,
      stdout: stdoutData,
      stderr: stderrData,
    });
  });
});

// Fallback /upload endpoint (if needed)
app.post("/upload", upload.single("geojson"), (req, res) => {
  if (!req.file) {
    return res.status(400).send("No valid .geojson file was uploaded.");
  }
  res.redirect("/");
});

// Start the server
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
