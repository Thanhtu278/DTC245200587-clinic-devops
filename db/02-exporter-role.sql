DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'exporter') THEN
        CREATE ROLE exporter WITH LOGIN PASSWORD 'PgExporterClinic2026Sec';
    ELSE
        ALTER ROLE exporter WITH PASSWORD 'PgExporterClinic2026Sec';
    END IF;
    GRANT pg_monitor TO exporter;
END
$$;
