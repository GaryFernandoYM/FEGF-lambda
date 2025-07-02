import json
import boto3
import os
import csv
from datetime import datetime

def lambda_handler(event, context):
    source_bucket = os.environ['SOURCE_BUCKET']
    target_bucket = os.environ['TARGET_BUCKET']
    s3 = boto3.client('s3')

    archivos = s3.list_objects_v2(Bucket=source_bucket).get('Contents', [])
    resultado = []

    for archivo in archivos:
        nombre = archivo['Key']
        if not nombre.lower().endswith('.csv'):
            continue

        archivo_procesado = {
            "archivo": nombre,
            "estado": "procesado",
            "archivo_corregido": nombre.replace('.csv', '.json'),
            "filas_exitosas": [],
            "filas_con_error": []
        }

        try:
            s3_object = s3.get_object(Bucket=source_bucket, Key=nombre)
            archivo_csv = s3_object['Body'].read().decode('ISO-8859-1').splitlines()
            csv_reader = csv.DictReader(archivo_csv)

            filas_corregidas = []
            filas_errores = []

            for num_fila, fila in enumerate(csv_reader, start=2):
                errores = []

                try:
                    if not fila['id']:
                        errores.append("ID vacío")

                    if fila['date']:
                        try:
                            datetime.strptime(fila['date'][:8], '%Y%m%d')
                        except:
                            errores.append("Fecha inválida")
                    else:
                        errores.append("Fecha vacía")

                    if float(fila['price']) <= 0:
                        errores.append("Precio inválido")

                    if not (1 <= int(fila['bedrooms']) < 15):
                        errores.append("Número de dormitorios inválido")

                    if not (0.5 <= float(fila['bathrooms']) < 10):
                        errores.append("Número de baños inválido")

                    if int(fila['sqft_living']) <= 100:
                        errores.append("Área habitable inválida")

                    if int(fila['sqft_lot']) <= 0:
                        errores.append("Área del lote inválida")

                    if not (1 <= float(fila['floors']) <= 4):
                        errores.append("Número de pisos inválido")

                    if int(fila['waterfront']) not in (0, 1):
                        errores.append("Valor de waterfront inválido")

                    if not (0 <= int(fila['view']) <= 4):
                        errores.append("Valor de vista inválido")

                    if not (1 <= int(fila['condition']) <= 5):
                        errores.append("Condición inválida")

                    if not (1 <= int(fila['grade']) <= 13):
                        errores.append("Grado inválido")

                    if int(fila['sqft_above']) > int(fila['sqft_living']):
                        errores.append("Área sobre terreno > área habitable")

                    if int(fila['sqft_basement']) > int(fila['sqft_living']):
                        errores.append("Área de sótano > área habitable")

                    if not (1900 <= int(fila['yr_built']) <= 2025):
                        errores.append("Año de construcción inválido")

                    if int(fila['yr_renovated']) not in (0,) and int(fila['yr_renovated']) < int(fila['yr_built']):
                        errores.append("Renovación antes del año de construcción")

                    if len(fila['zipcode']) != 5:
                        errores.append("Código postal inválido")

                    if not (47.1 <= float(fila['lat']) <= 47.8):
                        errores.append("Latitud fuera de rango")

                    if not (-122.5 <= float(fila['long']) <= -121.3):
                        errores.append("Longitud fuera de rango")

                    if int(fila['sqft_living15']) <= 0 or int(fila['sqft_lot15']) <= 0:
                        errores.append("Valores comparativos de tamaño inválidos")

                except Exception as e:
                    errores.append(f"Error inesperado: {str(e)}")

                if errores:
                    filas_errores.append({
                        "fila": num_fila,
                        "contenido": fila,
                        "errores": errores
                    })
                else:
                    filas_corregidas.append(fila)

            archivo_corregido_json = json.dumps(filas_corregidas, indent=2)

            s3.put_object(
                Bucket=target_bucket,
                Key=archivo_procesado["archivo_corregido"],
                Body=archivo_corregido_json
            )

            archivo_procesado["filas_exitosas"] = filas_corregidas
            archivo_procesado["filas_con_error"] = filas_errores

        except Exception as e:
            archivo_procesado["estado"] = "fallido"
            archivo_procesado["error"] = str(e)

        resultado.append(archivo_procesado)
    return {
        "statusCode": 200,
        "body": json.dumps(resultado, indent=2)
    }
