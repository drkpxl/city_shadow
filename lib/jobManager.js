const fs = require('fs').promises;
const path = require('path');
const { v4: uuidv4 } = require('uuid');

class JobManager {
  constructor(tempDir = './temp') {
    this.tempDir = tempDir;
    this.jobs = new Map();
    this.jobHistory = new Map();
  }

  async initialize() {
    // Ensure temp directory exists
    await fs.mkdir(this.tempDir, { recursive: true });
  }

  async createJob(userId = 'anonymous', params = {}) {
    const job = {
      id: uuidv4(),
      userId,
      status: 'pending',
      params,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      progress: 0,
      logs: [],
      outputs: {}
    };

    // Create job directory structure
    const jobDir = path.join(this.tempDir, userId, job.id);
    await fs.mkdir(jobDir, { recursive: true });

    // Save job parameters
    const paramsPath = path.join(jobDir, 'params.json');
    await fs.writeFile(paramsPath, JSON.stringify(params, null, 2));

    // Create log file
    const logPath = path.join(jobDir, 'log.txt');
    await fs.writeFile(logPath, `Job ${job.id} created at ${new Date().toISOString()}\n`);

    job.paths = {
      jobDir,
      logPath,
      paramsPath,
      outputDir: path.join(jobDir, 'output')
    };

    // Create output directory
    await fs.mkdir(job.paths.outputDir, { recursive: true });

    this.jobs.set(job.id, job);
    return job;
  }

  getJob(jobId) {
    return this.jobs.get(jobId);
  }

  updateJobStatus(jobId, status, progress = null) {
    const job = this.jobs.get(jobId);
    if (!job) return null;

    job.status = status;
    job.updatedAt = Date.now();
    
    if (progress !== null) {
      job.progress = progress;
    }

    if (status === 'completed' || status === 'failed') {
      // Move to history
      this.jobHistory.set(jobId, job);
      this.jobs.delete(jobId);
    }

    return job;
  }

  async addJobLog(jobId, message, type = 'info') {
    const job = this.jobs.get(jobId) || this.jobHistory.get(jobId);
    if (!job) return;

    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      type,
      message
    };

    job.logs.push(logEntry);

    // Also write to log file
    if (job.paths && job.paths.logPath) {
      const logLine = `[${timestamp}] [${type.toUpperCase()}] ${message}\n`;
      await fs.appendFile(job.paths.logPath, logLine);
    }
  }

  async setJobOutput(jobId, outputKey, outputValue) {
    const job = this.jobs.get(jobId);
    if (!job) return;

    job.outputs[outputKey] = outputValue;
  }

  async cleanupJob(jobId, keepOutputs = false) {
    const job = this.jobHistory.get(jobId);
    if (!job || !job.paths) return;

    try {
      if (!keepOutputs) {
        // Remove entire job directory
        await fs.rm(job.paths.jobDir, { recursive: true, force: true });
      } else {
        // Keep outputs but remove temp files
        const files = await fs.readdir(job.paths.jobDir);
        for (const file of files) {
          if (file !== 'output') {
            await fs.rm(path.join(job.paths.jobDir, file), { recursive: true, force: true });
          }
        }
      }
    } catch (error) {
      console.error(`Error cleaning up job ${jobId}:`, error);
    }
  }

  async cleanupOldJobs(maxAgeMs = 24 * 60 * 60 * 1000) {
    const now = Date.now();
    
    for (const [jobId, job] of this.jobHistory.entries()) {
      if (now - job.updatedAt > maxAgeMs) {
        await this.cleanupJob(jobId);
        this.jobHistory.delete(jobId);
      }
    }
  }

  getActiveJobs() {
    return Array.from(this.jobs.values());
  }

  getJobHistory(userId = null) {
    const jobs = Array.from(this.jobHistory.values());
    if (userId) {
      return jobs.filter(job => job.userId === userId);
    }
    return jobs;
  }
}

module.exports = JobManager;