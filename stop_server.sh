#!/bin/bash
echo "------------------------"

port_default=8031

if [ -n "$1" ]
then
	port=$1
else
	read -p "stopserver:input port number(defualt:{$port_default}):" port
	if [ ! $port ]
	then
		port=$port_default
	fi
fi

echo $port

#循环遍历杀死所有对应port的进程，因为开启了多进程
while :
do
    #根据端口号查询对应的pid
    pid=$(netstat -nlp | grep :$port | awk '{print $7}' | awk -F"/" '{ print $1 }');
    echo "kill $pid,port is $port"
    #杀掉对应的进程，如果pid不存在，则不执行
    if [  -n  "$pid"  ]
    then
        kill  $pid;
    else
        break;
    fi
done
echo "------------------------"
