delete files by time
按时间删除文件，或者做其他用途

除了最近修改的三个文件都删除,包含子文件夹，按访问时间排序
find . -name "*" -printf "%AY-%Am-%Ad %AH:%AM:%AS %p\n"|sort -rn|awk '{print $3}' |sed '1,4d'|grep -v "^.$"|xargs rm -rf

当然一个文件有 Access Modify Change，如果按 Modify 时间排序
find . -name "*" -printf "%MY-%Mm-%Md %MH:%MM:%MS %p\n"|sort -rn|awk '{print $3}' |sed '1,4d'|grep -v "^.$"|xargs rm -rf


除了最近修改的三个文件都删除，只是当前目录，没有子目录
ls -lt|sed '1,4d'
