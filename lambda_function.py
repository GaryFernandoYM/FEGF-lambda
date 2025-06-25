import json
import boto3
import os
import csv
import io

def lambda_handler(event, context):
    bucket = os.environ['BUCKET_NAME']
    s3 = boto3.client('s3')

    # Lista de archivos en el bucket
    archivos = s3.list_objects_v2(Bucket=bucket).get('Contents', [])

    resultado = []

    for archivo in archivos:
        nombre = archivo['Key']
        archivo_procesado = {
            "archivo": nombre,
            "estado": "procesado",
            "archivo_corregido": f"corregido_{nombre.replace('.csv', '.json')}",
            "archivo_con_errores": f"errores_{nombre.replace('.csv', '.json')}",
            "filas_exitosas": [],
            "filas_con_error": []
        }

        try:
            # Obtener el archivo CSV desde S3 con codificación ISO-8859-1
            s3_object = s3.get_object(Bucket=bucket, Key=nombre)
            archivo_csv = s3_object['Body'].read().decode('ISO-8859-1').splitlines()
            
            # Leer el archivo CSV línea por línea
            csv_reader = csv.reader(archivo_csv)
            encabezado = next(csv_reader)  # Obtener el encabezado (si lo tiene)
            
            filas_corregidas = []
            filas_errores = []

            fragmento_size = 2000  # Definir el tamaño de fragmento (2,000 filas)
            filas = []
            fila_num = 2  # Comenzamos desde la fila 2 (después del encabezado)

            for fila in csv_reader:
                if len(filas) >= fragmento_size:
                    # Procesar el fragmento actual (2,000 filas)
                    for f in filas:
                        if len(f) != len(encabezado):
                            filas_errores.append({"fila": fila_num, "contenido": f, "error": "Número de columnas incorrecto"})
                        elif any(not valor for valor in f):
                            filas_errores.append({"fila": fila_num, "contenido": f, "error": "Valores faltantes"})
                        else:
                            filas_corregidas.append(f)
                        fila_num += 1
                    
                    # Limpiar la lista de filas para el siguiente fragmento
                    filas = []

                filas.append(fila)

            # Procesar el último fragmento si tiene menos de 2,000 filas
            if filas:
                for f in filas:
                    if len(f) != len(encabezado):
                        filas_errores.append({"fila": fila_num, "contenido": f, "error": "Número de columnas incorrecto"})
                    elif any(not valor for valor in f):
                        filas_errores.append({"fila": fila_num, "contenido": f, "error": "Valores faltantes"})
                    else:
                        filas_corregidas.append(f)
                    fila_num += 1

            # Convertir las filas corregidas y con errores a JSON y subir a S3
            archivo_corregido_json = json.dumps(filas_corregidas, indent=2)
            archivo_errores_json = json.dumps(filas_errores, indent=2)

            # Subir archivos corregidos y con errores a S3 en formato JSON
            s3.put_object(
                Bucket=bucket,
                Key=f"corregidos/{archivo_procesado['archivo_corregido']}",
                Body=archivo_corregido_json
            )

            s3.put_object(
                Bucket=bucket,
                Key=f"errores/{archivo_procesado['archivo_con_errores']}",
                Body=archivo_errores_json
            )

            archivo_procesado["filas_exitosas"] = filas_corregidas
            archivo_procesado["filas_con_error"] = filas_errores

        except Exception as e:
            archivo_procesado["estado"] = "fallido"
            archivo_procesado["error"] = str(e)
        
        resultado.append(archivo_procesado)

    # Solo devolver un resumen con los nombres de los archivos y su estado
    return {
        "statusCode": 200,
        "body": json.dumps({"resultados": resultado}, indent=2)  # Solo el resumen del estado
    }
