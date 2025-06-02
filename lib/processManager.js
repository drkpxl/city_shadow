const { spawn } = require('child_process');
const EventEmitter = require('events');

class ProcessManager extends EventEmitter {
  constructor(maxConcurrent = 5, timeout = 600000) { // 10 minute default timeout
    super();
    this.maxConcurrent = maxConcurrent;
    this.timeout = timeout;
    this.activeProcesses = new Map();
    this.queue = [];
  }

  async executeProcess(jobId, command, args, options = {}) {
    // Check if we can start a new process
    if (this.activeProcesses.size >= this.maxConcurrent) {
      // Queue the process
      return new Promise((resolve, reject) => {
        this.queue.push({ jobId, command, args, options, resolve, reject });
      });
    }

    return this._startProcess(jobId, command, args, options);
  }

  async _startProcess(jobId, command, args, options) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const processOptions = {
        ...options,
        detached: false,
        stdio: ['ignore', 'pipe', 'pipe']
      };

      const childProcess = spawn(command, args, processOptions);
      
      // Set up timeout
      const timeoutId = setTimeout(() => {
        if (this.activeProcesses.has(jobId)) {
          this._killProcess(jobId, 'Process timeout exceeded');
          reject(new Error(`Process ${jobId} timed out after ${this.timeout}ms`));
        }
      }, this.timeout);

      // Store process info
      const processInfo = {
        process: childProcess,
        startTime,
        timeoutId,
        stdout: '',
        stderr: ''
      };
      
      this.activeProcesses.set(jobId, processInfo);

      // Handle stdout
      childProcess.stdout.on('data', (data) => {
        processInfo.stdout += data.toString();
        this.emit('stdout', { jobId, data: data.toString() });
      });

      // Handle stderr
      childProcess.stderr.on('data', (data) => {
        processInfo.stderr += data.toString();
        this.emit('stderr', { jobId, data: data.toString() });
      });

      // Handle process exit
      childProcess.on('exit', (code, signal) => {
        clearTimeout(timeoutId);
        this.activeProcesses.delete(jobId);
        
        const duration = Date.now() - startTime;
        const result = {
          code,
          signal,
          stdout: processInfo.stdout,
          stderr: processInfo.stderr,
          duration
        };

        if (code === 0) {
          resolve(result);
        } else {
          reject(new Error(`Process exited with code ${code}: ${processInfo.stderr}`));
        }

        // Process next in queue
        this._processQueue();
      });

      // Handle process errors
      childProcess.on('error', (error) => {
        clearTimeout(timeoutId);
        this.activeProcesses.delete(jobId);
        reject(error);
        this._processQueue();
      });
    });
  }

  _killProcess(jobId, reason) {
    const processInfo = this.activeProcesses.get(jobId);
    if (processInfo) {
      try {
        // Kill process group on Unix-like systems
        if (process.platform !== 'win32') {
          process.kill(-processInfo.process.pid, 'SIGTERM');
        } else {
          processInfo.process.kill('SIGTERM');
        }
        
        // Force kill after 5 seconds if still running
        setTimeout(() => {
          if (this.activeProcesses.has(jobId)) {
            if (process.platform !== 'win32') {
              process.kill(-processInfo.process.pid, 'SIGKILL');
            } else {
              processInfo.process.kill('SIGKILL');
            }
          }
        }, 5000);
        
        this.emit('process-killed', { jobId, reason });
      } catch (error) {
        console.error(`Error killing process ${jobId}:`, error);
      }
    }
  }

  _processQueue() {
    if (this.queue.length > 0 && this.activeProcesses.size < this.maxConcurrent) {
      const { jobId, command, args, options, resolve, reject } = this.queue.shift();
      this._startProcess(jobId, command, args, options)
        .then(resolve)
        .catch(reject);
    }
  }

  killJob(jobId) {
    this._killProcess(jobId, 'Manual termination');
    
    // Remove from queue if present
    this.queue = this.queue.filter(item => item.jobId !== jobId);
  }

  getActiveProcessCount() {
    return this.activeProcesses.size;
  }

  getQueueLength() {
    return this.queue.length;
  }

  shutdown() {
    // Kill all active processes
    for (const [jobId] of this.activeProcesses) {
      this._killProcess(jobId, 'System shutdown');
    }
    
    // Clear queue
    this.queue = [];
  }
}

module.exports = ProcessManager;