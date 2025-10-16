--
-- Datos de la tabla: Empleados
--

INSERT INTO Empleados(
	cedula
   ,nombres
   ,apellidos
   ,fecha_ingreso
   ,cargo
   ,area
   ,horas_diarias
   ,salario_base
   ,nacimiento
   ,direccion
   ,estado_civil
   ,hijos
   ,email
) VALUES 
	( 123456789
	 ,'Juan Pablo'
	 ,'Perez Mendieta'
	 ,(DATE '2022-01-15')
	 ,'Desarrollador Junior'
	 ,'TEC'
	 ,ARRAY[10,10,10,10,8]
	 ,1200000
	 ,(DATE '1990-05-20')
	 ,'Calle 123'
	 ,'S'
	 ,0
	 ,'juan.perez@email.com'),
	 
	( 987654321
	 ,'Maria Antonia'
	 ,'Gomez Diaz'
	 ,(DATE '2022-03-13')
	 ,'Contadora'
	 ,'FIN'
	 ,ARRAY[10,10,10,10,10]
	 ,1300000
	 ,(DATE '1985-08-13')
	 ,'Avenida 456'
	 ,'C'
	 ,2
	 ,'maria.gomez@email.com'),
	 
	( 555444333
	 ,'Pedro Andres'
	 ,'Rodriguez Gamboa'
	 ,(DATE '2022-02-15')
	 ,'Diseñador'
	 ,'DIS'
	 ,ARRAY[10,10,10,8,10]
	 ,1170000
	 ,(DATE '1992-11-16')
	 ,'Carrera 789'
	 ,'S'
	 ,1
	 ,'pedro.rodriguez@email.com'),
	 
	( 111222333
	 ,'Ana Maria'
	 ,'Lopez Quintero'
	 ,(DATE '2021-04-25')
	 ,'Gerente'
	 ,'GGN'
	 ,ARRAY[10,10,10,10,12]
	 ,4200000
	 ,(DATE '1980-03-15')
	 ,'Calle Principal'
	 ,'C'
	 ,3
	 ,'ana.lopez@email.com'),
	 
	( 999888777
	 ,'Carlos'
	 ,'Gutierrez Figueroa'
	 ,(DATE '2022-03-20')
	 ,'Analista de Requerimientos'
	 ,'TEC'
	 ,ARRAY[8,8,10,10,8,4]
	 ,1170000
	 ,(DATE '1993-07-25')
	 ,'Avenida Secundaria'
	 ,'S'
	 ,0
	 ,'carlos.gutierrez@email.com'),
	 
	( 444555666
	 ,'Laura Daniela'
	 ,'Martinez Mendez'
	 ,(DATE '2022-01-24')
	 ,'Auxiliar de RH'
	 ,'RHG'
	 ,ARRAY[8,8,8,8,8,8]
	 ,2360000
	 ,(DATE '1988-09-30')
	 ,'Calle 567'
	 ,'U'
	 ,2
	 ,'laura.martinez@email.com'),
	 
	( 777666555
	 ,'Daniel Felipe'
	 ,'Hernandez Castellanos'
	 ,(DATE '2022-02-15')
	 ,'Auxiliar de Infraestructura'
	 ,'TEC'
	 ,ARRAY[10,10,10,10,8]
	 ,1170000
	 ,(DATE '1991-04-29')
	 ,'Calle Nueva'
	 ,'D'
	 ,1
	 ,'daniel.hernandez@email.com'),
	
	( 666777888
	 ,'Sara Sofia'
	 ,'Cruz Gualteros'
	 ,(DATE '2022-05-19')
	 ,'Analista de Requerimientos'
	 ,'TEC'
	 ,ARRAY[8,10,12,10,10]
	 ,2455000
	 ,(DATE '1987-12-22')
	 ,'Avenida Principal'
	 ,'P'
	 ,2
	 ,'sofia.cruz@email.com'),
	
	( 333222111
	 ,'Javier Ignacio'
	 ,'Ramirez Soler'
	 ,(DATE '2022-03-25')
	 ,'Marketing'
	 ,'PUB'
	 ,ARRAY[10,10,10,10,8]
	 ,2265000
	 ,(DATE '1994-06-18')
	 ,'Carrera 101'
	 ,'U'
	 ,0
	 ,'javier.ramirez@email.com'),
	
	( 888999000
	 ,'Isabel'
	 ,'Perez Ramirez'
	 ,(DATE '2022-04-20')
	 ,'Desarrollador Profesional'
	 ,'TEC'
	 ,ARRAY[10,10,10,10,8]
	 ,3560000
	 ,(DATE '1995-02-28')
	 ,'Calle Central'
	 ,'C'
	 ,1
	 ,'isabel.perez@email.com'),
	
	( 222333444
	 ,'Leonardo Jose'
	 ,'Garcia Maldonado'
	 ,(DATE '2022-01-16')
	 ,'Desarrollador Senior'
	 ,'SPT'
	 ,ARRAY[10,10,10,10,8]
	 ,5706000
	 ,(DATE '1995-02-28')
	 ,'Avenida Nueva'
	 ,'U'
	 ,0
	 ,'jose.garcia@email.com'),
	
	( 111000222
	 ,'Monica Elizabeth'
	 ,'Fernandez Velez'
	 ,(DATE '2022-02-25')
	 ,'Gerente Financiero'
	 ,'FIN'
	 ,ARRAY[10,11,9,9,9]
	 ,6230000
	 ,(DATE '1986-07-01')
	 ,'Calle 456'
	 ,'D'
	 ,2
	 ,'monica.fernandez@email.com'),
	
	( 777888999
	 ,'Josue Raul'
	 ,'Lopez Avendaño'
	 ,(DATE '2022-05-30')
	 ,'Diseñador de Mockups'
	 ,'DIS'
	 ,ARRAY[10,10,10,10,8]
	 ,3760000
	 ,(DATE '1990-12-10')
	 ,'Carrera 789'
	 ,'V'
	 ,1
	 ,'raul.lopez@email.com'),
	
	( 555666777
	 ,'Natalia Alejandra'
	 ,'Torres Nieto'
	 ,(DATE '2021-02-15')
	 ,'CEO'
	 ,'GGN'
	 ,ARRAY[12,12,12,12,12]
	 ,10200000
	 ,(DATE '1981-05-20')
	 ,'Avenida Principal'
	 ,'S'
	 ,3
	 ,'natalia.torres@email.com'),
	
	( 333444555
	 ,'Juan Alejandro'
	 ,'Sanchez Tovar'
	 ,(DATE '2022-03-25')
	 ,'Desarrollador Senior'
	 ,'TEC'
	 ,ARRAY[8,8,8,8,8,8]
	 ,5706000
	 ,(DATE '1992-09-15')
	 ,'Calle Secundaria'
	 ,'S'
	 ,0
	 ,'alejandro.sanchez@email.com');