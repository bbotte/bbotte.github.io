查询redis 16个db中某一个key
比如查询 name*
redis_key="name*"
for i in {0..15};do redis-cli -n ${i} keys $redis_key |sed '/^$/d';done|while read j;do echo "----------";echo $j;echo -e ""; for k in {0..15};do redis-cli -n ${k} get $j |sed '/^$/d';done ;done
