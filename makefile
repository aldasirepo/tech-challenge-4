POSTGRES_HOST ?= togglemaster-db.c1wcg6yasyvp.us-east-1.rds.amazonaws.com
POSTGRES_PORT ?= 5432
POSTGRES_USER ?= togglemaster_admin
POSTGRES_PASSWORD ?= sua_senha
POSTGRES_DB ?= postgres

PSQL = PGPASSWORD=$(POSTGRES_PASSWORD) psql "host=$(POSTGRES_HOST) port=$(POSTGRES_PORT) user=$(POSTGRES_USER) dbname=$(POSTGRES_DB) sslmode=require"

.PHONY: wait-db
wait-db:
	@echo "Waiting for database..."
	@until PGPASSWORD=$(POSTGRES_PASSWORD) pg_isready -h $(POSTGRES_HOST) -p $(POSTGRES_PORT) -U $(POSTGRES_USER) -d $(POSTGRES_DB); do \
		sleep 2; \
	done

.PHONY: auth
auth: wait-db
	@echo "Running auth-service init..."
	@$(PSQL) <<'SQL'
CREATE TABLE IF NOT EXISTS api_keys (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  key_hash VARCHAR(64) NOT NULL UNIQUE,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
SQL

.PHONY: flag
flag: wait-db
	@echo "Running flag-service init..."
	@$(PSQL) <<'SQL'
CREATE TABLE IF NOT EXISTS flags (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  description TEXT,
  is_enabled BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_timestamp ON flags;

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON flags
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();
SQL

.PHONY: targeting
targeting: wait-db
	@echo "Running targeting-service init..."
	@$(PSQL) <<'SQL'
CREATE TABLE IF NOT EXISTS targeting_rules (
  id SERIAL PRIMARY KEY,
  flag_name VARCHAR(100) UNIQUE NOT NULL,
  is_enabled BOOLEAN NOT NULL DEFAULT true,
  rules JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_timestamp ON targeting_rules;

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON targeting_rules
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();
SQL

.PHONY: all
all: auth flag targeting
	@echo "All migrations executed"

.PHONY: tables
tables:
	@$(PSQL) -c "\dt"