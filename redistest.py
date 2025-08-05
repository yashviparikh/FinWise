import redis

redis_url = "rediss://default:9ElSXhXSjpLH7Sqkei8R0TAuHYd6KvI4@redis-10736.c212.ap-south-1-1.ec2.redns.redis-cloud.com:10736"

redis_client = redis.from_url(redis_url, decode_responses=True)

def test_redis():
    redis_client.set("testkey", "Hello Redis!")
    print(redis_client.get("testkey"))

test_redis()
