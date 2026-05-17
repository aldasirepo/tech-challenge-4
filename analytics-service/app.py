import os
import sys
import threading
import json
import uuid
import time
import logging
import boto3
from flask import Flask, jsonify
from dotenv import load_dotenv

# --- OpenTelemetry ---
from opentelemetry import trace, propagate
from otel_setup import setup_otel 
from opentelemetry.instrumentation.flask import FlaskInstrumentor 
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor 

setup_otel("analytics-service")
BotocoreInstrumentor().instrument()
tracer = trace.get_tracer("analytics-service")

# Configura o logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

load_dotenv()

# --- Configuracao ---
AWS_REGION = os.getenv("AWS_REGION")
SQS_QUEUE_URL = os.getenv("AWS_SQS_URL")
DYNAMODB_TABLE_NAME = os.getenv("AWS_DYNAMODB_TABLE")

if not all([AWS_REGION, SQS_QUEUE_URL, DYNAMODB_TABLE_NAME]):
    log.critical("Erro: AWS_REGION, SQS_URL e DYNAMODB_TABLE devem ser definidos.")
    sys.exit(1)

# --- Clientes Boto3 ---
try:
    session = boto3.Session(region_name=AWS_REGION)
    sqs_client = session.client("sqs")
    dynamodb_client = session.client("dynamodb")
    log.info(f"Clientes Boto3 inicializados na regiao {AWS_REGION}")
except Exception as e:
    log.critical(f"Erro ao inicializar o Boto3: {e}")
    sys.exit(1)

def process_message(message):
    """Processa uma mensagem SQS e insere no DynamoDB."""
    try:
        # Extracao de contexto para o rastro distribuido
        attributes = message.get("MessageAttributes", {})
        carrier = {k: v["StringValue"] for k, v in attributes.items()}
        context = propagate.extract(carrier)

        with tracer.start_as_current_span(
            "process_sqs_message",
            context=context,
            kind=trace.SpanKind.CONSUMER,
        ):
            log.info(f"Processando mensagem ID: {message['MessageId']}")
            body = json.loads(message["Body"])
            event_id = str(uuid.uuid4())

            item = {
                "event_id": {"S": event_id},
                "user_id": {"S": body["user_id"]},
                "flag_name": {"S": body["flag_name"]},
                "result": {"BOOL": body["result"]},
                "timestamp": {"S": body["timestamp"]},
            }

            dynamodb_client.put_item(TableName=DYNAMODB_TABLE_NAME, Item=item)
            log.info(f"Evento {event_id} salvo no DynamoDB.")

            sqs_client.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])
    except Exception as e:
        log.error(f"Erro ao processar {message.get('MessageId')}: {e}")

def sqs_worker_loop():
    log.info("Iniciando o worker SQS...")
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=20,
                MessageAttributeNames=['All']
            )
            messages = response.get("Messages", [])
            for message in messages:
                process_message(message)
        except Exception as e:
            log.error(f"Erro no loop SQS: {e}")
            time.sleep(10)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

def start_worker():
    threading.Thread(target=sqs_worker_loop, daemon=True).start()

start_worker()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8005))
    # nosec: B104 silencia o alerta de seguranca do Bandit para o binding 0.0.0.0
    app.run(host="0.0.0.0", port=port, debug=False) # nosec: B104