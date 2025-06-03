#!/usr/bin/env node

const database = require('../lib/database');

async function makeAdmin(username) {
  try {
    await database.initialize();
    
    // Find user by username
    const users = await database.getAllUsers();
    const user = users.find(u => u.username === username);
    
    if (!user) {
      console.error(`User '${username}' not found`);
      process.exit(1);
    }
    
    // Make user admin
    await database.setUserAdmin(user.id, true);
    console.log(`Successfully made '${username}' an admin`);
    
    database.close();
    process.exit(0);
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

// Get username from command line
const username = process.argv[2];

if (!username) {
  console.log('Usage: node scripts/make-admin.js <username>');
  console.log('Example: node scripts/make-admin.js drkpxl');
  process.exit(1);
}

makeAdmin(username);