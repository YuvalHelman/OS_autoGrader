#!/bin/bash

gcc –std=gnu99 –O3 –Wall –o pcc_server pcc_server.c –pthread
gcc –std=gnu99 –O3 –Wall –o pcc_client pcc_client.c