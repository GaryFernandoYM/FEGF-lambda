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
            "archivo_corregido": f"corregido_{nombre}",
            "archivo_con_errores": f"errores_{nombre}",
            "filas_exitosas": [],
            "filas_con_error": []
        }

        try:
            # Obtener el archivo CSV desde S3
            s3_object = s3.get_object(Bucket=bucket, Key=nombre)
            archivo_csv = s3_object['Body'].read().decode('utf-8').splitlines()
            
            # Leer el archivo CSV línea por línea
            csv_reader = csv.reader(archivo_csv)
            encabezado = next(csv_reader)  # Obtener el encabezado (si lo tiene)
            
            filas_corregidas = []
            filas_errores = []

            for fila_num, fila in enumerate(csv_reader, start=2):  # Empezamos desde la fila 2 (por el encabezado)
                if len(fila) != len(encabezado):  # Si la fila tiene un número diferente de columnas, es incorrecta
                    filas_errores.append({
                        "fila": fila_num,
                        "contenido": fila,
                        "error": "Número de columnas incorrecto"
                    })
                else:
                    # Validamos si hay valores faltantes
                    if any(not valor for valor in fila):  # Si hay algún campo vacío
                        filas_errores.append({
                            "fila": fila_num,
                            "contenido": fila,
                            "error": "Valores faltantes"
                        })
                    else:
                        # Si la fila está bien, la agregamos a las filas corregidas
                        filas_corregidas.append(fila)

            # Escribir archivo corregido y con errores en memoria
            output_corregido = io.StringIO()
            output_errores = io.StringIO()
            writer_corregido = csv.writer(output_corregido)
            writer_errores = csv.writer(output_errores)

            # Escribir encabezado
            writer_corregido.writerow(encabezado)
            writer_errores.writerow(encabezado)

            # Escribir las filas corregidas y con errores
            writer_corregido.writerows(filas_corregidas)
            writer_errores.writerows(filas_errores)

            # Subir archivos corregidos y con errores a S3
            s3.put_object(
                Bucket=bucket,
                Key=f"corregidos/{archivo_procesado['archivo_corregido']}",
                Body=output_corregido.getvalue()
            )

            s3.put_object(
                Bucket=bucket,
                Key=f"errores/{archivo_procesado['archivo_con_errores']}",
                Body=output_errores.getvalue()
            )

            archivo_procesado["filas_exitosas"] = filas_corregidas
            archivo_procesado["filas_con_error"] = filas_errores

        except Exception as e:
            archivo_procesado["estado"] = "fallido"
            archivo_procesado["error"] = str(e)
        
        resultado.append(archivo_procesado)

    return {
        "statusCode": 200,
        "body": json.dumps(resultado, indent=2)  # Formato JSON bonito
    }
