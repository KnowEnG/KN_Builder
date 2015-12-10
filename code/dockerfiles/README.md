### Build correct image
```
docker build -f Dockerfile -t cblatti3/python3:0.1 .
docker push cblatti3/python3:0.1
```

```
docker build -f Dockerfile.mysql -t cblatti3/py3_mysql:0.1 .
docker push cblatti3/py3_mysql:0.1
```

```
docker build -f Dockerfile.redis.mysql -t cblatti3/py3_redis_mysql:0.1 .
docker push cblatti3/py3_redis_mysql:0.1
```