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
  { bodyKey: "bridge-height", cliFlag: "--bridge-height" },
  { bodyKey: "bridge-thickness", cliFlag: "--bridge-thickness" },
  { bodyKey: "support-width", cliFlag: "--support-width" },
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
  { bodyKey: "debug", cliFlag: "--debug", isFlag: true },
];

const buildPythonArgs = (inputFile, outputFile, body) => {
  const args = [
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

// Run Python process in unbuffered mode and capture logs.
const runPythonProcess = (args) => {
  return new Promise((resolve, reject) => {
    console.log(`[Python] Executing: python3 -u geojson_to_shadow_city.py ${args.join(' ')}`);
    
    // Use "-u" flag to force unbuffered output.
    const pythonProcess = spawn("python3", ["-u", "geojson_to_shadow_city.py", ...args]);
    let stdoutData = "";
    let stderrData = "";

    pythonProcess.stdout.on("data", (data) => {
      const output = data.toString();
      console.log(`[Python stdout]: ${output.trim()}`);
      stdoutData += output;
    });
    
    pythonProcess.stderr.on("data", (data) => {
      const output = data.toString();
      console.log(`[Python stderr]: ${output.trim()}`);
      stderrData += output;
    });

    pythonProcess.on("error", (err) => {
      console.error(`[Python] Process error:`, err);
      reject(`Failed to start Python process: ${err.message}`);
    });

    pythonProcess.on("close", (code) => {
      console.log(`[Python] Process exited with code ${code}`);
      if (code !== 0) {
        reject(stderrData || `Python process exited with code ${code}`);
      } else {
        resolve({ stdout: stdoutData, stderr: stderrData });
      }
    });
  });
};

app.get("/", (req, res) => res.render("index"));

app.post("/uploadFile", upload.single("geojson"), (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No file uploaded" });
  res.json({ filePath: req.file.path });
});

app.post("/preview", async (req, res) => {
  try {
    console.log(`[Preview] Request received with file: ${req.body.uploadedFile}`);
    const outputBase = `preview-${Date.now()}-${uuidv4()}`;
    const outputScad = path.join("outputs", `${outputBase}.scad`);

    const args = buildPythonArgs(req.body.uploadedFile, outputScad, req.body);

    // Run Python process and capture logs.
    const result = await runPythonProcess(args);

    res.json({
      previewMain: `/outputs/${outputBase}_preview_main.png`,
      previewFrame: `/outputs/${outputBase}_preview_frame.png`,
      stdout: result.stdout,
      stderr: result.stderr,
    });
  } catch (error) {
    console.error(`[Preview] Error:`, error);
    res.status(500).json({ 
      error: error.toString(),
      stdout: error.stdout || '',
      stderr: error.stderr || error.toString()
    });
  }
});

app.post("/render", async (req, res) => {
  try {
    const outputBase = `output-${Date.now()}-${uuidv4()}`;
    const outputPath = path.join("outputs", `${outputBase}.scad`);

    const args = buildPythonArgs(req.body.uploadedFile, outputPath, req.body);

    const result = await runPythonProcess(args);

    res.json({
      mainScad: `/outputs/${outputBase}_main.scad`,
      frameScad: `/outputs/${outputBase}_frame.scad`,
      stlFiles: {
        mainStl: `/outputs/${outputBase}_main.stl`,
        frameStl: `/outputs/${outputBase}_frame.stl`,
      },
      stdout: result.stdout,
      stderr: result.stderr,
    });
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

// Server startup
app.listen(port, () =>
  console.log(`Server running on port ${port}\nhttp://localhost:${port}`)
);
