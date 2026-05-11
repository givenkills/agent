import time
import logging

logger = logging.getLogger("uvicorn.error")

redis_client = None


async def init_redis():
    global redis_client
    try:
        import redis.asyncio as aioredis
        from config import settings
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis 连接成功")
    except Exception as e:
        redis_client = None
        logger.warning(f"Redis 连接失败（限流功能禁用）: {e}")


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()


async def rate_limit_middleware(request, call_next):
    if redis_client is None:
        return await call_next(request)

    from fastapi import HTTPException
    from config import settings

    client_ip = request.client.host if request.client else "unknown"
    minute_key = f"rate_limit:{client_ip}:minute"
    hour_key = f"rate_limit:{client_ip}:hour"

    now = time.time()
    minute_window = now - 60
    hour_window = now - 3600

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(minute_key, 0, minute_window)
    pipe.zcard(minute_key)
    pipe.zremrangebyscore(hour_key, 0, hour_window)
    pipe.zcard(hour_key)
    results = await pipe.execute()

    minute_count = results[1]
    hour_count = results[3]

    if minute_count >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，每分钟限制 {settings.RATE_LIMIT_PER_MINUTE} 次",
        )
    if hour_count >= settings.RATE_LIMIT_PER_HOUR:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，每小时限制 {settings.RATE_LIMIT_PER_HOUR} 次",
        )

    pipe = redis_client.pipeline()
    pipe.zadd(minute_key, {str(now): now})
    pipe.expire(minute_key, 120)
    pipe.zadd(hour_key, {str(now): now})
    pipe.expire(hour_key, 7200)
    await pipe.execute()

    return await call_next(request)
