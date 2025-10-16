--
-- Tabla: Posicion
--
-- DROP TABLE IF EXISTS t_Posicion;

CREATE TABLE IF NOT EXISTS t_Posicion
(
    pscn_pscn          NUMERIC(5,0) DEFAULT NEXTVAL('s_Posicion')
   ,pscn_descri        VARCHAR(100) CONSTRAINT nn_pscn_descri NOT NULL
   ,pscn_min_jugadores NUMERIC(2,0)
   ,pscn_max_jugadores NUMERIC(2,0)
   ,pscn_cambio        BOOLEAN      CONSTRAINT nn_pscn_cambio NOT NULL DEFAULT FALSE
   ,pscn_dprt          NUMERIC(3,0) CONSTRAINT nn_pscn_dprt   NOT NULL
   ,pscn_usua          VARCHAR(30)  CONSTRAINT nn_pscn_usua   NOT NULL DEFAULT USER
   ,pscn_feccre        TIMESTAMP    CONSTRAINT nn_pscn_feccre NOT NULL DEFAULT CURRENT_TIMESTAMP
   ,pscn_usua_alt      VARCHAR(30)
   ,pscn_fecalt        TIMESTAMP
)
TABLESPACE pg_default;
--
ALTER TABLE IF EXISTS t_Posicion
    OWNER to postgres;
--
-- Comentarios de la tabla y de las columnas de cada tabla
--
COMMENT ON TABLE  t_Posicion                    IS 'Almacenamiento de posiciones por deporte';
COMMENT ON COLUMN t_Posicion.pscn_pscn          IS 'Identificador de la posicion';
COMMENT ON COLUMN t_Posicion.pscn_descri        IS 'Descripcion de la posicion';
COMMENT ON COLUMN t_Posicion.pscn_min_jugadores IS 'numero minimo de jugadores en la posicion, si es NULL, no valida';
COMMENT ON COLUMN t_Posicion.pscn_max_jugadores IS 'numero maximo de jugadores en la posicion, si es NULL, no valida';
COMMENT ON COLUMN t_Posicion.pscn_dprt          IS 'Deporte asociado';
COMMENT ON COLUMN t_Posicion.pscn_usua          IS 'Usuario Creador del Profesionalismo';
COMMENT ON COLUMN t_Posicion.pscn_feccre        IS 'Fecha de creacion del Profesionalismo';
COMMENT ON COLUMN t_Posicion.pscn_usua_alt      IS 'Ultimo Usuario modificador del Profesionalismo';
COMMENT ON COLUMN t_Posicion.pscn_fecalt        IS 'Ultima fecha de modificacion del Profesionalismo';