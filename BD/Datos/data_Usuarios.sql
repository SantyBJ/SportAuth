--
-- Datos de la tabla: Usuarios
--

INSERT INTO Usuarios(
    nombre
   ,contrasena
   ,permisos
) VALUES (
	'egforero'
   ,crypt('LaZorrErik123.', gen_salt('bf'))
   ,ARRAY['IE']),
   
   ('dojimenez'
   ,crypt('Stick.Man456', gen_salt('bf'))
   ,ARRAY['IE']),
   
   ('aateheran'
   ,crypt('ElBJx2.789', gen_salt('bf'))
   ,ARRAY['IE', 'GR']);