# VJ Startups Service (Backend 2) Refactoring Specification
> [!TIP]
> **Recommended Architecture**: Consolidating all data into a single **PostgreSQL** database (shared with Plane Core) is the optimal path. It removes synchronization delays, simplifies operations, ensures referential integrity (e.g. linking ideas directly to registered Plane users), and reduces hosting costs.

---

## 1. Unified Database Design (PostgreSQL-First)

Rather than keeping MongoDB for `backend 2` and syncing updates to PostgreSQL on Plane core, we store all collections—ideas, problems, upvotes, and users—in PostgreSQL. 

### Database Schema Mappings in PostgreSQL

| Feature Entity | MongoDB Collection (Old) | PostgreSQL Table (Unified) | Managed By |
| :--- | :--- | :--- | :--- |
| **Startups** | `startups` | `vj_startups` | Django Models / ORM |
| **Startup Members** | `startup_members` | `vj_startup_members` | Django Models / ORM |
| **Wings** | `wings` | `vj_wings` | Django Models / ORM |
| **Events** | `events` | `vj_events` | Django Models / ORM |
| **Ecosystem Ideas** | `ideas` | `vj_ideas` | Express SQL / Django ORM |
| **Ecosystem Problems** | `problems` | `vj_problems` | Express SQL / Django ORM |
| **Upvotes** | Inline array on document | `vj_upvotes` | Express SQL / Django ORM |
| **Users** | `users` | `accounts_user` (Plane User) | Django / Plane Core |

---

## 2. Express Database Connection (`config/db.js`)

In the Node.js/Express `backend 2` server, connect using a Postgres connection pool client (`pg`) instead of Mongoose:

```javascript
// config/db.js
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

pool.on('connect', () => {
  console.log('✅ Connected to Shared PostgreSQL Database');
});

pool.on('error', (err) => {
  console.error('❌ Unexpected Postgres Error:', err.message);
  process.exit(-1);
});

module.exports = pool;
```

---

## 3. SQL Query Patterns for Express (`backend 2`)

### 3.1 Auditing Student Ideas (with Paginated Search)
```javascript
const getIdeas = async (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 10;
  const offset = (page - 1) * limit;
  const searchQuery = req.query.search || '';

  try {
    const queryText = `
      SELECT i.*, u.email, u.first_name, u.last_name,
             (SELECT COUNT(*) FROM vj_upvotes WHERE idea_id = i.id) as upvotes_count
      FROM vj_ideas i
      LEFT JOIN accounts_user u ON i.user_id = u.id
      WHERE i.title ILIKE $1 OR i.description ILIKE $1
      ORDER BY i.created_at DESC
      LIMIT $2 OFFSET $3
    `;
    const values = [`%${searchQuery}%`, limit, offset];
    const { rows } = await pool.query(queryText, values);
    
    res.json({ success: true, page, limit, data: rows });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
};
```

### 3.2 Dynamic Upvoting Model (Handling Race Conditions)
Instead of Mongo `$addToSet` which can run into duplicate arrays, use a relational upvote constraints table:
```sql
CREATE TABLE vj_upvotes (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES accounts_user(id) ON DELETE CASCADE,
    idea_id INTEGER REFERENCES vj_ideas(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_idea_upvote UNIQUE (user_id, idea_id)
);
```

To toggle an upvote in Express:
```javascript
const toggleUpvote = async (req, res) => {
  const { ideaId } = req.body;
  const userId = req.user.id; // From authorized session token

  try {
    // Attempt insert; if it exists, delete it (toggle behavior)
    const checkQuery = `
      INSERT INTO vj_upvotes (user_id, idea_id)
      VALUES ($1, $2)
      ON CONFLICT (user_id, idea_id) DO NOTHING
      RETURNING id
    `;
    const result = await pool.query(checkQuery, [userId, ideaId]);

    if (result.rows.length === 0) {
      // Conflict hit -> remove upvote
      await pool.query('DELETE FROM vj_upvotes WHERE user_id = $1 AND idea_id = $2', [userId, ideaId]);
      return res.json({ success: true, action: 'removed' });
    }
    
    res.json({ success: true, action: 'added' });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
};
```

---

## 4. Admin Authentication Refactoring

Since the authentication token is stored inside the Plane database, checking admin authority is done by looking up user settings or roles directly in Postgres:

```javascript
const adminAuth = async (req, res, next) => {
  const token = req.headers['authorization']?.split(' ')[1];
  
  if (!token) {
    return res.status(401).json({ success: false, message: 'Authorization token required' });
  }

  try {
    // Find user by admin session token and check is_superuser/is_staff
    const queryText = `
      SELECT u.id, u.email, u.is_superuser, u.is_staff
      FROM accounts_user u
      JOIN accounts_session s ON s.user_id = u.id
      WHERE s.token = $1 AND u.is_active = true
    `;
    const { rows } = await pool.query(queryText, [token]);

    if (rows.length === 0 || (!rows[0].is_superuser && !rows[0].is_staff)) {
      return res.status(403).json({ success: false, message: 'Access denied: Admin credentials required' });
    }

    req.adminUser = rows[0];
    next();
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
};
```

---

## 5. Deployment Environment Variables Checklist (`.env`)

Deploy `backend 2` with variables connecting directly to the PostgreSQL pool:

```bash
PORT=5001
DATABASE_URL=postgresql://plane:plane@plane-db:5432/plane
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```
