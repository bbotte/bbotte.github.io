## Redis Search Key

为什么用这个工具：redis多数客户端并不支持在16个db中查询一个键的功能

用途：查询redis 16个数据库里面某些key的值

方式：模糊匹配需要查询的key，比如 `a*,  *a*`

缺点：不支持除get之外其他命令

![redissearch](./static/pic/redis-search-key.gif)
