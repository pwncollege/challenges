INSERT OR IGNORE INTO users (user_id, user_uuid)
VALUES (1, '11111111-1111-4111-8111-111111111111');

INSERT OR IGNORE INTO nodes (node_id, node_uuid, base_url, status)
VALUES (1, '33333333-3333-4333-8333-333333333333', 'http://127.0.0.1:8000', 'active');

INSERT OR IGNORE INTO nodes (node_id, node_uuid, base_url, status)
VALUES (2, '44444444-4444-4444-8444-444444444444', 'http://127.0.0.1:8001', 'disabled');

UPDATE nodes
SET
  base_url = CASE node_id
    WHEN 1 THEN 'http://127.0.0.1:8000'
    WHEN 2 THEN 'http://127.0.0.1:8001'
    ELSE base_url
  END,
  status = CASE node_id WHEN 1 THEN 'active' WHEN 2 THEN 'disabled' ELSE status END
WHERE node_id IN (1, 2);

DELETE FROM user_workspace_locks WHERE user_id = 1;
DELETE FROM volume_locks
WHERE volume_id IN (
  SELECT volume_id
  FROM user_home_volumes
  WHERE user_id = 1
);
DELETE FROM user_workspaces WHERE user_id = 1;
DELETE FROM workspaces;
