### Oauth/identity service

#### allows
- create user
- assign role to users
- notify rabbitmmq consumers about ongoing changes
- expose rabbitmq service for integration between other servises


### Setup

```sh
git clone https://github.com/davydovanton/popug-inventory.git
cd popug-inventory
git checkout 987fd44
cd docker-composes/rabbitmq
docker-compose up --build
# open localhost:3000
# apply migrations on UI
# register new user(with admin role)
# create new oauth app in http://localhost:3000/oauth/applications/new(see app settings)
```


### Integration notes
- expose 0.0.0.0 ports for consumers from other services in docker composer file
- create needed queues in rabbit


### oauth app settings

- app_name - task_service
- redirect url - http://localhost:7777/auth_callback
- scopes: openid task:read task:add task:complete task:shuffle 
- copy app details