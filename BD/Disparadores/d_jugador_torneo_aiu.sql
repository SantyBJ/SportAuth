-- Funcion Trigger: df_jugador_torneo_aiu()

-- DROP FUNCTION IF EXISTS df_jugador_torneo_aiu();

CREATE OR REPLACE FUNCTION df_jugador_torneo_aiu()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    --
    IF TG_OP = 'INSERT' THEN
        --
        NEW.jgtr_usua   := COALESCE(NEW.jgtr_usua, USER);
        NEW.jgtr_feccre := COALESCE(NEW.jgtr_feccre, CURRENT_TIMESTAMP);
        --
    ELSE
        --
        NEW.jgtr_usua_alt := COALESCE(NEW.jgtr_usua_alt, USER);
        NEW.jgtr_fecalt   := COALESCE(NEW.jgtr_fecalt, CURRENT_TIMESTAMP);
        --
    END IF;
    --
    RETURN NEW;
    --
END;
$BODY$;

ALTER FUNCTION df_jugador_torneo_aiu()
    OWNER TO postgres;

CREATE OR REPLACE TRIGGER d_jugador_torneo_aiu
    AFTER INSERT OR UPDATE 
    ON t_jugador_torneo
    FOR EACH ROW
    EXECUTE FUNCTION df_jugador_torneo_aiu();