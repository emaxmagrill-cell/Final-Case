docker build -t final_project:latest .
docker run --rm \
    -p 8080:8000 \
    --env-file .env.example \
    final_project:latest
