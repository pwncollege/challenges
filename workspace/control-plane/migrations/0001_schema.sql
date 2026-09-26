CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  user_uuid TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS nodes (
  node_id INTEGER PRIMARY KEY,
  node_uuid TEXT NOT NULL UNIQUE,
  base_url TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL CHECK (status IN ('active', 'draining', 'disabled'))
);

CREATE TABLE IF NOT EXISTS workspaces (
  workspace_id INTEGER PRIMARY KEY,
  workspace_uuid TEXT NOT NULL UNIQUE,
  node_id INTEGER NOT NULL REFERENCES nodes(node_id) ON DELETE RESTRICT,
  container_image_ref TEXT NOT NULL,
  runtime_config_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('creating', 'running', 'destroying')),
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_workspaces_node_id ON workspaces(node_id);
CREATE INDEX IF NOT EXISTS idx_workspaces_status ON workspaces(status);
CREATE INDEX IF NOT EXISTS idx_workspaces_updated_at ON workspaces(updated_at);

CREATE TABLE IF NOT EXISTS user_workspaces (
  user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  workspace_id INTEGER REFERENCES workspaces(workspace_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS workspace_operations (
  user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE RESTRICT,
  operation_uuid TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL CHECK (kind IN ('start', 'stop')),
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS volumes (
  volume_id INTEGER PRIMARY KEY,
  volume_uuid TEXT NOT NULL UNIQUE,
  snapshot_uuid TEXT,
  node_id INTEGER REFERENCES nodes(node_id) ON DELETE RESTRICT,
  max_size_bytes INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_volumes_node_id ON volumes(node_id);
CREATE INDEX IF NOT EXISTS idx_volumes_updated_at ON volumes(updated_at);

CREATE TABLE IF NOT EXISTS user_home_volumes (
  user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  volume_id INTEGER NOT NULL UNIQUE REFERENCES volumes(volume_id) ON DELETE CASCADE
);
