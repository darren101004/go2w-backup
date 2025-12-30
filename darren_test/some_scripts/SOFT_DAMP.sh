source /home/unitree/github/unitree_ros2/setup.sh
echo "Standing up..."
ros2 topic pub /api/sport/request unitree_api/msg/Request '{header: {identity: {id: 0, api_id: 1004}}, parameter: "{}"}' -1 > /dev/null #STAND_UP 
sleep 3
echo "Standing down..."
ros2 topic pub /api/sport/request unitree_api/msg/Request '{header: {identity: {id: 0, api_id: 1005}}, parameter: "{}"}' -1 > /dev/null #STAND_DOWN
ros2 topic pub /api/sport/request unitree_api/msg/Request '{header: {identity: {id: 0, api_id: 1001}}, parameter: "{}"}' -1 > /dev/null #DAMP
