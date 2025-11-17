-- Funcion Trigger: df_equipo_torneo_aiu()

-- DROP FUNCTION IF EXISTS df_equipo_torneo_aiu();

CREATE OR REPLACE FUNCTION df_equipo_torneo_aiu()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    --
    IF TG_OP = 'INSERT' THEN
        --
        NEW.eqtn_usua   := COALESCE(NEW.eqtn_usua, USER);
        NEW.eqtn_feccre := COALESCE(NEW.eqtn_feccre, CURRENT_TIMESTAMP);
        --
    ELSE
        --
        NEW.eqtn_usua_alt := COALESCE(NEW.eqtn_usua_alt, USER);
        NEW.eqtn_fecalt   := COALESCE(NEW.eqtn_fecalt, CURRENT_TIMESTAMP);
        --
    END IF;
    --
    IF NOT NEW.eqtn_estado THEN
        --
        UPDATE t_jugador_Torneo
           SET jgtr_estado = FALSE
         WHERE jgtr_equipo = NEW.eqtn_equipo
           AND jgtr_torneo = NEW.eqtn_torneo;
        --
    END IF;
    --
    RETURN NEW;
    --
END;
$BODY$;

ALTER FUNCTION df_equipo_torneo_aiu()
    OWNER TO postgres;

CREATE OR REPLACE TRIGGER d_equipo_torneo_aiu
    AFTER INSERT OR UPDATE 
    ON t_equipo_torneo
    FOR EACH ROW
    EXECUTE FUNCTION df_equipo_torneo_aiu();