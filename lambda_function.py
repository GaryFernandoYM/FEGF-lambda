import json
import boto3
import os

def lambda_handler(event, context):
    bucket = os.environ['BUCKET_NAME']
    s3 = boto3.client('s3')

    resultado = []

    archivos = s3.list_objects_v2(Bucket=bucket).get('Contents', [])

    for archivo in archivos:
        nombre = archivo['Key']
        try:
            contenido = s3.get_object(Bucket=bucket, Key=nombre)['Body'].read().decode('utf-8')
        except:
            contenido = "[No se pudo leer]"

        resultado.append({
            "archivo": nombre,
            "contenido": contenido[:300]
        })

    return {
        "statusCode": 200,
        "body": json.dumps(resultado)
    }
