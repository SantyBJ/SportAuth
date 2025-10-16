--
-- Secuencia: Profesionalismo
--
-- DROP SEQUENCE IF EXISTS s_Profesionalismo;

CREATE SEQUENCE IF NOT EXISTS s_Profesionalismo
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9999
    ;

ALTER SEQUENCE s_Profesionalismo
    OWNER TO postgres;