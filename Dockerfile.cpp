# Use alpine linux as base
FROM alpine:latest

RUN apk add --no-cache g++

WORKDIR /app

