# uber-papug-ates
Repo for event-driven architecture course by https://education.borshev.com/architecture


## How to run


```sh
# 1. fill env vars
# NOTE: for docker and local env hosts might be different
export OAUTH_CLIENT_ID=
export OAUTH_CLIENT_SECRET=
export OAUTH_URL=http://localhost:3000/oauth/authorize
export OAUTH_TOKEN_URL=http://localhost:3000/oauth/token
export OAUTH_REDIRECT_URL=http://localhost:7777/auth_callback
export OAUTH_ACCONT_INFO_URL=http://localhost:3000/accounts/current
export OAUTHLIB_INSECURE_TRANSPORT=1  # for local dev only, needs to have tls
export RABBITMQ_DSN=localhost

export MONGO_DSN=
export MONGO_DB_NAME=papug_jira
export MONGO_ERROR_COLLECTION=errors

# 2. start auth service + message broken
# 3. start task service
# 4. start account service
# 5. start analytics service
# 6. start scheduler service
```