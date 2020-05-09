#!/bin/bash
echo "------------------------"

port_default=8031

if [ -n "$1" ]
then
	port=$1
else
	read -p "input port number({$port_default}):" port
	if [ ! $port ]
	then
		port=$port_default
	fi
fi
echo ". ./stop_server.sh"
. ./stop_server.sh $port
echo ". ./run_server.sh"
. ./run_server.sh $port
echo "------------------------"
