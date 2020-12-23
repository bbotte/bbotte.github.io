# (转载)语句效率统计视图| 全面认识sys系统库

罗小波  原文链接 http://www.woqutech.com/docs_info.php?id=491



### 01 schema_tables_with_full_table_scans，x $ schema_tables_with_full_table_scans

查询执行过全扫描访问的表，或者在情况下按照表扫描的行数进行降序排序。数据来源：performance_schema.table_io_waits_summary_by_index_usage

首先查询语句文本

```
SELECT object_schema,
  object_name,
  count_read AS rows_full_scanned,
  sys.format_time(sum_timer_wait) AS latency
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE index_name IS NULL
AND count_read > 0
ORDER BY count_read DESC;
```

看看使用该视图查询返回的结果

```
# 不带x$前缀的视图
admin@localhost : sys 12:39:48> select * from schema_tables_with_full_table_scans limit 3;
+---------------+-------------+-------------------+---------+
| object_schema | object_name | rows_full_scanned | latency |
+---------------+-------------+-------------------+---------+
| sbtest        | sbtest1    |          16094049 | 24.80 s |
+---------------+-------------+-------------------+---------+
1 row in set (0.00 sec)
 
# 带x$前缀的视图
admin@localhost : sys 12:39:52> select * from x$schema_tables_with_full_table_scans limit 3;
+---------------+-------------+-------------------+----------------+
| object_schema | object_name | rows_full_scanned | latency        |
+---------------+-------------+-------------------+----------------+
| sbtest        | sbtest1    |          16094049 | 24795682856625 |
+---------------+-------------+-------------------+----------------+
1 row in set (0.00 sec)
```

初步确定如下：

1.object_schema：模式名称

2.OBJECT_NAME：表名

3.rows_full_scanned：全表扫描的总数据行数

4.延迟：完整的表扫描操作的总延迟时间（执行时间）

### 02 statement_analysis，x $ statement_analysis

查看语句汇总统计信息，这些视图模仿MySQL企业版监控的查询分析视图列出语句的聚合统计信息，根据情况下按照总时序时间（执行时间）降序排序。

首先查询语句文本

```
SELECT sys.format_statement(DIGEST_TEXT) AS query,
  SCHEMA_NAME AS db,
  IF(SUM_NO_GOOD_INDEX_USED > 0 OR SUM_NO_INDEX_USED > 0, "*", "") AS full_scan,
  COUNT_STAR AS exec_count,
  SUM_ERRORS AS err_count,
  SUM_WARNINGS AS warn_count,
  sys.format_time(SUM_TIMER_WAIT) AS total_latency,
  sys.format_time(MAX_TIMER_WAIT) AS max_latency,
  sys.format_time(AVG_TIMER_WAIT) AS avg_latency,
  sys.format_time(SUM_LOCK_TIME) AS lock_latency,
  SUM_ROWS_SENT AS rows_sent,
  ROUND(IFNULL(SUM_ROWS_SENT / NULLIF(COUNT_STAR, 0), 0)) AS rows_sent_avg,
  SUM_ROWS_EXAMINED AS rows_examined,
  ROUND(IFNULL(SUM_ROWS_EXAMINED / NULLIF(COUNT_STAR, 0), 0))  AS rows_examined_avg,
  SUM_ROWS_AFFECTED AS rows_affected,
  ROUND(IFNULL(SUM_ROWS_AFFECTED / NULLIF(COUNT_STAR, 0), 0))  AS rows_affected_avg,
  SUM_CREATED_TMP_TABLES AS tmp_tables,
  SUM_CREATED_TMP_DISK_TABLES AS tmp_disk_tables,
  SUM_SORT_ROWS AS rows_sorted,
  SUM_SORT_MERGE_PASSES AS sort_merge_passes,
  DIGEST AS digest,
  FIRST_SEEN AS first_seen,
  LAST_SEEN as last_seen
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC;
```

看看使用该视图查询返回的结果

```
# 不带x$前缀的视图
admin@localhost : sys 12:46:07> select * from statement_analysis limit 1G
*************************** 1. row ***************************
        query: ALTER TABLE `test` ADD INDEX `i_k` ( `test` ) 
          db: xiaoboluo
    full_scan: 
  exec_count: 2
    err_count: 2
  warn_count: 0
total_latency: 56.56 m
  max_latency: 43.62 m
  avg_latency: 28.28 m
lock_latency: 0 ps
    rows_sent: 0
rows_sent_avg: 0
rows_examined: 0
rows_examined_avg: 0
rows_affected: 0
rows_affected_avg: 0
  tmp_tables: 0
tmp_disk_tables: 0
  rows_sorted: 0
sort_merge_passes: 0
      digest: f359a4a8407ee79ea1d84480fdd04f62
  first_seen: 2017-09-07 11:44:35
    last_seen: 2017-09-07 12:36:47
1 row in set (0.14 sec)
 
# 带x$前缀的视图
admin@localhost : sys 12:46:34> select * from x$statement_analysis limit 1G;
*************************** 1. row ***************************
        query: ALTER TABLE `test` ADD INDEX `i_k` ( `test` ) 
          db: xiaoboluo
    full_scan: 
  exec_count: 2
    err_count: 2
  warn_count: 0
total_latency: 3393877088372000
  max_latency: 2617456143674000
  avg_latency: 1696938544186000
lock_latency: 0
    rows_sent: 0
rows_sent_avg: 0
rows_examined: 0
rows_examined_avg: 0
rows_affected: 0
rows_affected_avg: 0
  tmp_tables: 0
tmp_disk_tables: 0
  rows_sorted: 0
sort_merge_passes: 0
      digest: f359a4a8407ee79ea1d84480fdd04f62
  first_seen: 2017-09-07 11:44:35
    last_seen: 2017-09-07 12:36:47
1 row in set (0.01 sec)

```

初步确定如下：

- 查询：通过标准化转换的语句字符串，不带x $的视图长度限制为64字节，带x $的视图长度限制为1024字节
- db：语句对应的默认数据库，如果没有分布式数据库，该分区为NULL
- full_scan：语句全表扫描查询的总次数
- exec_count：语句执行的总次数
- err_count：语句发生的错误总次数
- warn_count：语句发生的警告总次数
- total_latency：语句的总延迟时间（执行时间）
- max_latency：个别语句的最大延迟时间（执行时间）
- avg_latency：每个语句的平均延迟时间（执行时间）
- lock_latency：语句的总锁等待时间
- rows_sent：语句返回客户端的总数据行数
- rows_sent_avg：每个语句返回客户端的平均数据行数
- rows_examined：语句从存储引擎读取的总数据数
- rows_examined_avg：每个语句从存储引擎检查的平均数据行数
- rows_affected：语句影响的总数据行数
- rows_affected_avg：每个语句影响的平均数据行数
- tmp_tables：语句执行时创建的内部内存临时表的总数
- tmp_disk_tables：语句执行时创建的内部磁盘临时表的总数
- rows_sorted：语句执行时出现排序的总数据行数
- sort_merge_passes：语句执行时出现排序合并的总次数
- 摘要：语句摘要计算的md5哈希值
- first_seen：该语句第一次出现的时间
- last_seen：该语句最近一次出现的时间

### **03 **statement_with_errors_or_warnings，x $ statements_with_errors_or_warnings**

查看产生错误或警告的语句，每次情况下，按照错误数量和警告数量降序排序。数据来源：performance_schema.events_statements_summary_by_digest

PS：这里大家注意了，语法错误或产生警告的语句通常错误日志中不记录，慢查询日志中也不记录，只有查询日志中会记录所有的语句，但不携带语句执行状态的信息，所以无法判断是否执行了错误或有警告的语句，通过该视图可以查询到语句执行的状态信息，以后开发执行了某个语句有语法错误来问你想查看具体的语句文本的时候，别再说MySQL不支持查看啦。

首先查询语句文本

```
SELECT sys.format_statement(DIGEST_TEXT) AS query,
  SCHEMA_NAME as db,
  COUNT_STAR AS exec_count,
  SUM_ERRORS AS errors,
  IFNULL(SUM_ERRORS / NULLIF(COUNT_STAR, 0), 0) * 100 as error_pct,
  SUM_WARNINGS AS warnings,
  IFNULL(SUM_WARNINGS / NULLIF(COUNT_STAR, 0), 0) * 100 as warning_pct,
  FIRST_SEEN as first_seen,
  LAST_SEEN as last_seen,
  DIGEST AS digest
FROM performance_schema.events_statements_summary_by_digest
WHERE SUM_ERRORS > 0
OR SUM_WARNINGS > 0
ORDER BY SUM_ERRORS DESC, SUM_WARNINGS DESC;
```

下面我们看看使用该视图查询返回的结果

```
# 不带x$前缀的视图
admin@localhost : sys 12:47:36> select * from statements_with_errors_or_warnings limit 1G
*************************** 1. row ***************************
  query: SELECT * FROM `test` LIMIT ? FOR UPDATE 
    db: xiaoboluo
exec_count: 5
errors: 3
error_pct: 60.0000
warnings: 0
warning_pct: 0.0000
first_seen: 2017-09-07 11:29:44
last_seen: 2017-09-07 12:45:58
digest: 9f50f1fc79fc6ea678dec6576b7d7faa
1 row in set (0.00 sec)
 
# 带x$前缀的视图
admin@localhost : sys 12:47:45> select * from x$statements_with_errors_or_warnings limit 1G;
*************************** 1. row ***************************
  query: SELECT * FROM `test` LIMIT ? FOR UPDATE 
    db: xiaoboluo
exec_count: 5
errors: 3
error_pct: 60.0000
warnings: 0
warning_pct: 0.0000
first_seen: 2017-09-07 11:29:44
last_seen: 2017-09-07 12:45:58
digest: 9f50f1fc79fc6ea678dec6576b7d7faa
1 row in set (0.00 sec)
```

初步确定如下：

- 查询：通过标准化转换的语句字符串
- db：语句对应的默认数据库，如果没有分布式数据库，该分区为NULL
- exec_count：语句执行的总次数
- 错误：语句发生的错误总次数
- error_pct：语句产生错误的次数与语句总执行次数的百分比
- 警告：语句发生的警告总次数
- warning_pct：语句产生警告的与语句总执行次数的百分比
- first_seen：该语句第一次出现的时间
- last_seen：该语句最近一次出现的时间
- 摘要：语句摘要计算的md5哈希值

### 04 statement_with_full_table_scans，x $ statements_with_full_table_scans

查看全表扫描或者没有使用到最佳索引的语句（通过标准化转换的语句文本），或者在情况下按照全表扫描次数与语句总次数百分比和语句总延迟时间（执行时间）降序排序。数据来源： performance_schema.events_statements_summary_by_digest

首先查询语句文本

```
SELECT sys.format_statement(DIGEST_TEXT) AS query,
  SCHEMA_NAME as db,
  COUNT_STAR AS exec_count,
  sys.format_time(SUM_TIMER_WAIT) AS total_latency,
  SUM_NO_INDEX_USED AS no_index_used_count,
  SUM_NO_GOOD_INDEX_USED AS no_good_index_used_count,
  ROUND(IFNULL(SUM_NO_INDEX_USED / NULLIF(COUNT_STAR, 0), 0) * 100) AS no_index_used_pct,
  SUM_ROWS_SENT AS rows_sent,
  SUM_ROWS_EXAMINED AS rows_examined,
  ROUND(SUM_ROWS_SENT/COUNT_STAR) AS rows_sent_avg,
  ROUND(SUM_ROWS_EXAMINED/COUNT_STAR) AS rows_examined_avg,
  FIRST_SEEN as first_seen,
  LAST_SEEN as last_seen,
  DIGEST AS digest
FROM performance_schema.events_statements_summary_by_digest
WHERE (SUM_NO_INDEX_USED > 0
OR SUM_NO_GOOD_INDEX_USED > 0)
AND DIGEST_TEXT NOT LIKE "SHOW%"
ORDER BY no_index_used_pct DESC, total_latency DESC;
```

下面我们看看使用该视图查询返回的结果

```
# 不带x$前缀的视图
admin@localhost : sys 12:51:27> select * from statements_with_full_table_scans limit 1G
*************************** 1. row ***************************
              query: SELECT `performance_schema` .  ... ance` . `SUM_TIMER_WAIT` DESC 
                  db: sys
          exec_count: 1
      total_latency: 938.45 us
no_index_used_count: 1
no_good_index_used_count: 0
  no_index_used_pct: 100
          rows_sent: 3
      rows_examined: 318
      rows_sent_avg: 3
  rows_examined_avg: 318
          first_seen: 2017-09-07 09:34:12
          last_seen: 2017-09-07 09:34:12
              digest: 5b5b4e15a8703769d9b9e23e9e92d499
1 row in set (0.01 sec)
 
# 带x$前缀的视图，要注意：从这里可以明显看到带x$的视图的query字段值较长，
该长度受系统变量performance_schema_max_digest_length的值控制，默认为1024字节，
而不带x$的视图该字段进一步使用了sys.format_statement()函数进行截断，
该函数的截断长度限制受sys.sys_config配置表中的statement_truncate_len 配置值控制，默认值为64字节。
所以，你会看到对于query语句文本，两者的输出长度有很大差别，如果你需要通过这些文本来甄别语句，那么请留意这个差异
admin@localhost : sys 12:51:36> select * from x$statements_with_full_table_scans limit 1G;
*************************** 1. row ***************************
              query: SELECT IF ( ( `locate` ( ? , `ibp` . `TABLE_NAME` ) = ? ) , ? , REPLACE ( `substring_index` ( `ibp` . `TABLE_NAME` , ?, ... ) , ?, ... ) ) AS `object_schema` , REPLACE ( `substring_index`
( `ibp` . `TABLE_NAME` , ? , - (?) ) , ?, ... ) AS `object_name` , SUM ( IF ( ( `ibp` . `COMPRESSED_SIZE` = ? ) , ? , `ibp` . `COMPRESSED_SIZE` ) ) AS `allocated` , SUM ( `ibp` . `DATA_SIZE` ) AS `data` , 
COUNT ( `ibp` . `PAGE_NUMBER` ) AS `pages` , COUNT ( IF ( ( `ibp` . `IS_HASHED` = ? ) , ?, ... ) ) AS `pages_hashed` , COUNT ( IF ( ( `ibp` . `IS_OLD` = ? ) , ?, ... ) ) AS `pages_old` , `round` ( `ifnull` ( ( SUM
( `ibp` . `NUMBER_RECORDS` ) / `nullif` ( COUNT ( DISTINCTROW `ibp` . `INDEX_NAME` ) , ? ) ) , ? ) , ? ) AS `rows_cached` FROM `information_schema` . `innodb_buffer_page` `ibp` WHERE
 ( `ibp` . `TABLE_NAME` IS NOT NULL ) GROUP BY `object_schema` , `object_name` ORDER BY SUM ( IF ( ( `ibp` . `COMPRESSED_SIZE` = ? ) , ? , `ibp` . `COMPRESSED_SIZE` ) ) DESC 
                  db: sys
          exec_count: 4
      total_latency: 46527032553000
no_index_used_count: 4
no_good_index_used_count: 0
  no_index_used_pct: 100
          rows_sent: 8
      rows_examined: 942517
      rows_sent_avg: 2
  rows_examined_avg: 235629
          first_seen: 2017-09-07 12:36:58
          last_seen: 2017-09-07 12:38:37
              digest: 59abe341d11b5307fbd8419b0b9a7bc3
1 row in set (0.00 sec)
```

初步确定如下：

- 查询：通过标准化转换的语句字符串
- db：语句对应的默认数据库，如果没有分布式数据库，该分区为NULL
- exec_count：语句执行的总次数
- total_latency：语句执行的总延迟时间（执行时间）
- no_index_used_count：语句执行没有使用索引扫描表（其他使用全表扫描）的总次数
- no_good_index_used_count：语句执行没有使用到更好的索引扫描表的总次数
- no_index_used_pct：语句执行没有使用索引扫描表（或使用其他表扫描）的次数与语句执行总次数的百分比
- rows_sent：语句执行从表返回给客户端的总数据行数
- rows_examined：语句执行从存储引擎检查的总数据行数
- rows_sent_avg：每个语句执行从表中返回客户端的平均数据行数
- rows_examined_avg：每个语句执行从存储引擎读取的平均数据行数
- first_seen：该语句第一次出现的时间
- last_seen：该语句最近一次出现的时间
- 摘要：语句摘要计算的md5哈希值

### 05 statement_with_runtimes_in_95th_percentile，x $ statements_with_runtimes_in_95th_percentile

查看平均执行时间值大于95％的平均执行时间的语句（可近似地认为是平均执行时间超长的语句），在其他情况下按照语句平均延迟（执行时间）降序排序。数据来源：performance_schema.events_statements_summary_by_digest， sys.x $ ps_digest_95th_percentile_by_avg_us

两个视图都使用两个辅助视图sys.x `$` ps_digest_avg_latency_distribution和sys.x `$` ps_digest_95th_percentile_by_avg_us

`*` X `$` ps_digest_avg_latency_distribution视图对performance_schema.events_statements_summary_by_digest表中的avg_timer_wait列转换为微秒单位，然后使用轮（）函数以微秒为单位转换为整型值并命名为avg_us列，根据avg_us分组并使用count（）统计行数并命名为cnt列

`*` x `$` ps_digest_95th_percentile_by_avg_us视图在内部通过两个（x）ps `$` digest_avg_latency_distribution查询形式，使用联结条件ON s1.avg_us <= s2.avg_us的形式，按照s2.avg_us分组，并根据SUM（s1.cnt）/ select COUNT（）... performance_schema.events_statements_summary_by_digest> 0.95进行分组后再再过滤，实际上该视图最终返回的是每个语句平均执行时间相对于整个performance_schema.events_statements_summary_by_digest表统计值的直方图

`*`statement_with_runtimes_in_95th_percentile，x `$` statements_with_runtimes_in_95th_percentile_内部_x_ps_digest_95th_percentile_by_avg_us视图与performance_schema.events_statements_summary_by_digest表联结打印直方图分布值大于0.95的性能_schema。

首先查询语句文本

```
SELECT sys.format_statement(DIGEST_TEXT) AS query,
  SCHEMA_NAME as db,
  IF(SUM_NO_GOOD_INDEX_USED > 0 OR SUM_NO_INDEX_USED > 0, "*", "") AS full_scan,
  COUNT_STAR AS exec_count,
  SUM_ERRORS AS err_count,
  SUM_WARNINGS AS warn_count,
  sys.format_time(SUM_TIMER_WAIT) AS total_latency,
  sys.format_time(MAX_TIMER_WAIT) AS max_latency,
  sys.format_time(AVG_TIMER_WAIT) AS avg_latency,
  SUM_ROWS_SENT AS rows_sent,
  ROUND(IFNULL(SUM_ROWS_SENT / NULLIF(COUNT_STAR, 0), 0)) AS rows_sent_avg,
  SUM_ROWS_EXAMINED AS rows_examined,
  ROUND(IFNULL(SUM_ROWS_EXAMINED / NULLIF(COUNT_STAR, 0), 0)) AS rows_examined_avg,
  FIRST_SEEN AS first_seen,
  LAST_SEEN AS last_seen,
  DIGEST AS digest
FROM performance_schema.events_statements_summary_by_digest stmts
JOIN sys.x$ps_digest_95th_percentile_by_avg_us AS top_percentile
ON ROUND(stmts.avg_timer_wait/1000000) >= top_percentile.avg_us
ORDER BY AVG_TIMER_WAIT DESC;
```

看看使用该视图查询返回的结果

```
# 不带x$前缀的视图
admin@localhost : sys 12:53:06> select * from statements_with_runtimes_in_95th_percentile limit 1G
*************************** 1. row ***************************
        query: ALTER TABLE `test` ADD INDEX `i_k` ( `test` ) 
          db: xiaoboluo
    full_scan: 
  exec_count: 2
    err_count: 2
  warn_count: 0
total_latency: 56.56 m
  max_latency: 43.62 m
  avg_latency: 28.28 m
    rows_sent: 0
rows_sent_avg: 0
rows_examined: 0
rows_examined_avg: 0
  first_seen: 2017-09-07 11:44:35
    last_seen: 2017-09-07 12:36:47
      digest: f359a4a8407ee79ea1d84480fdd04f62
1 row in set (0.01 sec)
 
# 带x$前缀的视图
admin@localhost : sys 12:53:10> select * from x$statements_with_runtimes_in_95th_percentile limit 1G;
*************************** 1. row ***************************
        query: ALTER TABLE `test` ADD INDEX `i_k` ( `test` ) 
          db: xiaoboluo
    full_scan: 
  exec_count: 2
    err_count: 2
  warn_count: 0
total_latency: 3393877088372000
  max_latency: 2617456143674000
  avg_latency: 1696938544186000
    rows_sent: 0
rows_sent_avg: 0
rows_examined: 0
rows_examined_avg: 0
  first_seen: 2017-09-07 11:44:35
    last_seen: 2017-09-07 12:36:47
      digest: f359a4a8407ee79ea1d84480fdd04f62
1 row in set (0.01 sec)
```

初步确定如下：

- 查询：通过标准化转换的语句字符串
- db：语句对应的默认数据库，如果没有分布式数据库，该分区为NULL
- full_scan：语句全表扫描查询的总次数
- exec_count：语句执行的总次数
- err_count：语句发生的错误总次数
- warn_count：语句发生的警告总次
- total_latency：语句执行的总延迟时间（执行时间）
- max_latency：个别语句的最大延迟时间（执行时间）
- avg_latency：每个语句的平均延迟时间（执行时间）
- rows_sent：语句执行从表返回给客户端的总数据行数
- rows_sent_avg：每个语句执行从表中返回客户端的平均数据行数
- rows_examined：语句执行从存储引擎检查的总数据行数
- rows_examined_avg：每个语句执行从存储引擎检查的平均数据行数
- first_seen：该语句第一次出现的时间
- last_seen：该语句最近一次出现的时间
- 摘要：语句摘要计算的md5哈希值

### 06 statement_with_sorting，x $ statements_with_sorting

查看执行了文件排序的语句，每次情况下遵循语句总时间（执行时间）降序排序，数据来源：performance_schema.events_statements_summary_by_digest

首先查询语句文本

```
SELECT sys.format_statement(DIGEST_TEXT) AS query,
  SCHEMA_NAME db,
  COUNT_STAR AS exec_count,
  sys.format_time(SUM_TIMER_WAIT) AS total_latency,
  SUM_SORT_MERGE_PASSES AS sort_merge_passes,
  ROUND(IFNULL(SUM_SORT_MERGE_PASSES / NULLIF(COUNT_STAR, 0), 0)) AS avg_sort_merges,
  SUM_SORT_SCAN AS sorts_using_scans,
  SUM_SORT_RANGE AS sort_using_range,
  SUM_SORT_ROWS AS rows_sorted,
  ROUND(IFNULL(SUM_SORT_ROWS / NULLIF(COUNT_STAR, 0), 0)) AS avg_rows_sorted,
  FIRST_SEEN as first_seen,
  LAST_SEEN as last_seen,
  DIGEST AS digest
FROM performance_schema.events_statements_summary_by_digest
WHERE SUM_SORT_ROWS > 0
ORDER BY SUM_TIMER_WAIT DESC;
```

看看使用该视图查询返回的结果

```
# 不带x$前缀的视图
admin@localhost : sys 12:53:16> select * from statements_with_sorting limit 1G
*************************** 1. row ***************************
        query: SELECT IF ( ( `locate` ( ? , ` ...  . `COMPRESSED_SIZE` ) ) DESC 
          db: sys
  exec_count: 4
total_latency: 46.53 s
sort_merge_passes: 48
avg_sort_merges: 12
sorts_using_scans: 16
sort_using_range: 0
  rows_sorted: 415391
avg_rows_sorted: 103848
  first_seen: 2017-09-07 12:36:58
    last_seen: 2017-09-07 12:38:37
      digest: 59abe341d11b5307fbd8419b0b9a7bc3
1 row in set (0.00 sec)
 
# 带x$前缀的视图
admin@localhost : sys 12:53:35> select * from x$statements_with_sorting limit 1G;
*************************** 1. row ***************************
        query: SELECT IF ( ( `locate` ( ? , `ibp` . `TABLE_NAME` ) = ? ) , ? , REPLACE ( `substring_index` ( `ibp` . `TABLE_NAME` , ?, ... ) , ?, ... ) ) AS `object_schema` , REPLACE ( `substring_index` 
( `ibp` . `TABLE_NAME` , ? , - (?) ) , ?, ... ) AS `object_name` , SUM ( IF ( ( `ibp` . `COMPRESSED_SIZE` = ? ) , ? , `ibp` . `COMPRESSED_SIZE` ) ) AS `allocated` , SUM ( `ibp` . `DATA_SIZE` ) AS `data` , 
COUNT ( `ibp` . `PAGE_NUMBER` ) AS `pages` , COUNT ( IF ( ( `ibp` . `IS_HASHED` = ? ) , ?, ... ) ) AS `pages_hashed` , COUNT ( IF ( ( `ibp` . `IS_OLD` = ? ) , ?, ... ) ) AS `pages_old` , `round` 
( `ifnull` ( ( SUM ( `ibp` . `NUMBER_RECORDS` ) / `nullif` ( COUNT ( DISTINCTROW `ibp` . `INDEX_NAME` ) , ? ) ) , ? ) , ? ) AS `rows_cached` FROM `information_schema` . `innodb_buffer_page` `ibp` WHERE 
( `ibp` . `TABLE_NAME` IS NOT NULL ) GROUP BY `object_schema` , `object_name` ORDER BY SUM ( IF ( ( `ibp` . `COMPRESSED_SIZE` = ? ) , ? , `ibp` . `COMPRESSED_SIZE` ) ) DESC 
          db: sys
  exec_count: 4
total_latency: 46527032553000
sort_merge_passes: 48
avg_sort_merges: 12
sorts_using_scans: 16
sort_using_range: 0
  rows_sorted: 415391
avg_rows_sorted: 103848
  first_seen: 2017-09-07 12:36:58
    last_seen: 2017-09-07 12:38:37
      digest: 59abe341d11b5307fbd8419b0b9a7bc3
1 row in set (0.00 sec)
```

初步确定如下：

- 查询：通过标准化转换的语句字符串
- db：语句对应的默认数据库，如果没有分布式数据库，该分区为NULL
- exec_count：语句执行的总次数
- total_latency：语句执行的总延迟时间（执行时间）
- sort_merge_passes：语句执行发生的语句排序合并的总次数
- avg_sort_merges：针对发生排序合并的语句，每个语句的平均排序合并次数（SUM_SORT_MERGE_PASSES / COUNT_STAR）
- sorts_using_scans：语句排序执行全表扫描的总次数
- sort_using_range：语句排序执行范围扫描的总次数
- rows_sorted：语句执行发生排序的总数据行数
- avg_rows_sorted：针对发生排序的语句，每个语句的平均排序数据行数（SUM_SORT_ROWS / COUNT_STAR）
- first_seen：该语句第一次出现的时间
- last_seen：该语句最近一次出现的时间
- 摘要：语句摘要计算的md5哈希值

### 07 statement_with_temp_tables，x $ statements_with_temp_tables

查看使用了临时表的语句，在情况下按照磁盘临时表数量和内存临时表数量进行降序排序。数据来源：performance_schema.events_statements_summary_by_digest

首先查询语句文本

```
SELECT sys.format_statement(DIGEST_TEXT) AS query,
  SCHEMA_NAME as db,
  COUNT_STAR AS exec_count,
  sys.format_time(SUM_TIMER_WAIT) as total_latency,
  SUM_CREATED_TMP_TABLES AS memory_tmp_tables,
  SUM_CREATED_TMP_DISK_TABLES AS disk_tmp_tables,
  ROUND(IFNULL(SUM_CREATED_TMP_TABLES / NULLIF(COUNT_STAR, 0), 0)) AS avg_tmp_tables_per_query,
  ROUND(IFNULL(SUM_CREATED_TMP_DISK_TABLES / NULLIF(SUM_CREATED_TMP_TABLES, 0), 0) * 100) AS tmp_tables_to_disk_pct,
  FIRST_SEEN as first_seen,
  LAST_SEEN as last_seen,
  DIGEST AS digest
FROM performance_schema.events_statements_summary_by_digest
WHERE SUM_CREATED_TMP_TABLES > 0
ORDER BY SUM_CREATED_TMP_DISK_TABLES DESC, SUM_CREATED_TMP_TABLES DESC;
```

看看使用该视图查询返回的结果

```
# 不带x$前缀的视图
admin@localhost : sys 12:54:26> select * from statements_with_temp_tables limit 1G
*************************** 1. row ***************************
              query: SELECT `performance_schema` .  ... name` . `SUM_TIMER_WAIT` DESC 
                  db: sys
          exec_count: 2
      total_latency: 1.53 s
  memory_tmp_tables: 458
    disk_tmp_tables: 38
avg_tmp_tables_per_query: 229
tmp_tables_to_disk_pct: 8
          first_seen: 2017-09-07 11:18:31
          last_seen: 2017-09-07 11:19:43
              digest: 6f58edd9cee71845f592cf5347f8ecd7
1 row in set (0.00 sec)
 
# 带x$前缀的视图
admin@localhost : sys 12:54:28> select * from x$statements_with_temp_tables limit 1G;
*************************** 1. row ***************************
              query: SELECT `performance_schema` . `events_waits_summary_global_by_event_name` . `EVENT_NAME` AS `events` , `performance_schema` . `events_waits_summary_global_by_event_name` . 
`COUNT_STAR` AS `total` , `performance_schema` . `events_waits_summary_global_by_event_name` . `SUM_TIMER_WAIT` AS `total_latency` , `performance_schema` . 
`events_waits_summary_global_by_event_name` . `AVG_TIMER_WAIT` AS `avg_latency` , `performance_schema` . `events_waits_summary_global_by_event_name` . `MAX_TIMER_WAIT` AS `max_latency` 
FROM `performance_schema` . `events_waits_summary_global_by_event_name` WHERE ( ( `performance_schema` . `events_waits_summary_global_by_event_name` . `EVENT_NAME` != ? ) AND
( `performance_schema` . `events_waits_summary_global_by_event_name` . `SUM_TIMER_WAIT` > ? ) ) ORDER BY `performance_schema` . `events_waits_summary_global_by_event_name` . 
`SUM_TIMER_WAIT` DESC 
                  db: sys
          exec_count: 2
      total_latency: 1529225370000
  memory_tmp_tables: 458
    disk_tmp_tables: 38
avg_tmp_tables_per_query: 229
tmp_tables_to_disk_pct: 8
          first_seen: 2017-09-07 11:18:31
          last_seen: 2017-09-07 11:19:43
              digest: 6f58edd9cee71845f592cf5347f8ecd7
1 row in set (0.00 sec)
```

初步确定如下：

- 查询：通过标准化转换的语句字符串
- db：语句对应的默认数据库，如果没有分布式数据库，该分区为NULL
- exec_count：语句执行的总次数
- total_latency：语句执行的总延迟时间（执行时间）
- memory_tmp_tables：语句执行时创建内部内存临时表的总数量
- disk_tmp_tables：语句执行时创建的内部磁盘临时表的总数量
- avg_tmp_tables_per_query：对于使用了内存临时表的语句，每个语句使用内存临时表的平均数量（SUM_CREATED_TMP_TABLES / COUNT_STAR）
- tmp_tables_to_disk_pct：内存临时表的总数量与磁盘临时表的总数量比例，表示磁盘临时表的转换率（SUM_CREATED_TMP_DISK_TABLES /SUM_CREATED_TMP_TABLES）
- first_seen：该语句第一次出现的时间
- last_seen：该语句最近一次出现的时间
- 摘要：语句摘要计算的md5哈希值

**内容参考链接如下：**

- https://dev.mysql.com/doc/refman/5.7/zh-CN/sys-schema-tables-with-full-table-scans.html
- https://dev.mysql.com/doc/refman/5.7/zh-CN/sys-statements-with-temp-tables.html
- https://dev.mysql.com/doc/refman/5.7/zh-CN/sys-statement-analysis.html
- https://dev.mysql.com/doc/refman/5.7/zh-CN/sys-statements-with-errors-or-warnings.html
- https://dev.mysql.com/doc/refman/5.7/zh-CN/sys-statements-with-full-table-scans.html
- https://dev.mysql.com/doc/refman/5.7/en/sys-statements-with-runtimes-in-95th-percentile.html
- https://dev.mysql.com/doc/refman/5.7/zh-CN/sys-statements-with-sorting.html