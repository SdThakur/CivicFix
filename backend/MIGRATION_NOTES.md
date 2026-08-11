# Migration Notes

To fully apply the new SLA, Crew Management, and Equipment models, create Alembic revisions for the newly added models.

Additionally, we need to add the `crew_id` column to the `work_orders` table:
```sql
ALTER TABLE work_orders ADD COLUMN crew_id INTEGER;
ALTER TABLE work_orders ADD CONSTRAINT fk_work_orders_crews FOREIGN KEY (crew_id) REFERENCES crews(id) ON DELETE SET NULL;
```
