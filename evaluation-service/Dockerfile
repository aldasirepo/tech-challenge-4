# Etapa 1: Build do Go
FROM golang:1.25-alpine AS builder

WORKDIR /app

# Copia arquivos de dependências
COPY go.mod go.sum ./
RUN go mod download

# Copia todo o código
COPY . .

# Compila o binário
RUN go build -o evaluation-service .

# Etapa 2: Container final mais leve
FROM alpine:3.23
RUN apk update && apk upgrade

WORKDIR /app

# Copia o binário
COPY --from=builder /app/evaluation-service .

EXPOSE 8004

CMD ["./evaluation-service"]
