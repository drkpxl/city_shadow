const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, '..', 'database', 'terrainforge.db');
const SCHEMA_PATH = path.join(__dirname, '..', 'database', 'schema.sql');

class Database {
  constructor() {
    this.db = null;
  }

  async initialize() {
    return new Promise((resolve, reject) => {
      this.db = new sqlite3.Database(DB_PATH, (err) => {
        if (err) {
          console.error('Error opening database:', err);
          reject(err);
          return;
        }
        
        console.log('Connected to SQLite database');
        
        // Initialize schema
        const schema = fs.readFileSync(SCHEMA_PATH, 'utf8');
        this.db.exec(schema, (err) => {
          if (err) {
            console.error('Error initializing schema:', err);
            reject(err);
            return;
          }
          
          console.log('Database schema initialized');
          resolve();
        });
      });
    });
  }

  // User methods
  async findUserByGithubId(githubId) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT * FROM users WHERE github_id = ?', [githubId], (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  async getUserCount() {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT COUNT(*) as count FROM users', (err, row) => {
        if (err) reject(err);
        else resolve(row.count);
      });
    });
  }

  async createUser(userData) {
    const { github_id, username, display_name, email, avatar_url } = userData;
    
    // Check if this will be the first user
    const userCount = await this.getUserCount();
    const isFirstUser = userCount === 0;
    
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO users (github_id, username, display_name, email, avatar_url, last_login, is_admin) 
         VALUES (?, ?, ?, ?, ?, datetime('now'), ?)`,
        [github_id, username, display_name, email, avatar_url, isFirstUser ? 1 : 0],
        function(err) {
          if (err) reject(err);
          else {
            const newUser = { id: this.lastID, ...userData, is_admin: isFirstUser };
            if (isFirstUser) {
              console.log(`First user '${username}' automatically made admin`);
            }
            resolve(newUser);
          }
        }
      );
    });
  }

  async updateUserLogin(userId) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE users SET last_login = datetime("now") WHERE id = ?',
        [userId],
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  }

  async incrementUserModelCount(userId) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE users SET model_count = model_count + 1 WHERE id = ?',
        [userId],
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  }

  // Model methods
  async createModel(modelData) {
    const { user_id, job_id, bbox, parameters, preview_url, stl_url, scad_url, expires_at } = modelData;
    const self = this;
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO models (user_id, job_id, bbox, parameters, preview_url, stl_url, scad_url, expires_at) 
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [user_id, job_id, bbox, JSON.stringify(parameters), preview_url, stl_url, scad_url, expires_at],
        function(err) {
          if (err) reject(err);
          else {
            // Increment user's model count
            self.incrementUserModelCount(user_id).catch(console.error);
            resolve({ id: this.lastID, ...modelData });
          }
        }
      );
    });
  }

  async getModelsByUserId(userId, limit = 50) {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT * FROM models WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
        [userId, limit],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows);
        }
      );
    });
  }

  async updateModelPreview(jobId, previewUrl) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE models SET preview_url = ? WHERE job_id = ?',
        [previewUrl, jobId],
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  }

  // Admin methods
  async getAllUsers(limit = 100, offset = 0) {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT u.*, COUNT(m.id) as actual_model_count 
         FROM users u 
         LEFT JOIN models m ON u.id = m.user_id 
         GROUP BY u.id 
         ORDER BY u.created_at DESC 
         LIMIT ? OFFSET ?`,
        [limit, offset],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows);
        }
      );
    });
  }

  async toggleUserEnabled(userId, isEnabled) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE users SET is_enabled = ? WHERE id = ?',
        [isEnabled ? 1 : 0, userId],
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  }

  async setUserAdmin(userId, isAdmin) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE users SET is_admin = ? WHERE id = ?',
        [isAdmin ? 1 : 0, userId],
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  }

  async getRecentModels(limit = 50) {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT m.*, u.username, u.display_name 
         FROM models m 
         JOIN users u ON m.user_id = u.id 
         ORDER BY m.created_at DESC 
         LIMIT ?`,
        [limit],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows);
        }
      );
    });
  }

  close() {
    if (this.db) {
      this.db.close();
    }
  }
}

module.exports = new Database();