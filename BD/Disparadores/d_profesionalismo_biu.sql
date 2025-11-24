-- Funcion Trigger: df_profesionalismo_aiu()

-- DROP FUNCTION IF EXISTS df_profesionalismo_aiu();

CREATE OR REPLACE FUNCTION df_profesionalismo_aiu()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    --
    IF TG_OP = 'INSERT' THEN
        --
        NEW.prfm_usua   := COALESCE(NEW.prfm_usua, USER);
        NEW.prfm_feccre := COALESCE(NEW.prfm_feccre, CURRENT_TIMESTAMP);
        --
    ELSE
        --
        NEW.prfm_usua_alt := COALESCE(NEW.prfm_usua_alt, USER);
        NEW.prfm_fecalt   := COALESCE(NEW.prfm_fecalt  , CURRENT_TIMESTAMP);
        --
    END IF;
    --
    RETURN NEW;
    --
END;
$BODY$;

ALTER FUNCTION df_profesionalismo_aiu()
    OWNER TO postgres;

CREATE OR REPLACE TRIGGER d_profesionalismo_aiu
    AFTER INSERT OR UPDATE 
    ON t_profesionalismo
    FOR EACH ROW
    EXECUTE FUNCTION df_profesionalismo_aiu();