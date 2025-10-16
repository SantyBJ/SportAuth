--
-- Secuencia: s_Deportes
--
-- DROP SEQUENCE IF EXISTS s_Deportes;

CREATE SEQUENCE IF NOT EXISTS s_Deportes
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 999
    ;

ALTER SEQUENCE s_Deportes
    OWNER TO postgres;