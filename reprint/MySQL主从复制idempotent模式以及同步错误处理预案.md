# (转载)MySQL主从复制idempotent模式以及同步错误处理预案

seanlook.com  原文链接 http://seanlook.com/2018/03/11/mysql-replication-error-and-idempotent/

好像链接变为 http://xgknight.com/2018/03/11/mysql-replication-error-and-idempotent/



# 1. slave_exec_mode 参数作用

`slave_exec_mode` 可以在主从复制中遇到 duplicate-key 和 no-key-found 错误时，自动覆盖或者略过binlog里面这个row_event，避免报错停止复制。

这个参数原本是解决像 NDB Cluster 多节点写入冲突的情况，也可以在普通主从、双主、环形复制等情况下解决冲突，保持幂等性。幂等性怎么定义，感兴趣的可以阅读[The differences between IDEMPOTENT and AUTO-REPAIR mode](http://http//blog.wl0.org/2016/05/the-differences-between-idempotent-and-my-suggested-auto-repair-mode/)）。

`set global slave_exec_mode=IDEMPOTENT` （可以动态修改）使从库运行在 幂等模式，对1062，1032等不同的错误类型，有不同的处理：

1. write_row event 遇到主键冲突或唯一索引冲突，这一行被覆写(delete + insert)。
   delete时候不是full value match，仅需要主键或唯一索引找到记录则删除
2. delete_row event 遇到记录不存在，忽略这一行
3. update_row event 修改唯一索引导致的冲突，忽略这一行

注意：

- idempotent 模式都是对有疑问的行进行replace或ignore，不影响其它row。
- idempotent 模式要求表上必须要有主键
- binlog必须是 FULL RBR 模式

# 2. slave-skip-errors

这个参数不能在线修改，只能加到配置文件里面或者启动的时候带上`--slave-skip-errors=1032,1062`。除非你真的理解它skip掉了什么，否则不建议使用。

讲一个我所遇到的坑。在我们的一个分库项目中，需要把一个database里面的数据拆成32份，于是做了个主从，把从库里面不需要的那份删除，但复制过来肯定会报 HA_ERR_KEY_NOT_FOUND 错误，于是这也是所期望的，就设置了`--slave-skip-errors=1032`。

但接下来就出现 1062:HA_ERR_FOUND_DUPP_KEY 错误！从库只会删数据，不会写入和更新，怎么会出现重复数据？读者不妨试想一下为什么。

这里做个说明：

```
① insert into t values (1, 'a'), (2, 'b'), (3, 'c');

② begin;
③ delete from t where id=1;
④ delete from t where id in (1, 2, 3);
⑤ insert into t where (3, 'c'), (4, 'd'), (5, 'e');
⑥ update t set ... id=1;
⑦ commit;
```

- 事务包括显式事务和隐式事务(transaction)，语句①落在binlog里面也会有begin和end
- 一个事物可以包含多个语句(statement)
- 一个语句可以影响多行(row)，但属于一个event
- 一个语句在binlog里面有多个event (row log event, table map event, xid event…)
- event在binlog里面以 event group 组合起来
  事务引擎如 InnoDB，event group 就一个事务；非事务引擎如 MyISAM，event group就是一条语句

**slave-skip-errors 参数作用的是 statement，上面的slave_exec_mode作用的是row**
比如上面那段sql在RBR复制到从库时发现④的 id=2 不存在：

- `slave_exec_mode`: ④里面的 id=2 略过，id=1,3 正常删除，事务里其它sql(row event)都正常重放

- `slave-skip-errors=1032`: 从库也会一直从 begin 执行到 end ，但④里面的 id=3 会跳过（跳过的是这个statement，而 id=1 会依然删除，不是原子操作），事务里其它sql正常重放。

  这就导致了我上面那个问题，id=3应该是被删除的但被跳过，下面在插入 id=3 的记录就 1062 了。如果再把 1062 也加入到 skip-errors，那么数据肯定会出现的丢失，是不可取的。

相关验证可以看后文。

# 3. sql_slave_skip_counter

MySQL主从复制出现异常的时候，如不及时处理，延迟的时间会越来越长，所以有时候哪怕允许极少量的数据不一致，也要让数据继续同步，往往会用到 `sql_slave_skip_counter` 参数来跳过异常事件。
用法:

```
mysql> show slave status\G -- 1062可以看到是哪条记录重复

mysql> slave stop;
mysql> set GLOBAL SQL_SLAVE_SKIP_COUNTER=1;
mysql> slave start;
```

- sql_slave_skip_counter=1
  跳过一个 event group。前面讲到对InnoDB而言，就是**跳过一个事务**。
  如果当前 binlog postion 落在 event group 中间，那么就一直跳到这个事务末尾。
- sql_slave_skip_counter=N (N>1)
  跳过 N 个 event。对不同的binlog版本会加入不同的event类型。
  [![slave_error_binlog_events](/slave_error_binlog_events.png)](http:///slave_error_binlog_events.png)
  比如上图在 pos 199 出现error，如果设置 `set global sql_slave_skip_counter=3`，那么就会以此跳过 199,264,332，每跳过一个 Skip_Counter 减去1，减到 Skip_Counter=1 的时候，如果pos还在**事务**中间，那么那么就一直跳到该事务末尾。
  (同样，在事务中出现异常之前的修改，不会回滚)

# 4. GTID复制异常处理

主从开启了GTID（`select @@gtid_mode`），就不能再用 sql_slave_skip_counter 来跳过错误，需要注册一个空gtid event来代替原本执行报错的event。比如：

```
mysql> show slave status\G
*************************** 1. row ***************************
               Slave_IO_State: Waiting for master to send event
                  Master_Host: 10.153.173.149
                  Master_User: replicator
                  Master_Port: 3027
                Connect_Retry: 60
              Master_Log_File: mysql-bin.014670
          Read_Master_Log_Pos: 181716556
               Relay_Log_File: slave-relay.028871
                Relay_Log_Pos: 166693104
        Relay_Master_Log_File: mysql-bin.014670
             Slave_IO_Running: Yes
            Slave_SQL_Running: No
                   Last_Errno: 1032
                   Last_Error: Could not execute Update_rows event on table mysql.user; Can't find record in 'user', Error_code: 1032; handler error HA_ERR_KEY_NOT_FOUND; the event's master log mysql-bin.014670, end_log_pos 166693925
                 Skip_Counter: 0
          Exec_Master_Log_Pos: 166692941
              Relay_Log_Space: 688
              Until_Condition: None
               Master_SSL_Key: 
        Seconds_Behind_Master: NULL
                Last_IO_Errno: 0
                Last_IO_Error: 
               Last_SQL_Errno: 1032
               Last_SQL_Error: Could not execute Update_rows event on table mysql.user; Can't find record in 'user', Error_code: 1032; handler error HA_ERR_KEY_NOT_FOUND; the event's master log mysql-bin.014670, end_log_pos 166693925 
  Replicate_Ignore_Server_Ids: 
             Master_Server_Id: 1088575531
                  Master_UUID: 108f89d5-d74f-11e7-942f-7cd30ac4755e
             Master_Info_File: mysql.slave_master_info
                    SQL_Delay: 0
          SQL_Remaining_Delay: NULL
      Slave_SQL_Running_State: Slave has read all relay log; waiting for the slave I/O thread to update it
           Master_Retry_Count: 86400
           Master_SSL_Crlpath: 
           Retrieved_Gtid_Set: 108f89d5-d74f-11e7-942f-7cd30ac4755e:8077-122925776
            Executed_Gtid_Set: 108f89d5-d74f-11e7-942f-7cd30ac4755e:1-122925773,
8b101f33-f327-11e7-89c3-7cd30ac333bc:1-1425,
fba62795-d74e-11e7-942e-7cd30ac4e7fc:1-630905526
                Auto_Position: 0
1 row in set (0.00 sec)
```

跳过处理：

```
mysql> stop slave;
mysql> set gtid_next='108f89d5-d74f-11e7-942f-7cd30ac4755e:122925774';
mysql> begin; commit;  -- empty trx
mysql> set gtid_next='AUTOMATIC';  -- auto position
mysql> start slave;
```

上面 gtid_next 的值 `108f89d5-d74f-11e7-942f-7cd30ac4755e:122925774` 是个会话级变量。

- uuid是 `Retrieved_Gtid_Set` 的uuid，一般是 `Master_UUID` 的值，但如果是级联复制(master -> slavel1 -> slave2)，那么要找到出错事务最原先在哪执行的
- trx_id(或叫position)是 master 上正常执行的最大id + 1，即`Executed_Gtid_Set`里面master uuid执行过的最大值 122925773 + 1

# 5. pt-slave-restart

pt-slave-restart 可以快速方便的恢复主从复制错误，并且支持普通 file:postion 和 GTID 模式。

修复的原理就是运行上面的 `sql_slave_skip_counter` 和 `gtid_next`，只是它可以自动的帮DBA识别错误码，或者匹配error_msg，stop/start slave，并且默认情况下它是一直运行 检测+修复。

```
pt-slave-restart --user=dbuser --password=xxxx --socket=/var/lib/mysql/mysql.sock --error-numbers=1032,1677,1051
```

几点说明一下：

- `--sleep`
  pt-slave-restart 循环检查 `show slave status` 的间隔时间。如果发现有异常，下次sleep time将减半，因为它假设当前有异常，那么下一个event很有可能也异常。
- `--master_uuid`
  级联复制下指定了 master_uuid 才能知道事件原始来自于哪里，好让`pt-slave-restart`知道在哪个 max_trx_id 上面 + 1。
- 在gtid模式下，pt-slave-restart 不能用在多线程复制下（即 `slave_parallel_workers>0`），因为它不知道这个GTID错误是从库哪个sql线程产生的。
- 以上所有处理错误的方法，在跳过后，都需要进行数据一致性修复(pt-table-sync)，或者重做从库。

# 6. 手动处理复制错误并修复

这种处理思路是写程序实现，遇到1032错误，在主库Binlog里面解析出before image，在从库插入，再stop/start slave；遇到1062错误，在从库删除这条数据（可以根据主库binlog after image取数据，也可以根据duplicate key中提示的重复记录），再stop/start/slave。

不需要skip操作，也不需要后续修复数据（只是不会因为有跳过event而产生不一致），如果从主库拿binl log或者从库拿relay log有困难，也可使用 `pymysql-replication` 来伪装成从库拿到出错的 binlog postion 的内容，解析再用。

当然为保险起见，已经出现不一致的还是要 pt-table-checksum 跑一下。

## 7. 附: 测试 slave_skip_errors, slave_exec_mode

```
CREATE TABLE `t_repl_test` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(30) DEFAULT NULL,
  `age` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4

insert into t_repl_test values(1,'a',10), (2,'b',20), (3,'c',30), (4,'d',40),(5,'e',50);

# 初始化测试数据
# master:
delete from t_repl_test where id=2;

# slave:
delete from t_repl_test where id=3; insert into t_repl_test values(2,'b',20);
```

每次测试前，数据都初始化成下面的：

| master                                   | slave                                    |
| ---------------------------------------- | ---------------------------------------- |
| `mysql> select * from t_repl_test;+—-+——+——+| id | name | age  |+—-+——+——+|  1 | a    |   10 ||  3 | c    |   30 ||  4 | d    |   40 ||  5 | e    |   50 |+—-+——+——+*` | `mysql> select  from t_repl_test;+—-+——+——+| id | name | age  |+—-+——+——+|  1 | a    |   10 ||  2 | b    |   20 ||  4 | d    |   40 ||  5 | e    |   50 |+—-+——+——+` |

### 7.1 delete 测试

**1. slave_skip_errors=1032,1062**
slave:

```
mysql> select @@slave_skip_errors, @@slave_exec_mode;
+---------------------+-------------------+
| @@slave_skip_errors | @@slave_exec_mode |
+---------------------+-------------------+
| 1032,1062           | STRICT            |
+---------------------+-------------------+
1 row in set (0.00 sec)
```

| master(每轮测试都执行)                          | slave                               |
| ---------------------------------------- | ----------------------------------- |
| `mysql> begin; mysql> delete from t_repl_test where id in (1,3,4); mysql> delete from t_repl_test where id in (5); mysql> commit;` | `mysql> select * from t_repl_test;` |

在从库，1和5被删除，4被跳过了，`skip_error=1032`作用在statement上，并且已经部分成功了的statement 不会回滚。

**2. slave_exec_mode=IDEMPOTENT**
复原。不是设置skip, 设置idempotent， slave:

```
mysql> select @@slave_skip_errors, @@slave_exec_mode;
+---------------------+-------------------+
| @@slave_skip_errors | @@slave_exec_mode |
+---------------------+-------------------+
| OFF                 | IDEMPOTENT        |
+---------------------+-------------------+

mysql> select * from t_repl_test;
+----+------+------+
| id | name | age  |
+----+------+------+
|  2 | b    |   20 |
+----+------+------+
```

这次1, 4, 5都被删除，也就是4是一个 statement 里面某一个row_event，没有受到 id=3 error 1032的影响。

**注意**
如果slave同时设置 slave_skip_errors 和 slave_exec_mode，那么优先生效的是 slave_skip_errors。

### 7.2 insert

**1. slave_skip_errors=1032,1062 slave_exec_mode=STRICT**

master(每轮测试都执行)

| master(每轮测试都执行)                          | slave                                    |
| ---------------------------------------- | ---------------------------------------- |
| `mysql> begin;mysql> insert into t_repl_test values(6,’f’,60),(2,’bb’,200),(7,’g’,70);Query OK, 3 rows affected (0.00 sec)mysql> insert into t_repl_test values(8,’h’,80);Query OK, 1 row affected (0.01 sec)mysql> commit;` | `mysql> select * from t_repl_test;+—-+——+——+| id | name | age  |+—-+——+——+|  1 | a    |   10 ||  2 | b    |   20 ||  4 | d    |   40 ||  5 | e    |   50 ||  6 | f    |   60 ||  8 | h    |   80 |+—-+——+——+` |

6成功，2和7失败，8成功。与delete作用范围一致。

**2. slave_skip_errors=OFF slave_exec_mode=IDEMPOTENT**
slave:

```
mysql> select @@slave_skip_errors, @@slave_exec_mode;
+---------------------+-------------------+
| @@slave_skip_errors | @@slave_exec_mode |
+---------------------+-------------------+
| OFF                 | IDEMPOTENT        |
+---------------------+-------------------+

mysql> select * from t_repl_test;
+----+------+------+
| id | name | age  |
+----+------+------+
|  1 | a    |   10 |
|  2 | bb   |  200 |
|  4 | d    |   40 |
|  5 | e    |   50 |
|  6 | f    |   60 |
|  7 | g    |   70 |
|  8 | h    |   80 |
+----+------+------+

```

6, 7, 8 都插入成功，id=2的id=2被更新。所以从库在 idempotent 模式下遇到1062，是replace操作。

**3. slave_skip_errors=OFF slave_exec_mode=IDEMPOTENT unique_key**
再来看一个好玩的（id是主键，name是唯一索引）: 从库应用relay log遇到 Duplicate entry 错误有不同处理动作。

master

```
mysql> select  from t_repl_test;
+—-+——+——+
| id | name | age  |
+—-+——+——+
|  1 | a    |   10 |
|  3 | c    |   30 |
|  4 | d    |   40 |
+—-+——+——+
3 rows in set (0.00 sec)

mysql> insert into t_repl_test values(9,’b’,200);
Query OK, 1 row affected (0.00 sec)

mysql> update t_repl_test set name=’e’ where id=4;
Query OK, 1 row affected (0.01 sec)
Rows matched: 1  Changed: 1  Warnings: 0

mysql> select  from t_repl_test;
+—-+——+——+
| id | name | age  |
+—-+——+——+
|  1 | a    |   10 |
|  3 | c    |   30 |
|  4 | e    |   40 |
|  9 | b    |  200 |
+—-+——+——+
4 rows in set (0.00 sec)
```

slave

```
mysql> select  from t_repl_test;
+—-+——+——+
| id | name | age  |
+—-+——+——+
|  1 | a    |   10 |
|  2 | b    |   20 |
|  4 | d    |   40 |
|  5 | e    |   50 |
+—-+——+——+
4 rows in set (0.00 sec)








mysql> select  from t_repl_test;
+—-+——+——+
| id | name | age  |
+—-+——+——+
|  1 | a    |   10 |
|  4 | d    |   40 |
|  5 | e    |   50 |
|  9 | b    |  200 |
+—-+——+——+
4 rows in set (0.00 sec)
```

第一条 insert 值在从库上 name=b 已经存在，违反唯一约束，所以被 **replace** 掉了。
第二条 update 值在从库上 name=e 已经存在，违反唯一约束，在从库 **被忽略** 了。看从从库的imdepotent错误日志:

```
2018-02-02 14:50:35 24325 [Warning] Slave SQL: Could not execute Update_rows event on table d_ec_crmlog.t_repl_test; 
Duplicate entry 'e' for key 'uk_name', Error_code: 1062; handler error HA_ERR_FOUND_DUPP_KEY; 
the event's master log mysql-bin.000015, end_log_pos 27072, Error_code: 1062
```

为什么会有这个行为，可以从源码里面找到答案：

```
Write_rows_log_event::do_before_row_operations()
  if ((slave_exec_mode == SLAVE_EXEC_MODE_IDEMPOTENT) ||
      (m_table->s->db_type()->db_type == DB_TYPE_NDBCLUSTER))
  {
    /*
      We are using REPLACE semantics and not INSERT IGNORE semantics
      when writing rows, that is: new rows replace old rows.  We need to
      inform the storage engine that it should use this behaviour.
    */
    
    /* Tell the storage engine that we are using REPLACE semantics. */
    thd->lex->duplicates= DUP_REPLACE;
    
    /*
      Pretend we're executing a REPLACE command: this is needed for
      InnoDB and NDB Cluster since they are not (properly) checking the
      lex->duplicates flag.
    */
    thd->lex->sql_command= SQLCOM_REPLACE;
    /* 
       Do not raise the error flag in case of hitting to an unique attribute
    */
    m_table->file->extra(HA_EXTRA_IGNORE_DUP_KEY);
    ...
  }
```

