#pragma once

#include "network_secrets.hpp"

// Raspberry Pi 3 / Mosquitto broker used by the HK17.2 laboratory network.
#define HK17_MQTT_BROKER_URI "mqtt://192.168.1.40:1883"

#define HK17_MQTT_QOS 1
#define HK17_MQTT_KEEPALIVE_SECONDS 60
#define HK17_BASE_TOPIC "hk17"
