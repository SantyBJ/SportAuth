--
-- Resticciones a la Tabla: Posicion
--
ALTER TABLE t_Posicion ADD CONSTRAINT ch_Posicion_min_jugadores   CHECK (pscn_min_jugadores > 0);
ALTER TABLE t_Posicion ADD CONSTRAINT ch_Posicion_max_jugadores   CHECK (pscn_max_jugadores >= pscn_min_jugadores);
ALTER TABLE t_Posicion ADD CONSTRAINT ch_Posicion_valid_jugadores CHECK ((pscn_min_jugadores IS NULL AND pscn_max_jugadores IS NULL) OR (pscn_min_jugadores IS NOT NULL AND pscn_max_jugadores IS NOT NULL));

ALTER TABLE t_Posicion ADD CONSTRAINT fk_Posicion_Deportes FOREIGN KEY (pscn_dprt) REFERENCES t_Deportes(dprt_dprt);