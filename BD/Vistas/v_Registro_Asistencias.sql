--
-- Vista: v_Registro_Asistencias
--

CREATE OR REPLACE VIEW v_Registro_Asistencias AS
	SELECT Emp.cedula 						    AS Cedula
		  ,(Emp.Nombres || ' ' ||Emp.Apellidos) AS Nombre_Completo
		  ,Emp.Cargo 							AS Cargo
		  ,Emp.Area								AS Area
		  ,As_Emp.Ingreso						AS Ingreso
		  ,As_Emp.Salida						AS Salida
		  ,As_Emp.Horas_Ex						AS Horas_Extra
	  FROM Asistencia_Empleados As_Emp
	  JOIN Empleados            Emp
	    ON As_Emp.cedula = Emp.cedula
		;
		
COMMENT ON VIEW   v_Registro_Asistencias                 IS 'Consulta que lleva el registro detallado de las asistencias de los empleados';
COMMENT ON COLUMN v_Registro_Asistencias.Cedula          IS 'Cedula del empleado';
COMMENT ON COLUMN v_Registro_Asistencias.Nombre_Completo IS 'Nombre completo del empleado';
COMMENT ON COLUMN v_Registro_Asistencias.Cargo           IS 'Cargo en la empresa';
COMMENT ON COLUMN v_Registro_Asistencias.Area            IS 'Area en la que opera';
COMMENT ON COLUMN v_Registro_Asistencias.Ingreso         IS 'Fecha de hora de ingreso del empleado en el registro';
COMMENT ON COLUMN v_Registro_Asistencias.Salida          IS 'Fecha de hora de salida del empleado en el registro';
COMMENT ON COLUMN v_Registro_Asistencias.Horas_Extra     IS 'Horas Extra si llega a tener';