import mysql.connector
import numpy as np

def obtener_conexion_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="inventario_db"
    )

def autenticar_usuario(email, password):
    conexion = obtener_conexion_db()
    cursor = conexion.cursor()
    query = "SELECT * FROM usuarios WHERE email = %s AND password = %s"
    cursor.execute(query, (email, password))
    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()
    
    if resultado:
        user = {
            'id': resultado[0],
            'nombre': resultado[1],
            'apellido': resultado[2],
            'email': resultado[3],
            'telefono': resultado[4],
            'rol': resultado[5],
            'password': resultado[6],
            'rostro_descriptor': resultado[7]
        }
        return user
    return None

def obtener_usuarios(email):
    try:
        conexion = obtener_conexion_db()
        cursor = conexion.cursor(dictionary=True)
        query = "SELECT * FROM usuarios WHERE email = %s"
        cursor.execute(query, (email,))
        usuario = cursor.fetchone()
        cursor.close()
        conexion.close()
        return usuario
    except Exception as e:
        print(f"Error al obtener usuario: {e}")
        return None

def obtener_rol(usuario):
    conexion = obtener_conexion_db()
    cursor = conexion.cursor()
    query = "SELECT rol FROM usuarios WHERE email = %s"
    cursor.execute(query, (usuario,))
    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()
    return resultado[0] if resultado else None

def obtener_productos():
    try:
        conexion = obtener_conexion_db()
        cursor = conexion.cursor(dictionary=True)
        query = """
        SELECT p.nombre AS producto_nombre, 
               p.precio, 
               pr.nombre AS proveedor_nombre
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        """
        cursor.execute(query)
        productos = cursor.fetchall()

        print(f"Productos obtenidos: {productos}")
        
        cursor.close()
        conexion.close()
        return productos
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return []


def obtener_descriptor_rostro(email):
    if not isinstance(email, str):
        raise TypeError("El parámetro 'email' debe ser una cadena de texto.")
    
    conexion = obtener_conexion_db()
    cursor = conexion.cursor()
    query = "SELECT rostro_descriptor FROM usuarios WHERE email = %s"
    cursor.execute(query, (email,))
    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()
    if resultado and resultado[0]:
        return np.frombuffer(resultado[0], dtype=np.float64)
    return None

def verificar_rostro(descriptor):
    conexion = obtener_conexion_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT email, rostro_descriptor FROM usuarios")
    rostros = cursor.fetchall()
    
    descriptor = np.frombuffer(descriptor, dtype=np.float64)
    
    for email, db_descriptor in rostros:
        if db_descriptor is None:
            continue
        
        db_descriptor = np.frombuffer(db_descriptor, dtype=np.float64)
        if compare_faces(descriptor, db_descriptor):
            cursor.execute("SELECT rol FROM usuarios WHERE email = %s", (email,))
            rol = cursor.fetchone()[0]
            cursor.close()
            conexion.close()
            return {'email': email, 'rol': rol}
    
    cursor.close()
    conexion.close()
    return None

def compare_faces(descriptor1, descriptor2, tolerance=0.6):
    descriptor1 = np.array(descriptor1, dtype=np.float64)
    descriptor2 = np.array(descriptor2, dtype=np.float64)
    distance = np.linalg.norm(descriptor1 - descriptor2)
    return distance < tolerance

def actualizar_datos_db(email, nombre, apellido, telefono, rol, password, rostro_descriptor):
    try:
        conexion = obtener_conexion_db()
        cursor = conexion.cursor()
        
        if rostro_descriptor is not None:
            rostro_descriptor = rostro_descriptor.tobytes()
        else:
            rostro_descriptor = None
        
        query = """
            UPDATE usuarios 
            SET nombre = %s, apellido = %s, telefono = %s, rol = %s, password = %s, rostro_descriptor = %s 
            WHERE email = %s
        """
        cursor.execute(query, (nombre, apellido, telefono, rol, password, rostro_descriptor, email))
        conexion.commit()
        
    except Exception as e:
        print(f"Error al actualizar datos: {str(e)}")
    
    finally:
        cursor.close()
        conexion.close()

def crear_cliente(nombre, apellido, email, telefono, rol, password, rostro_descriptor):
    conexion = obtener_conexion_db()
    cursor = conexion.cursor()
    
    query = "SELECT COUNT(*) FROM usuarios WHERE email = %s"
    cursor.execute(query, (email,))
    if cursor.fetchone()[0] > 0:
        cursor.close()
        conexion.close()
        raise ValueError("El correo electrónico ya está registrado.")
    
    if rostro_descriptor is not None:
        rostro_descriptor = rostro_descriptor.tobytes()
    
    query = """
        INSERT INTO usuarios (nombre, apellido, email, telefono, rol, password, rostro_descriptor) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (nombre, apellido, email, telefono, rol, password, rostro_descriptor))
    
    conexion.commit()
    cursor.close()
    conexion.close()
