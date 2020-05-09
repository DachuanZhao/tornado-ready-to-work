#!/bin/bash
echo "------------------------"

base_dir="."
log_dir="${base_dir}/log"
#python="/home/zhaodachuan/anaconda3/bin/python3.7"
python="python"
conf="${base_dir}/conf/dip_kg_server.conf"
port_default=8031
conda_name="kg_online_proj"

#conda activate ${conda_name}

if [ -n "$1" ]
then
	port=$1
else
	read -p "runserver:input port number(defualt:${port_default}):" port
	if [ ! ${port} ]
	then
		port=${port_default}
	fi
fi
echo "nohup ${python} app_project.py --port=$port &"
#判断文件是否存在，如果存在则转移
if [ ! -d "./tornado.log" ];then
    time=$(date "+%Y-%m-%d-%H:%M:%S")
    mv ./tornado.log ./logs/tornado${time}.log
fi

nohup ${python} app_project.py --port=$port > tornado.log &
echo "------------------------"
#conda deactivate
echo "------------------------"
echo "------------------------"
tail -f tornado.log -n 100

