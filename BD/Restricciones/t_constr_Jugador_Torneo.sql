--
-- Resticciones a la Tabla: Jugador_Torneo
--
ALTER TABLE t_Jugador_Torneo ADD CONSTRAINT fk_Jugador       FOREIGN KEY (jgtr_jugador)             REFERENCES t_jugadores(jgdr_jgdr);
ALTER TABLE t_Jugador_Torneo ADD CONSTRAINT fk_torneo_equipo FOREIGN KEY (jgtr_torneo, jgtr_equipo) REFERENCES t_Equipo_Torneo(eqtn_torneo, eqtn_equipo);

ALTER TABLE t_Jugador_Torneo ADD CONSTRAINT uq_nro_camiseta  UNIQUE (jgtr_torneo, jgtr_equipo, jgtr_nro_camiseta);