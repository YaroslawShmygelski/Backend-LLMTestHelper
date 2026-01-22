up:
	docker compose --env-file .env.compose up --build -d

clean-up:
	docker compose --env-file .env.compose down -v && make up

down:
	docker compose --env-file .env.compose down

logs:
	docker compose logs -f

build:
	docker build -t llmtesthelper:dev .