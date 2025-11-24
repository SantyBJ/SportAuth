--
-- Secuencia: s_Equipos
--
-- DROP SEQUENCE IF EXISTS s_Equipos;

CREATE SEQUENCE IF NOT EXISTS s_Equipos
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 99999
    ;

ALTER SEQUENCE s_Equipos
    OWNER TO postgres;