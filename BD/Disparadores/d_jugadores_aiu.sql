-- Funcion Trigger: df_jugadores_aiu()

-- DROP FUNCTION IF EXISTS df_jugadores_aiu();

CREATE OR REPLACE FUNCTION df_jugadores_aiu()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    --
    IF TG_OP = 'INSERT' THEN
        --
        NEW.jgdr_usua   := COALESCE(NEW.jgdr_usua, USER);
        NEW.jgdr_feccre := COALESCE(NEW.jgdr_feccre, CURRENT_TIMESTAMP);
        --
    ELSE
        --
        NEW.jgdr_usua_alt := COALESCE(NEW.jgdr_usua_alt, USER);
        NEW.jgdr_fecalt   := COALESCE(NEW.jgdr_fecalt, CURRENT_TIMESTAMP);
        --
    END IF;
    --
    IF NOT NEW.jgdr_estado THEN
        --
        UPDATE t_jugador_Torneo
           SET jgtr_estado = FALSE
         WHERE jgtr_jugador = NEW.jgdr_jgdr;
        --
    END IF;
    --
    RETURN NEW;
    --
END;
$BODY$;

ALTER FUNCTION df_jugadores_aiu()
    OWNER TO postgres;

CREATE OR REPLACE TRIGGER d_jugadores_aiu
    AFTER INSERT OR UPDATE 
    ON t_jugadores
    FOR EACH ROW
    EXECUTE FUNCTION df_jugadores_aiu();