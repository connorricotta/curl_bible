#!/bin/bash
docker buildx build \
    --file Containerfile \
    --tag docker.io/connorricotta/curl_bible:latest \
    --cache-to type=registry,ref=docker.io/connorricotta/curl_bible:buildcache,mode=max \
    --cache-from type=registry,ref=docker.io/connorricotta/curl_bible:buildcache \
    --platform linux/amd64,linux/arm64 \
    --push \
    .
#,,linux/arm/v7