DO $$
BEGIN
    IF NOT EXISTS (
        SELECT
        FROM pg_catalog.pg_roles
        WHERE rolname = 'financial_reader'
    ) THEN
        CREATE ROLE financial_reader
        LOGIN PASSWORD 'reader_dev_password';
    END IF;
END
$$;
