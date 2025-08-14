# python3 redis_sync.py
# 适用于使用布隆过滤器的redis之间迁移，比如主机之间，主机和云服务（阿里云云数据库 Tair）之间。只需要安装redis 模块
# 没有使用bloom模块的也可以做redis之间数据复制
from redis import Redis
      
def migrate_single_key(src, dst, key):
    key_type = src.type(key)
    if key_type == b'string':
        dst.set(key, src.get(key))
    elif key_type == b'hash':
        dst.hmset(key, src.hgetall(key))
    elif key_type == b'list':
        if vals := src.lrange(key, 0, -1):
            dst.rpush(key, *vals)
    elif key_type == b'set':
        if vals := src.smembers(key):
            dst.sadd(key, *vals)
    elif key_type == b'zset':
        if vals := src.zrange(key, 0, -1, withscores=True):
            dst.zadd(key, dict(vals))
    else:
        raise ValueError("not suppot {}".format(key_type))

for r in range(16):
    print("db {}".format(r))
    # redis源数据库
    s = Redis(host='r-12345.redis.rds.aliyuncs.com', port=6379,password='redis_user:1234512345', db=r, socket_connect_timeout=1)
    
    # 目的地数据库
    d = Redis(host="r-67890.redis.rds.aliyuncs.com", port=6379, password='redis_user:6789067890',db=r)
    
    normal_keys = []
    bloom_keys = []
    
    for k in s.scan_iter(match="*"):
        # 使用布隆过滤器的key前缀是 abcd:efg:
        if not k.decode().startswith("abcd:efg:"):
            normal_keys.append(k)
        else:
            bloom_keys.append(k)
    print(len(normal_keys))
    print(len(bloom_keys))
    
    for b in bloom_keys:
        chunks = []
        cursor=0
        try:
            while True:
                cursor, data = s.execute_command('BF.SCANDUMP', b, cursor)
                if cursor == 0: break
                chunks.append([cursor, data])
            
            d.execute_command('DEL', b)
            for cursor, data in chunks:
                d.execute_command('BF.LOADCHUNK', b, cursor, data)
        except Exception as e:
            print(b)
            print(e)
    
    batch_size=200
    for i in range(0, len(normal_keys), batch_size):
        batch = normal_keys[i:i+batch_size]
        pipe = d.pipeline()
        for key in batch:
            key_type = s.type(key)
            if key_type == b'string':
                val = s.get(key)
                pipe.set(key, val)
            elif key_type == b'hash':
                val = s.hgetall(key)
                pipe.hmset(key, val)
            elif key_type == b'list':
                val = s.lrange(key, 0, -1)
                if val: pipe.rpush(key, *val)
            elif key_type == b'set':
                val = s.smembers(key)
                if val: pipe.sadd(key, *val)
            elif key_type == b'zset':
                val = s.zrange(key, 0, -1, withscores=True)
                if val: pipe.zadd(key, dict(val))
            else:
                print("key_type err {}".format(key))
        try:
            pipe.execute()
        except Exception as e:
            print(e)
            for key in batch:
                try:
                    migrate_single_key(s, d, key)
                except Exception as e:
                    print(e)
 
