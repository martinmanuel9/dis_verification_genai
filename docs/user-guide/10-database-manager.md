# Database Manager

Manage PostgreSQL and ChromaDB databases, view data, and perform maintenance.

## Overview

Database Manager provides:
- View database contents
- Manage collections and documents
- Clean up orphaned data
- Export/import data
- Database health monitoring
- Performance metrics

## Accessing Database Manager

1. Navigate to **Database Manager** page (sidebar)
2. Choose database type:
   - PostgreSQL (relational data)
   - ChromaDB (vector embeddings)

## PostgreSQL Management

### View Tables

[Screenshot: PostgreSQL table list]

```
Database: dis_verification_db

Tables (8):
├─ chat_sessions (234 rows)
├─ messages (1,823 rows)
├─ documents (45 rows)
├─ agents (23 rows)
├─ agent_sets (8 rows)
├─ test_plans (12 rows)
├─ test_cards (89 rows)
└─ users (5 rows)

[Refresh] [Export All] [Backup]
```

### Browse Data

Click any table to view contents:

```
Table: chat_sessions

┌────┬──────────┬────────────────┬────────┬──────────┐
│ ID │ User     │ Created        │ Model  │ Messages │
├────┼──────────┼────────────────┼────────┼──────────┤
│ 23 │ john_doe │ 2025-11-18 ... │ gpt-4o │ 45       │
│ 22 │ jane_s   │ 2025-11-17 ... │ llama  │ 12       │
└────┴──────────┴────────────────┴────────┴──────────┘

[Export CSV] [Delete Selected] [Refresh]
```

### Query Builder

Run custom SQL queries:

```
SQL Query:

SELECT model, COUNT(*) as usage_count, 
       AVG(token_count) as avg_tokens
FROM messages
WHERE created_at > '2025-11-01'
GROUP BY model
ORDER BY usage_count DESC;

[Run Query] [Save Query] [Export Results]

Results (3 rows):
┌─────────┬─────────────┬────────────┐
│ Model   │ Usage Count │ Avg Tokens │
├─────────┼─────────────┼────────────┤
│ gpt-4o  │ 1,234       │ 456        │
│ llama   │ 589         │ 312        │
└─────────┴─────────────┴────────────┘
```

### Database Maintenance

**Vacuum**:
```
Run VACUUM to reclaim space

Last vacuum: 2025-11-10 14:23
Database size: 234 MB
Estimated recovery: 45 MB

[Run Vacuum]
```

**Reindex**:
```
Rebuild indexes for better performance

[Analyze] [Reindex All] [Reindex Selected]
```

## ChromaDB Management

### View Collections

```
ChromaDB Collections (4)

┌───────────────────────────────────────────┐
│ technical_specifications                  │
│ Documents: 5 | Chunks: 234 | Size: 45 MB │
│ Embedding: arctic-embed-l                │
│ Created: 2025-11-15                      │
│ [View] [Export] [Delete]                 │
└───────────────────────────────────────────┘

[Create Collection] [Import] [Clean Up]
```

### Browse Vectors

View vector embeddings:

```
Collection: technical_specifications

Chunks (234):
┌────┬──────────────┬───────┬──────┬─────────┐
│ ID │ Document     │ Page  │ Dims │ Preview │
├────┼──────────────┼───────┼──────┼─────────┤
│ 1  │ Tech_Spec... │ 3     │ 768  │ The ... │
│ 2  │ Tech_Spec... │ 4     │ 768  │ Syste...│
└────┴──────────────┴───────┴──────┴─────────┘

[Search Vectors] [Export] [Refresh]
```

### Vector Search

Test semantic search:

```
Test Vector Search

Query: [authentication requirements]

Number of Results: [5 ▼]
Score Threshold: [0.5 ▼]

[Search]

Results:
1. Score: 0.92 | Doc: Tech_Spec.pdf | Page 23
   "The system shall provide user authentication..."
   
2. Score: 0.87 | Doc: Tech_Spec.pdf | Page 24
   "Authentication must use industry-standard..."
```

### Clean Orphaned Vectors

Remove vectors for deleted documents:

```
Orphaned Vector Cleanup

Scanning for orphaned vectors...

Found:
• 45 vectors for deleted documents
• 12 vectors in non-existent collections
• Estimated space to reclaim: 8.3 MB

[Preview Cleanup] [Clean Now]
```

## Data Export

### Export Options

```
Export Data

Source:
○ PostgreSQL Tables
  ☑ chat_sessions
  ☑ messages
  ☑ documents
  
● ChromaDB Collections
  ☑ technical_specifications
  ☑ test_plans
  
Format: [JSON ▼]
Options:
• JSON (structured)
• CSV (spreadsheet)
• SQL Dump (backup)
• Parquet (analytics)

[Export]
```

### Backup Database

```
Create Backup

Backup Type:
● Full Backup (all data)
○ Incremental (changes only)

Include:
☑ PostgreSQL
☑ ChromaDB
☑ Uploaded files
☑ Configuration

Destination:
[/backups/dis_verification_2025-11-18.zip]

[Create Backup]
```

## Best Practices

### Regular Maintenance

**Weekly**:
- Review database size
- Clean orphaned vectors
- Export important conversations

**Monthly**:
- Full database backup
- Vacuum and reindex
- Review old data for archival

### Storage Management

Monitor disk usage:

```
Storage Overview

PostgreSQL: 234 MB / 10 GB (2%)
ChromaDB:   456 MB / 20 GB (2%)
Files:      1.2 GB / 50 GB (2%)

Total: 1.9 GB / 80 GB (2%)

[View Details] [Clean Up]
```

## Next Steps

- **[Document Management](05-document-management.md)** - Manage uploaded documents
- **[Troubleshooting](12-troubleshooting.md)** - Database issues

---

See [FAQ](13-faq.md) for database questions
