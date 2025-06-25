import json
import boto3
import os
import csv

def lambda_handler(event, context):
    bucket = os.environ['BUCKET_NAME']
    s3 = boto3.client('s3')

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
            s3_object = s3.get_object(Bucket=bucket, Key=nombre)
            archivo_csv = s3_object['Body'].read().decode('ISO-8859-1').splitlines()
            
            csv_reader = csv.reader(archivo_csv)
            encabezado = next(csv_reader)
            
            filas_corregidas = []
            filas_errores = []

            for fila_num, fila in enumerate(csv_reader, start=2):
                if len(fila) != len(encabezado):
                    filas_errores.append({
                        "fila": fila_num,
                        "contenido": fila,
                        "error": "Número de columnas incorrecto"
                    })
                elif any(not valor for valor in fila):
                    filas_errores.append({
                        "fila": fila_num,
                        "contenido": fila,
                        "error": "Valores faltantes"
                    })
                else:
        
                    filas_corregidas.append(fila)

            archivo_corregido_json = json.dumps(filas_corregidas, indent=2)

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

    resumen_resultados = json.dumps({"resultados": resultado}, indent=2)
    s3.put_object(
        Bucket=bucket,
        Key='resumen_resultados.json',
        Body=resumen_resultados
    )

    return {
        "statusCode": 200,
        "body": resumen_resultados
    }
