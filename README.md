# 📘 ChatGPT Archive System

**A local, PostgreSQL-backed system for archiving, searching, browsing, and backing up your full ChatGPT conversation history.**

This project ingests ChatGPT’s exported JSON files, stores them in a normalized PostgreSQL database, generates a static HTML site for offline browsing, and bundles automated backups (database dump + static site + raw exports) into timestamped archive folders.

The system is designed for durability, privacy, and long-term preservation of your ChatGPT knowledge.

---

# 🚀 Features

* **Ingestion Pipeline**

  * Reads ChatGPT export ZIPs
  * Normalizes chats & messages into PostgreSQL
  * Deduplicates using content hashing
  * Detects updated conversations
  * Stores raw JSON for future-proofing

* **Searchable Database**

  * Fast queries on titles, timestamps, message content
  * Optional full-text search and vector embeddings

* **Static HTML Site Generator**

  * Per-chat pages
  * Chronological indexes
  * Clean, fast, searchable browsing
  * 100% offline

* **Backup System**

  * PostgreSQL dump
  * Static HTML site
  * Raw export ZIP
  * Timestamped directory
  * One-command archival

* **Extensible Architecture**

  * Modular Python package
  * Optional Flask interface
  * Optional HTMX enhancement

---

# 📦 Directory Structure

```
chatgpt-archive/
│
├── ingest/                  # Ingestion pipeline modules
├── static_site/             # Auto-generated HTML (gitignored)
├── backups/                 # Timestamped backup folders (gitignored)
├── schema.sql               # Database schema
├── .env.example             # Template for secrets (NOT committed)
├── .gitignore
└── README.md
```

---

# ⚙️ Setup Instructions

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/chatgpt-archive.git
cd chatgpt-archive
```

---

## 2. Create a Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Install PostgreSQL (if needed)

Ubuntu / WSL:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
```

Confirm it is running:

```bash
sudo service postgresql status
```

---

## 5. Create the Database

```bash
sudo -u postgres createdb chat_archive
```

---

## 6. Apply the Schema

```bash
psql -U postgres -d chat_archive -f schema.sql
```

---

## 7. Create Your `.env` File

Do **NOT** commit your `.env`.
Instead, create it locally:

```bash
nano .env
```

Paste:

```
CHAT_ARCHIVE_DB_URL=postgresql://postgres:YOUR_PASSWORD@localhost/chat_archive
```

Save the file.

---

## 8. Place ChatGPT Export ZIPs

Put your ChatGPT export `.zip` files here:

```
exports/
```

(This folder is gitignored.)

---

## 9. Run the Ingestion Pipeline

Once implemented:

```bash
python -m ingest.run_ingest
```

---

## 10. Generate the Static HTML Site

```bash
python -m static_site.generate
```

Open in your browser:

```
static_site/index.html
```

---

## 11. Run Backup Script (optional)

```bash
python -m backup.create_backup
```

This produces:

```
backups/
    backup_2025-01-15_14-22-53/
        chat_archive.dump
        static_site/
        raw_exports/
```

---

# 🔐 Security & Privacy Warnings

⚠️ **Never commit your ChatGPT data or secrets to GitHub.**
This project is safe to make public *only if you do not commit:*

### ❌ ChatGPT export files (`exports/`)

### ❌ Static HTML output (`static_site/`)

### ❌ Database dumps (`*.sql`, `*.dump`, `backups/`)

### ❌ Logs containing message text

### ❌ Your `.env` file (contains passwords)

Your `.gitignore` **must** include:

```
.env
static_site/
backups/
exports/
raw_exports/
logs/
*.json
*.sql
*.dump
*.gz
```

These patterns are included by default.

---

# 🧪 Development & Contribution Guidelines

1. **Fork** the project or clone locally.
2. Use a **feature branch** for changes.
3. Keep PRs focused on one logical improvement.
4. Follow **PEP8** style guidelines.
5. Include docstrings for all modules and functions.
6. Do not include:

   * Real chat data
   * Credentials
   * Sensitive logs

---

# 🗺️ Future Roadmap

### 🔹 Phase 1 — Core System (MVP)

* [x] PostgreSQL schema
* [ ] Ingestion pipeline (JSON → DB)
* [ ] Static HTML site generator
* [ ] Backup system
* [ ] CLI interface

### 🔹 Phase 2 — Enhanced Browsing

* [ ] Flask app (local, offline)
* [ ] HTMX-powered page loading
* [ ] Full-text search
* [ ] Message-level filters

### 🔹 Phase 3 — Semantic Search (Optional)

* [ ] pgvector embeddings
* [ ] Similar-chats suggestions
* [ ] “Find related discussions” view

### 🔹 Phase 4 — Automation

* [ ] Automatic daily backup
* [ ] Scheduled ingestion
* [ ] Export-to-archive utility

### 🔹 Phase 5 — Extra Tools

* [ ] Chat summaries
* [ ] Tagging system
* [ ] Message statistics
* [ ] Prompt templates index

---
