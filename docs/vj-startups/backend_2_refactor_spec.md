# VJ Startups Service (Backend 2) Refactoring Specification

This document provides a blueprint for running the `backend 2` Node.js/Express server as a dedicated, standalone microservice.

---

## 1. Database Configuration

The `backend 2` microservice can continue utilizing **MongoDB** for flexible schemas (e.g. nested upvotes lists, comment threads, dynamic questionnaire responses), while reading or writing to the **Plane PostgreSQL** instance for user records or startup status synchronization.

### MongoDB Configuration (mongoose)
Ensure the mongoose connection URI is loaded correctly from env variables:
```javascript
// config/db.js
const mongoose = require('mongoose');

const connectDB = async () => {
  try {
    await mongoose.connect(process.env.MONGO_URI);
    console.log('✅ MongoDB Connected');
  } catch (err) {
    console.error('❌ Connection Failed:', err.message);
    process.exit(1);
  }
};
```

### Optional: PostgreSQL Sync Integration
If direct Postgres writes are desired (e.g., updating a startup's stage directly in Postgres when it passes a questionnaire), configure a `pg` pool client:
```javascript
const { Pool } = require('pg');
const pgPool = new Pool({
  connectionString: process.env.DATABASE_URL,
});
```

---

## 2. Authentication Middleware Refactoring

### Admin Auth Middleware (`middlewares/adminAuth.js`)
Currently, `backend 2` looks up a UUID `adminToken` in MongoDB. To simplify, allow it to verify if the request is signed with a valid Plane admin session or if the admin's email is present in the `ADMIN_EMAILS` env variable:
```javascript
const adminAuth = async (req, res, next) => {
  const token = req.headers['authorization']?.split(' ')[1];
  
  if (!token) {
    return res.status(401).json({ success: false, message: 'Authorization required' });
  }

  // Option A: Verify token exists in MongoDB users collection
  const user = await User.findOne({ adminToken: token, role: 'admin' });
  if (user) {
    req.adminUser = user;
    return next();
  }

  return res.status(403).json({ success: false, message: 'Access denied' });
};
```

---

## 3. Upload & Media Middleware

`backend 2` uses `multer` and `cloudinary` for title images, team icons, and pitch deck uploads. 
Keep this isolated from Plane's S3/MinIO engine. Multer is configured to use memory storage, sending buffer arrays directly to Cloudinary:

```javascript
const multer = require('multer');
const storage = multer.memoryStorage();
const upload = multer({ 
  storage,
  limits: { fileSize: 10 * 1024 * 1024 } // 10MB limit
});
```

---

## 4. Environment Variables Checklist (`.env`)

Deploy `backend 2` with the following variables:

```bash
PORT=5001
MONGO_URI=mongodb+srv://...
ADMIN_EMAILS=admin@vnrvjiet.in,lead@vnrvjiet.in
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```
