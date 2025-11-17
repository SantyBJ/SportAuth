--
-- Tabla: Equipo_Torneo
--
-- DROP TABLE IF EXISTS t_Equipo_Torneo;

CREATE TABLE IF NOT EXISTS t_Equipo_Torneo
(
    eqtn_equipo   NUMERIC(5,0)
   ,eqtn_torneo   NUMERIC(11,0)
   ,eqtn_estado   BOOLEAN       CONSTRAINT nn_eqtn_estado NOT NULL DEFAULT TRUE
   ,eqtn_usua     VARCHAR(30)   CONSTRAINT nn_eqtn_usua   NOT NULL DEFAULT USER
   ,eqtn_feccre   TIMESTAMP     CONSTRAINT nn_eqtn_feccre NOT NULL DEFAULT CURRENT_TIMESTAMP
   ,eqtn_usua_alt VARCHAR(30)
   ,eqtn_fecalt   TIMESTAMP
)
TABLESPACE pg_default;
--
ALTER TABLE IF EXISTS public.t_Equipo_Torneo
    OWNER to postgres;
--
-- Comentarios de la tabla y de las columnas de cada tabla
--
COMMENT ON TABLE  t_Equipo_Torneo               IS 'Almacena Los torneos que han jugado los equipos';
COMMENT ON COLUMN t_Equipo_Torneo.eqtn_equipo   IS 'Identificacion del equipo';
COMMENT ON COLUMN t_Equipo_Torneo.eqtn_torneo   IS 'Identificacion del torneo';
COMMENT ON COLUMN t_Equipo_Torneo.eqtn_estado   IS 'Estado del equipo en el torneo, TRUE - Juega, FALSE - Eliminado';
COMMENT ON COLUMN t_Equipo_Torneo.eqtn_usua     IS 'Usuario que asocia equipo con torneo';
COMMENT ON COLUMN t_Equipo_Torneo.eqtn_feccre   IS 'Fecha de asociación';
COMMENT ON COLUMN t_Equipo_Torneo.eqtn_usua_alt IS 'Ultimo Usuario modificador';
COMMENT ON COLUMN t_Equipo_Torneo.eqtn_fecalt   IS 'Ultima fecha de modificacion';