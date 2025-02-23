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

// Define directories
const uploadsDir = path.join(__dirname, "uploads");
const outputsDir = path.join(__dirname, "outputs");

// Ensure required directories exist
[uploadsDir, outputsDir].forEach((dir) => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir);
  }
});

// Configure Multer storage
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, "uploads/"),
  filename: (req, file, cb) => {
    const uniqueSuffix = `${Date.now()}-${uuidv4()}`;
    cb(null, `${uniqueSuffix}-${file.originalname}`);
  },
});

// Only allow .geojson files
const fileFilter = (req, file, cb) => {
  const ext = path.extname(file.originalname).toLowerCase();
  ext === ".geojson"
    ? cb(null, true)
    : cb(new Error("Invalid file type. Only .geojson files are allowed."));
};

const upload = multer({ storage, fileFilter });

// Shared argument processing functions
const processBasicOptions = (body, args) => {
  const numberOptions = [
    "size",
    "height",
    "detail",
    "merge-distance",
    "cluster-size",
    "height-variance",
    "road-width",
    "water-depth",
    "min-building-area",
  ];

  numberOptions.forEach((opt) => {
    if (body[opt]) args.push(`--${opt}`, body[opt]);
  });

  if (body.style) args.push("--style", body.style);
  if (body.debug === "on") args.push("--debug");
};

const processBridgeOptions = (body, args) => {
  const bridgeOptions = ["bridge-height", "bridge-thickness", "support-width"];
  bridgeOptions.forEach((opt) => {
    if (body[opt]) args.push(`--${opt}`, body[opt]);
  });
};

const processPreprocessingOptions = (body, args) => {
  if (body.preprocess === "on") args.push("--preprocess");
  if (body["crop-distance"])
    args.push("--crop-distance", body["crop-distance"]);

  if (body["crop-bbox"]) {
    const bbox = body["crop-bbox"]
      .split(",")
      .map((coord) => coord.trim())
      .map(Number);
    if (bbox.length === 4 && bbox.every((num) => !isNaN(num))) {
      args.push("--crop-bbox", ...bbox.map(String));
    }
  }
};

const processPreviewOptions = (body, args) => {
  if (body["preview-size-width"] && body["preview-size-height"]) {
    args.push(
      "--preview-size",
      body["preview-size-width"],
      body["preview-size-height"]
    );
  }
  if (body["preview-file"]) args.push("--preview-file", body["preview-file"]);
  if (body.watch === "on") args.push("--watch");
  if (body["openscad-path"])
    args.push("--openscad-path", body["openscad-path"]);
};

const buildPythonArgs = (inputFile, outputFile, body) => {
  const args = [
    path.join(__dirname, "geojson_to_shadow_city.py"),
    inputFile,
    outputFile,
  ];

  processBasicOptions(body, args);
  processBridgeOptions(body, args);
  processPreprocessingOptions(body, args);
  processPreviewOptions(body, args);

  return args;
};

// Route handlers
app.get("/", (req, res) => res.render("index"));

app.post("/uploadFile", upload.single("geojson"), (req, res) => {
  if (!req.file) {
    return res
      .status(400)
      .json({ error: "No valid .geojson file was uploaded." });
  }
  res.json({ filePath: path.join(__dirname, req.file.path) });
});

const runPythonProcess = (args) => {
  return new Promise((resolve, reject) => {
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
        console.error("Python process exited with code", code);
        console.error(stderrData);
        reject(stderrData);
        return;
      }
      resolve({ stdout: stdoutData, stderr: stderrData });
    });
  });
};

app.post("/preview", async (req, res) => {
  const uploadedFile = req.body.uploadedFile;
  if (!uploadedFile) {
    return res.status(400).json({ error: "No uploaded file provided." });
  }

  const outputBase = `preview-${Date.now()}-${uuidv4()}`;
  const outputScad = path.join(outputsDir, `${outputBase}.scad`);

  try {
    const args = buildPythonArgs(uploadedFile, outputScad, req.body);

    const { stdout, stderr } = await runPythonProcess(args);

    res.json({
      previewMain: `/outputs/${outputBase}_preview_main.png`,
      previewFrame: `/outputs/${outputBase}_preview_frame.png`,
      stdout,
      stderr,
    });
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

app.post("/render", async (req, res) => {
  const uploadedFile = req.body.uploadedFile;
  if (!uploadedFile) {
    return res.status(400).json({ error: "No uploaded file provided." });
  }

  const outputBase = `output-${Date.now()}-${uuidv4()}`;
  const outputPath = path.join(outputsDir, `${outputBase}.scad`);

  try {
    const args = buildPythonArgs(uploadedFile, outputPath, req.body);
    const { stdout, stderr } = await runPythonProcess(args);

    const response = {
      mainScad: `/outputs/${outputBase}_main.scad`,
      frameScad: `/outputs/${outputBase}_frame.scad`,
      logFile: `/outputs/${outputBase}.scad.log`,
      stdout,
      stderr,
      stlFiles: {
        mainStl: `/outputs/${outputBase}_main.stl`,
        frameStl: `/outputs/${outputBase}_frame.stl`,
      },
    };

    res.json(response);
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

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
