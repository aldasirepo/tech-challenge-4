package main

import (
	"context"
	"encoding/json"
	"log"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/sqs"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/propagation"
	goOtelTrace "go.opentelemetry.io/otel/trace"
)

type EvaluationEvent struct {
	UserID    string    `json:"user_id"`
	FlagName  string    `json:"flag_name"`
	Result    bool      `json:"result"`
	Timestamp time.Time `json:"timestamp"`
}

func (a *App) sendEvaluationEvent(ctx context.Context, userID, flagName string, result bool) {
	if a.SqsSvc == nil || a.SqsQueueURL == "" {
		log.Printf("[SQS_DISABLED] Evento: User '%s', Flag '%s', Result '%t'", userID, flagName, result)
		return
	}

	event := EvaluationEvent{
		UserID:    userID,
		FlagName:  flagName,
		Result:    result,
		Timestamp: time.Now().UTC(),
	}

	body, err := json.Marshal(event)
	if err != nil {
		log.Printf("Erro ao serializar evento SQS: %v", err)
		return
	}

	// Cria um span explícito para a publicação no SQS
	tracer := otel.Tracer("evaluation-service")
	pubCtx, pubSpan := tracer.Start(ctx, "sqs.publish", goOtelTrace.WithSpanKind(goOtelTrace.SpanKindProducer))
	
	// Adiciona convenções semânticas para o Datadog conectar a fila
	pubSpan.SetAttributes(
		attribute.String("messaging.system", "aws_sqs"),
		attribute.String("messaging.destination.name", a.SqsQueueURL),
		attribute.String("messaging.operation", "publish"),
	)
	defer pubSpan.End()

	// Injeta o rastro (trace) nos atributos da mensagem usando MapCarrier
	messageAttributes := make(map[string]*sqs.MessageAttributeValue)
	carrier := make(map[string]string)
	otel.GetTextMapPropagator().Inject(pubCtx, propagation.MapCarrier(carrier))

	for k, v := range carrier {
		messageAttributes[k] = &sqs.MessageAttributeValue{
			DataType:    aws.String("String"),
			StringValue: aws.String(v),
		}
	}

	_, err = a.SqsSvc.SendMessage(&sqs.SendMessageInput{
		MessageBody:       aws.String(string(body)),
		QueueUrl:          aws.String(a.SqsQueueURL),
		MessageAttributes: messageAttributes,
	})

	if err != nil {
		log.Printf("Erro ao enviar mensagem para SQS: %v", err)
	}
}