kong-postgres:
	COMPOSE_PROFILES=database KONG_DATABASE=postgres docker-compose up -d

kong-dbless:
	docker-compose up -d

clean:
	docker-compose kill
	docker-compose rm -f
	docker volume rm uber-popug-ates_kong_data
	docker volume rm uber-popug-ates_kong_prefix_vol
	docker volume rm uber-popug-ates_kong_tmp_vol
	