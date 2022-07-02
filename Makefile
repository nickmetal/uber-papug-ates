run-external-rabbit:
	docker-compose -f auth_service_external/popug-inventory/docker-composes/rabbitmq/docker-compose.yml up --build --remove-orphans rabbitmq

run-oauth-service-stack:
	docker-compose -f auth_service_external/popug-inventory/docker-composes/rabbitmq/docker-compose.yml up --build --remove-orphans

run-uber-papug-ates-stack:
	docker-compose up --build --remove-orphans
