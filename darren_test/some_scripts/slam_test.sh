#!/bin/bash

echo "Setup unitree ros2 environment"
source /home/unitree/github/unitree_ros2/setup.sh
ros2 topic pub /api/sport/request unitree_api/msg/Request '{header: {identity: {id: 0, api_id: 1002}}, parameter: "{}"}' -1 >> /dev/null #BALANCE_STAND
ros2 topic pub /api/sport/request unitree_api/msg/Request '{header: {identity: {id: 0, api_id: 1008}}, parameter: "{\"x\": 0, \"y\": 0, \"z\": -0.8}"}' -1 >> /dev/null
ros2 topic pub /api/sport/request unitree_api/msg/Request '{header: {identity: {id: 0, api_id: 1008}}, parameter: "{\"x\": 0, \"y\": 0, \"z\": 1.6}"}' -1 >> /dev/null
ros2 topic pub /api/sport/request unitree_api/msg/Request '{header: {identity: {id: 0, api_id: 1008}}, parameter: "{\"x\": 0, \"y\": 0, \"z\": -0.8}"}' -1 >> /dev/null

ros2 topic pub /api/sport/request unitree_api/msg/Request '{header: {identity: {id: 0, api_id: 1004}}, parameter: "{}"}' -1 >> /dev/null #STAND_UP 
ros2 topic pub /api/sport/request unitree_api/msg/Request '{header: {identity: {id: 0, api_id: 1005}}, parameter: "{}"}' -1 >> /dev/null #STAND_DOWN	
ros2 topic pub /api/sport/request unitree_api/msg/Request '{header: {identity: {id: 0, api_id: 1001}}, parameter: "{}"}' -1 > /dev/null #DAMP