run-external-rabbit:
	docker-compose -f auth_service_external/popug-inventory/docker-composes/rabbitmq/docker-compose.yml up --build --remove-orphans rabbitmq
