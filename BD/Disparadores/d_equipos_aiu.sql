-- Funcion Trigger: df_equipos_aiu()

-- DROP FUNCTION IF EXISTS df_equipos_aiu();

CREATE OR REPLACE FUNCTION df_equipos_aiu()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    --
    IF TG_OP = 'INSERT' THEN
        --
        NEW.eqpo_usua   := COALESCE(NEW.eqpo_usua, USER);
        NEW.eqpo_feccre := COALESCE(NEW.eqpo_feccre, CURRENT_TIMESTAMP);
        --
    ELSE
        --
        NEW.eqpo_usua_alt := COALESCE(NEW.eqpo_usua_alt, USER);
        NEW.eqpo_fecalt   := COALESCE(NEW.eqpo_fecalt, CURRENT_TIMESTAMP);
        --
    END IF;
    --
    IF NOT NEW.eqpo_estado THEN
        --
        UPDATE t_equipo_Torneo
           SET eqtn_estado = FALSE
         WHERE eqtn_equipo = NEW.eqpo_eqpo;
        --
    END IF;
    --
    RETURN NEW;
    --
END;
$BODY$;

ALTER FUNCTION df_equipos_aiu()
    OWNER TO postgres;

CREATE OR REPLACE TRIGGER d_equipos_aiu
    AFTER INSERT OR UPDATE 
    ON t_Equipos
    FOR EACH ROW
    EXECUTE FUNCTION df_equipos_aiu();