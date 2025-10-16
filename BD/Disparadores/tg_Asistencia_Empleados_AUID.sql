-- Funcion Trigger: tf_asistencia_empleados_auid()

-- DROP FUNCTION IF EXISTS tf_asistencia_empleados_auid();

CREATE OR REPLACE FUNCTION tf_asistencia_empleados_auid()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
DECLARE
	--
	v_Accion_Antes TEXT;
	v_Accion_Despues TEXT;
	--
BEGIN
	--
    IF TG_OP = 'INSERT' THEN
    	--
		v_Accion_Despues := 'Identif: ' || NEW.Identif
					   || ', Cedula: '  || NEW.Cedula
					   || ', Ingreso: ' || TO_CHAR(NEW.Ingreso, 'YYYY-MM-DD HH:MI AM')
					   || ', Salida: '  || COALESCE(TO_CHAR(NEW.Salida, 'YYYY-MM-DD HH:MI AM'), '')
					   || ', Horas_Ex: '|| COALESCE(TO_CHAR(NEW.Horas_Ex, '99'), '')
					   || ', Usua_Cre: '|| NEW.Usua_Cre
					   || ', Usua_Mod: '|| COALESCE(NEW.Usua_Mod, '')
						;
		--
		INSERT INTO auditoria (
								 Id_Usuario
								,Tabla
								,Accion
								,Info_Antes
								,Info_Desp
								,Fech_Reg
							  )
					   VALUES (
					   			 NEW.Usua_Cre
						   		,'asistencia_empleados'
						   		,'INS'
						        ,'N/A'
						   		,v_Accion_Despues
						        ,CURRENT_TIMESTAMP
					          );
		--
	ELSIF TG_OP = 'UPDATE' THEN
    	--
		v_Accion_Antes :=   'Identif: ' || OLD.Identif
					   || ', Cedula: '  || OLD.Cedula
					   || ', Ingreso: ' || TO_CHAR(OLD.Ingreso, 'YYYY-MM-DD HH:MI AM')
					   || ', Salida: '  || COALESCE(TO_CHAR(OLD.Salida, 'YYYY-MM-DD HH:MI AM'), '')
					   || ', Horas_Ex: '|| COALESCE(TO_CHAR(OLD.Horas_Ex, '99'), '')
					   || ', Usua_Cre: '|| OLD.Usua_Cre
					   || ', Usua_Mod: '|| COALESCE(OLD.Usua_Mod, '')
					   ;
		--
		v_Accion_Despues := 'Identif: ' || NEW.Identif
					   || ', Cedula: '  || NEW.Cedula
					   || ', Ingreso: ' || TO_CHAR(NEW.Ingreso, 'YYYY-MM-DD HH:MI AM')
					   || ', Salida: '  || TO_CHAR(NEW.Salida, 'YYYY-MM-DD HH:MI AM')
					   || ', Horas_Ex: '|| COALESCE(TO_CHAR(NEW.Horas_Ex, '99'), '')
					   || ', Usua_Cre: '|| NEW.Usua_Cre
					   || ', Usua_Mod: '|| NEW.Usua_Mod
					   ;
		--
		INSERT INTO auditoria (
								 Id_Usuario
								,Tabla
								,Accion
								,Info_Antes
								,Info_Desp
								,Fech_Reg
							  )
					   VALUES (
					   			 NEW.Usua_Mod
						   		,'asistencia_empleados'
						   		,'UPD'
						        ,v_Accion_Antes
						   		,v_Accion_Despues
						        ,CURRENT_TIMESTAMP
					          );
		--
	ELSE
    	--
		v_Accion_Antes := 'Identif: ' || OLD.Identif
					 || ', Cedula: '  || OLD.Cedula
					 || ', Ingreso: ' || TO_CHAR(OLD.Ingreso, 'YYYY-MM-DD HH:MI AM')
					 || ', Salida: '  || COALESCE(TO_CHAR(OLD.Salida, 'YYYY-MM-DD HH:MI AM'), '')
					 || ', Horas_Ex: '|| COALESCE(TO_CHAR(OLD.Horas_Ex, '99'), '')
					 || ', Usua_Cre: '|| OLD.Usua_Cre
					 || ', Usua_Mod: '|| COALESCE(OLD.Usua_Mod, '')
					   ;
		--
		INSERT INTO auditoria (
								 Id_Usuario
								,Tabla
								,Accion
								,Info_Antes
								,Info_Desp
								,Fech_Reg
							  )
					   VALUES (
					   			 COALESCE(OLD.Usua_Mod, OLD.Usua_Cre)
						   		,'asistencia_empleados'
						   		,'DEL'
						        ,v_Accion_Antes
						   		,'N/A'
						        ,CURRENT_TIMESTAMP
					          );
		--
	END IF;
	--
    RETURN NEW;
END;
$BODY$;

ALTER FUNCTION tf_asistencia_empleados_auid()
    OWNER TO postgres;

CREATE OR REPLACE TRIGGER tg_asistencia_empleados_auid
    AFTER INSERT OR DELETE OR UPDATE 
    ON asistencia_empleados
    FOR EACH ROW
    EXECUTE FUNCTION tf_asistencia_empleados_auid();