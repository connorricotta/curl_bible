#!/bin/bash
docker buildx build \
    --file Containerfile \
    --tag docker.io/connorricotta/bible_db:latest \
    --cache-to type=registry,ref=docker.io/connorricotta/bible_db:buildcache,mode=max \
    --cache-from type=registry,ref=docker.io/connorricotta/bible_db:buildcache \
    --platform linux/amd64,linux/arm64 \
    --push \
    .