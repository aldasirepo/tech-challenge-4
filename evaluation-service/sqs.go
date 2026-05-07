package main

import (
	"context" // Adicionado
	"encoding/json"
	"log"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/sqs"
	"go.opentelemetry.io/otel" // Adicionado
	"go.opentelemetry.io/otel/propagation" // Adicionado
)

type EvaluationEvent struct {
	UserID    string    `json:"user_id"`
	FlagName  string    `json:"flag_name"`
	Result    bool      `json:"result"`
	Timestamp time.Time `json:"timestamp"`
}

// Alterado para receber ctx (context.Context)
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
		return
	}

	// INJECAO DE CONTEXTO: Prepara os atributos da mensagem com o Trace ID
	messageAttributes := make(map[string]*sqs.MessageAttributeValue)
	otel.GetTextMapPropagator().Inject(ctx, propagation.MapEntries(func(k, v string) {
		messageAttributes[k] = &sqs.MessageAttributeValue{
			DataType:    aws.String("String"),
			StringValue: aws.String(v),
		}
	}))

	_, err = a.SqsSvc.SendMessage(&sqs.SendMessageInput{
		MessageBody:       aws.String(string(body)),
		QueueUrl:          aws.String(a.SqsQueueURL),
		MessageAttributes: messageAttributes, // Enviamos os atributos aqui
	})

	if err != nil {
		log.Printf("Erro ao enviar para SQS: %v", err)
	}
}