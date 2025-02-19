// Switch to admin database first
db = db.getSiblingDB('admin');

// Create root user if it doesn't exist
try {
  db.createUser({
    user: 'admin',
    pwd: 'password123',
    roles: [
      { role: 'userAdminAnyDatabase', db: 'admin' },
      { role: 'readWriteAnyDatabase', db: 'admin' },
      { role: 'dbAdminAnyDatabase', db: 'admin' },
    ],
  });
} catch (err) {
  // User might already exist, continue
}

// Switch to and initialize arbitragex database
db = db.getSiblingDB('arbitragex');

// Create application user if it doesn't exist
try {
  db.createUser({
    user: 'admin',
    pwd: 'password123',
    roles: [
      { role: 'readWrite', db: 'arbitragex' },
      { role: 'dbAdmin', db: 'arbitragex' },
    ],
  });
} catch (err) {
  // User might already exist, continue
}

// Create initial collections if they don't exist
try {
  db.createCollection('trades');
} catch (err) {
  // Collection might already exist
}

try {
  db.createCollection('opportunities');
} catch (err) {
  // Collection might already exist
}
