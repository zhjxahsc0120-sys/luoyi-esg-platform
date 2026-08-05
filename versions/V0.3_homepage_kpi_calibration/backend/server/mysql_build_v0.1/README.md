# Luoyi ESG MySQL Build Package V0.1

This is the ASCII fallback README for tools that have trouble displaying the Chinese filename `README_建库说明.md`.

Use the scripts in this order:

```sql
SOURCE 01_schema_mysql.sql;
SOURCE 02_seed_dictionary.sql;
SOURCE 03_seed_field_mapping.sql;
SOURCE 04_seed_demo_data.sql;
SOURCE 05_views.sql;
SOURCE 06_validation_queries.sql;
```

Target:

- MySQL 8.0+
- Database: `luoyi_esg`
- Charset: `utf8mb4`

Validation targets:

- 12 dashboard KPI rows
- S01 = 368
- 12 upload tasks
- 10 document samples
- 7 review records
- 27 AI field mapping rules
- 3 demo parse jobs
- at least 1 task match candidate
