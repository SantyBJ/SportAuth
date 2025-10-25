-- Funcion Trigger: df_torneo_aiu()

-- DROP FUNCTION IF EXISTS df_torneo_aiu();

CREATE OR REPLACE FUNCTION df_torneo_aiu()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    --
    IF TG_OP = 'INSERT' THEN
        --
        NEW.trno_usua   := COALESCE(NEW.trno_usua, USER);
        NEW.trno_feccre := COALESCE(NEW.trno_feccre, CURRENT_TIMESTAMP);
        --
    ELSE
        --
        NEW.trno_usua_alt := COALESCE(NEW.trno_usua_alt, USER);
        NEW.trno_fecalt   := COALESCE(NEW.trno_fecalt, CURRENT_TIMESTAMP);
        --
    END IF;
    --
    RETURN NEW;
    --
END;
$BODY$;

ALTER FUNCTION df_torneo_aiu()
    OWNER TO postgres;

CREATE OR REPLACE TRIGGER d_torneo_aiu
    AFTER INSERT OR UPDATE 
    ON t_torneo
    FOR EACH ROW
    EXECUTE FUNCTION df_torneo_aiu();