service_name=task_tracker_api
service_host=http://task_tracker_api:7777
# admin_host=http://localhost
admin_host=http://kong
admin_url=$admin_host:8001
gateway_url=$admin_host:8000

echo "adding service $service_name"
curl --fail -i -X POST \
  --url $admin_url/services/ \
  --data "name=$service_name" \
  --data "url=$service_host" || echo "service $service_name exists"


echo "adding routes to $service_name"

curl -i -X POST $admin_url/services/$service_name/routes \
  --data "paths[]=/$service_name" \
  --data name="root_$service_name"

sleep 1s
echo "healthcheck call"
curl -i -X GET --url $gateway_url/$service_name/healthcheck --header "Host: $service_name"