import csv
import mysql.connector
from mysql.connector import Error

def ejecutar_etl():
    try:
        # 1. Conexión a la base de datos
        conexion = mysql.connector.connect(
            host='localhost',
            user='root',
            password='19067',
            database='saludMedica'
        )
        
        if conexion.is_connected():
            cursor = conexion.cursor()
            
            # Crear la tabla automáticamente si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facturacion_citas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    paciente VARCHAR(100),
                    especialidad VARCHAR(100),
                    costo_base DECIMAL(10,2),
                    descuento DECIMAL(10,2),
                    igv DECIMAL(10,2),
                    total DECIMAL(10,2)
                )
            """)

            registros_exitosos = 0
            registros_descartados = 0

            # 2. Transformación y Limpieza de Datos
            with open('citas_dia.csv', mode='r', encoding='utf-8') as archivo_csv:
                lector_csv = csv.DictReader(archivo_csv)
                
                for fila in lector_csv:
                    try:
                        # Extraer limpiando espacios en blanco a los lados
                        paciente = fila['paciente'].strip() if fila['paciente'] else ''
                        especialidad = fila['especialidad'].strip() if fila['especialidad'] else ''
                        costo_base_str = fila['costo_base'].strip() if fila['costo_base'] else ''
                        
                        # Validación: Descartar si el campo especialidad está vacío
                        if not especialidad:
                            registros_descartados += 1
                            continue
                            
                        # Intentar convertir el costo a número (esto falla con "ErrorTipografico")
                        costo_base = float(costo_base_str)
                        
                        # Validación: Descartar si el costo_base es menor o igual a 0
                        if costo_base <= 0:
                            registros_descartados += 1
                            continue
                            
                        # --- LÓGICA DE NEGOCIO ---
                        descuento = 0.0
                        # Descuento del 10% solo para Pediatría
                        if especialidad.lower() == 'pediatria':
                            descuento = costo_base * 0.10
                            
                        costo_con_descuento = costo_base - descuento
                        # IGV del 18% sobre el costo con descuento
                        igv = costo_con_descuento * 0.18
                        # Total a pagar
                        total = costo_con_descuento + igv
                        
                        # 3. Carga de datos (Load)
                        cursor.execute("""
                            INSERT INTO facturacion_citas 
                            (paciente, especialidad, costo_base, descuento, igv, total)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (paciente, especialidad, costo_base, descuento, igv, total))
                        
                        registros_exitosos += 1
                        
                    except ValueError:
                        # Captura los errores al intentar convertir texto a float (ej. "ErrorTipografico")
                        registros_descartados += 1
                    except Exception as e:
                        # Captura cualquier otra anomalía imprevista en la fila
                        registros_descartados += 1
            
            # Confirmar e insertar los cambios reales en MySQL
            conexion.commit()
            
            # Reporte final en consola
            print("\n--- RESUMEN DE EJECUCIÓN ETL ---")
            print(f"Total de registros procesados con éxito: {registros_exitosos}")
            print(f"Total de registros descartados por errores: {registros_descartados}")
            print("--------------------------------")

    except Error as e:
        print(f"Error al interactuar con MySQL: {e}")
    finally:
        # Asegurarse de cerrar la conexión siempre
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

if __name__ == '__main__':
    ejecutar_etl()