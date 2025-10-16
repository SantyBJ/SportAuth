--
-- Secuencia: Posicion
--
-- DROP SEQUENCE IF EXISTS s_Posicion;

CREATE SEQUENCE IF NOT EXISTS s_Posicion
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 99999
    ;

ALTER SEQUENCE s_Posicion
    OWNER TO postgres;