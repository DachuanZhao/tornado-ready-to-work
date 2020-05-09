#!/bin/bash
echo "------------------------"

python="python"
port_default=9010

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

echo "nohup ${python} app_data_labeling_platform.py -port=$port &"
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
