
# Prerequisites 
- Python3, Pygame

### Tested on Apple Silicon MacPro 

# How to run the project
- python3 sim.py

# Tunable parameters
-    PACKET_DELAY, The amount of simulation ticks it takes for a message to propagate
-    PACKET_LOSS_CHANCE, The odds of a packet being dropped during transmission
-    CAR_AMOUNT, The amount of simulated cars
-    ROUTER_RANGE, The range of the connection between cars
## All are initialized near the top of sim.py

# Actions
- Clicking on a vehicle will show that vehicles network knowledge
- Click on the background to deselect

# Output
- Outputs in the format of [SIM_TICK] [GLOBAL_NETWORK_KNOWLEDGE]
- SIM_TICK is the tick of the simulation...
- GLOBAL_NETWORK_KNOWLEDGE is the average knowledge of the network for all the vehicles

- Resets at 5000 ticks
- Runs 5 times to average results

