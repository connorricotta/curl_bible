TAG=$(cat .bumpversion.cfg | grep 'current_version =' | awk -F "=" '{ print $2}' | xargs)
echo v$TAG
docker buildx build --platform linux/amd64,linux/arm/v7,linux/arm64  --cache-from type=registry,ref=quay.io/connorricotta/curl_bible --cache-from type=registry,ref=quay.io/connorricotta/curl_bible,mode=max -t quay.io/connorricotta/curl_bible:v$TAG -t quay.io/connorricotta/curl_bible:latest --push .
