const express = require("express");
const multer = require("multer");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const { v4: uuidv4 } = require("uuid");

const app = express();
const port = process.env.PORT || 3000;

// Configuration setup
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));
app.use("/uploads", express.static("uploads"));
app.use("/outputs", express.static("outputs"));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// File upload configuration
const upload = multer({
  storage: multer.diskStorage({
    destination: "uploads/",
    filename: (req, file, cb) => {
      const uniqueSuffix = `${Date.now()}-${uuidv4()}`;
      cb(null, `${uniqueSuffix}-${file.originalname}`);
    },
  }),
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    ext === ".geojson" ? cb(null, true) : cb(new Error("Invalid file type"));
  },
});

// Argument configuration
const OPTION_CONFIG = [
  // Basic options
  { bodyKey: "size", cliFlag: "--size" },
  { bodyKey: "height", cliFlag: "--height" },
  { bodyKey: "style", cliFlag: "--style" },
  { bodyKey: "detail", cliFlag: "--detail" },
  { bodyKey: "merge-distance", cliFlag: "--merge-distance" },
  { bodyKey: "cluster-size", cliFlag: "--cluster-size" },
  { bodyKey: "height-variance", cliFlag: "--height-variance" },
  { bodyKey: "road-width", cliFlag: "--road-width" },
  { bodyKey: "water-depth", cliFlag: "--water-depth" },
  { bodyKey: "min-building-area", cliFlag: "--min-building-area" },

  // Bridge options
  { bodyKey: "bridge-height", cliFlag: "--bridge-height" },
  { bodyKey: "bridge-thickness", cliFlag: "--bridge-thickness" },
  { bodyKey: "support-width", cliFlag: "--support-width" },

  // Preprocessing options
  { bodyKey: "preprocess", cliFlag: "--preprocess", isFlag: true },
  { bodyKey: "crop-distance", cliFlag: "--crop-distance" },
  {
    bodyKey: "crop-bbox",
    process: (value) => {
      const bbox = value.split(",").map((coord) => Number(coord.trim()));
      return bbox.length === 4 && bbox.every((num) => !isNaN(num))
        ? ["--crop-bbox", ...bbox.map(String)]
        : [];
    },
  },

  // Debug flag
  { bodyKey: "debug", cliFlag: "--debug", isFlag: true },
];

const buildPythonArgs = (inputFile, outputFile, body) => {
  const args = [
    path.join(__dirname, "geojson_to_shadow_city.py"),
    inputFile,
    outputFile,
  ];

  OPTION_CONFIG.forEach((config) => {
    const value = body[config.bodyKey];
    if (value === undefined || value === "") return;

    if (config.process) {
      args.push(...config.process(value));
    } else if (config.isFlag) {
      if (value === "on") args.push(config.cliFlag);
    } else {
      args.push(config.cliFlag, value);
    }
  });

  return args;
};

// Route handlers
app.get("/", (req, res) => res.render("index"));

app.post("/uploadFile", upload.single("geojson"), (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No file uploaded" });
  res.json({ filePath: req.file.path });
});

const runPythonProcess = (args) => {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn("python3", args);
    let stdoutData = "";
    let stderrData = "";

    pythonProcess.stdout.on("data", (data) => (stdoutData += data));
    pythonProcess.stderr.on("data", (data) => (stderrData += data));

    pythonProcess.on("close", (code) => {
      code !== 0
        ? reject(stderrData)
        : resolve({ stdout: stdoutData, stderr: stderrData });
    });
  });
};

app.post("/preview", async (req, res) => {
  try {
    const outputBase = `preview-${Date.now()}-${uuidv4()}`;
    const outputScad = path.join("outputs", `${outputBase}.scad`);

    const args = buildPythonArgs(req.body.uploadedFile, outputScad, req.body);

    await runPythonProcess(args);

    res.json({
      previewMain: `/outputs/${outputBase}_preview_main.png`,
      previewFrame: `/outputs/${outputBase}_preview_frame.png`,
    });
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

app.post("/render", async (req, res) => {
  try {
    const outputBase = `output-${Date.now()}-${uuidv4()}`;
    const outputPath = path.join("outputs", `${outputBase}.scad`);

    const args = buildPythonArgs(req.body.uploadedFile, outputPath, req.body);

    await runPythonProcess(args);

    res.json({
      mainScad: `/outputs/${outputBase}_main.scad`,
      frameScad: `/outputs/${outputBase}_frame.scad`,
      stlFiles: {
        mainStl: `/outputs/${outputBase}_main.stl`,
        frameStl: `/outputs/${outputBase}_frame.stl`,
      },
    });
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

// Server startup
app.listen(port, () =>
  console.log(`Server running on port ${port}\nhttp://localhost:${port}`)
);
