import json
import boto3
import os
import csv

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
            "archivo_corregido": f"{nombre.replace('.csv', '.json')}",
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

            for fila_num, fila in enumerate(csv_reader, start=2):  # Comenzamos desde la fila 2 (después del encabezado)
                # Validamos si la fila tiene el número correcto de columnas
                if len(fila) != len(encabezado):
                    filas_errores.append({
                        "fila": fila_num,
                        "contenido": fila,
                        "error": "Número de columnas incorrecto"
                    })
                # Validamos si hay valores faltantes en la fila
                elif any(not valor for valor in fila):
                    filas_errores.append({
                        "fila": fila_num,
                        "contenido": fila,
                        "error": "Valores faltantes"
                    })
                else:
                    # Si la fila está correcta, la agregamos a las filas corregidas
                    filas_corregidas.append(fila)

            # Convertir las filas corregidas a JSON
            archivo_corregido_json = json.dumps(filas_corregidas, indent=2)

            # Subir el archivo corregido a S3 en formato JSON (con el mismo nombre pero extensión .json)
            s3.put_object(
                Bucket=bucket,
                Key=f"{archivo_procesado['archivo_corregido']}",
                Body=archivo_corregido_json
            )

            archivo_procesado["filas_exitosas"] = filas_corregidas
            archivo_procesado["filas_con_error"] = filas_errores

        except Exception as e:
            archivo_procesado["estado"] = "fallido"
            archivo_procesado["error"] = str(e)
        
        resultado.append(archivo_procesado)

    # Guardar el resumen final de los resultados en un archivo JSON
    resumen_resultados = json.dumps({"resultados": resultado}, indent=2)
    s3.put_object(
        Bucket=bucket,
        Key='resumen_resultados.json',  # Nombre del archivo resumen
        Body=resumen_resultados
    )

    return {
        "statusCode": 200,
        "body": resumen_resultados  # Solo el resumen del estado
    }
