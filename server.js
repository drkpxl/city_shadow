const express = require("express");
const multer = require("multer");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const { v4: uuidv4 } = require("uuid");
const http = require("http");
const { Server } = require("socket.io");
const JobManager = require("./lib/jobManager");
const ProcessManager = require("./lib/processManager");

const app = express();
const server = http.createServer(app);
const io = new Server(server);
const port = process.env.PORT || 3000;

// Initialize managers
const jobManager = new JobManager();
const processManager = new ProcessManager(5, 600000); // Max 5 concurrent, 10 min timeout
jobManager.initialize().catch(console.error);

// Forward process events to Socket.io
processManager.on('stdout', ({ jobId, data }) => {
  io.to(`job-${jobId}`).emit("job-output", {
    jobId,
    type: "stdout",
    data
  });
  
  // Parse progress if possible
  const progressMatch = data.match(/Progress:\s*(\d+)%/);
  if (progressMatch) {
    const progress = parseInt(progressMatch[1]);
    jobManager.updateJobStatus(jobId, "processing", progress);
    io.to(`job-${jobId}`).emit("job-progress", {
      jobId,
      progress
    });
  }
});

processManager.on('stderr', ({ jobId, data }) => {
  io.to(`job-${jobId}`).emit("job-output", {
    jobId,
    type: "stderr",
    data
  });
  jobManager.addJobLog(jobId, data, "error");
});

processManager.on('process-killed', ({ jobId, reason }) => {
  jobManager.addJobLog(jobId, `Process killed: ${reason}`, "error");
  jobManager.updateJobStatus(jobId, "failed");
  io.to(`job-${jobId}`).emit("job-failed", {
    jobId,
    error: reason
  });
});

// Configuration setup
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));
app.use("/uploads", express.static("uploads"));
app.use("/outputs", express.static("outputs"));
app.use("/temp", express.static("temp"));
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

// Socket.io connection handling
io.on("connection", (socket) => {
  console.log("Client connected:", socket.id);

  socket.on("disconnect", () => {
    console.log("Client disconnected:", socket.id);
  });

  socket.on("subscribe-job", (jobId) => {
    socket.join(`job-${jobId}`);
    console.log(`Client ${socket.id} subscribed to job ${jobId}`);
  });

  socket.on("unsubscribe-job", (jobId) => {
    socket.leave(`job-${jobId}`);
    console.log(`Client ${socket.id} unsubscribed from job ${jobId}`);
  });
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

// Run Python process with job management
const runPythonProcessWithJob = async (jobId, args) => {
  const job = jobManager.getJob(jobId);
  if (!job) throw new Error("Job not found");

  console.log(`[Job ${jobId}] Executing: python3 -u geojson_to_shadow_city.py ${args.join(' ')}`);
  await jobManager.addJobLog(jobId, `Executing: python3 -u geojson_to_shadow_city.py ${args.join(' ')}`);
  
  try {
    const result = await processManager.executeProcess(
      jobId,
      "python3",
      ["-u", "geojson_to_shadow_city.py", ...args],
      {
        cwd: process.cwd()
      }
    );
    
    // Log to file
    const logStream = fs.createWriteStream(job.paths.logPath, { flags: 'a' });
    logStream.write(`[STDOUT]\n${result.stdout}\n`);
    if (result.stderr) {
      logStream.write(`[STDERR]\n${result.stderr}\n`);
    }
    logStream.end();
    
    await jobManager.addJobLog(jobId, "Process completed successfully");
    jobManager.updateJobStatus(jobId, "completed", 100);
    
    io.to(`job-${jobId}`).emit("job-completed", {
      jobId,
      stdout: result.stdout,
      stderr: result.stderr
    });
    
    return result;
  } catch (error) {
    await jobManager.addJobLog(jobId, error.message, "error");
    jobManager.updateJobStatus(jobId, "failed");
    
    io.to(`job-${jobId}`).emit("job-failed", {
      jobId,
      error: error.message
    });
    
    throw error;
  }
};

app.get("/", (req, res) => res.render("index"));

app.post("/uploadFile", upload.single("geojson"), (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No file uploaded" });
  res.json({ filePath: req.file.path });
});

app.post("/preview", async (req, res) => {
  try {
    // Create a new job
    const job = await jobManager.createJob("anonymous", {
      type: "preview",
      ...req.body
    });
    
    console.log(`[Preview] Job ${job.id} created for file: ${req.body.uploadedFile}`);
    
    const outputBase = `preview-${job.id}`;
    const outputScad = path.join(job.paths.outputDir, `${outputBase}.scad`);

    const args = buildPythonArgs(req.body.uploadedFile, outputScad, req.body);

    // Start processing
    jobManager.updateJobStatus(job.id, "processing", 0);
    
    // Run Python process with job tracking
    const result = await runPythonProcessWithJob(job.id, args);
    
    // Store outputs
    await jobManager.setJobOutput(job.id, "previewMain", 
      path.join(job.paths.outputDir, `${outputBase}_preview_main.png`));
    await jobManager.setJobOutput(job.id, "previewFrame", 
      path.join(job.paths.outputDir, `${outputBase}_preview_frame.png`));

    res.json({
      jobId: job.id,
      previewMain: `/temp/anonymous/${job.id}/output/${outputBase}_preview_main.png`,
      previewFrame: `/temp/anonymous/${job.id}/output/${outputBase}_preview_frame.png`,
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
    // Create a new job
    const job = await jobManager.createJob("anonymous", {
      type: "render",
      ...req.body
    });
    
    const outputBase = `output-${job.id}`;
    const outputPath = path.join(job.paths.outputDir, `${outputBase}.scad`);

    const args = buildPythonArgs(req.body.uploadedFile, outputPath, req.body);

    // Start processing
    jobManager.updateJobStatus(job.id, "processing", 0);
    
    const result = await runPythonProcessWithJob(job.id, args);
    
    // Store outputs
    await jobManager.setJobOutput(job.id, "mainScad", 
      path.join(job.paths.outputDir, `${outputBase}_main.scad`));
    await jobManager.setJobOutput(job.id, "frameScad", 
      path.join(job.paths.outputDir, `${outputBase}_frame.scad`));
    await jobManager.setJobOutput(job.id, "mainStl", 
      path.join(job.paths.outputDir, `${outputBase}_main.stl`));
    await jobManager.setJobOutput(job.id, "frameStl", 
      path.join(job.paths.outputDir, `${outputBase}_frame.stl`));

    res.json({
      jobId: job.id,
      mainScad: `/temp/anonymous/${job.id}/output/${outputBase}_main.scad`,
      frameScad: `/temp/anonymous/${job.id}/output/${outputBase}_frame.scad`,
      stlFiles: {
        mainStl: `/temp/anonymous/${job.id}/output/${outputBase}_main.stl`,
        frameStl: `/temp/anonymous/${job.id}/output/${outputBase}_frame.stl`,
      },
      stdout: result.stdout,
      stderr: result.stderr,
    });
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

// Job status endpoint
app.get("/job/:jobId", (req, res) => {
  const job = jobManager.getJob(req.params.jobId) || 
              jobManager.jobHistory.get(req.params.jobId);
  
  if (!job) {
    return res.status(404).json({ error: "Job not found" });
  }
  
  res.json({
    id: job.id,
    status: job.status,
    progress: job.progress,
    createdAt: job.createdAt,
    updatedAt: job.updatedAt,
    outputs: job.outputs
  });
});

// Cleanup old jobs periodically
setInterval(() => {
  jobManager.cleanupOldJobs().catch(console.error);
}, 60 * 60 * 1000); // Every hour

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully...');
  
  // Stop accepting new connections
  server.close(() => {
    console.log('HTTP server closed');
  });
  
  // Shutdown process manager
  processManager.shutdown();
  
  // Wait for active jobs to complete or timeout
  const timeout = setTimeout(() => {
    console.log('Shutdown timeout, forcing exit');
    process.exit(1);
  }, 30000); // 30 second grace period
  
  // Clear timeout if we finish early
  timeout.unref();
  
  // Exit cleanly
  process.exit(0);
});

// Server startup
server.listen(port, () =>
  console.log(`Server running on port ${port}\nhttp://localhost:${port}`)
);