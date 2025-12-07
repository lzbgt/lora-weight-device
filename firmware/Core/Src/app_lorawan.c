#include "app_lorawan.h"

// Mock internal state
static bool joined = false;

void MX_LoRaWAN_Init(void) {
    // Init LmHandler or similar
    // Region setup
    // Class A setup
}

void LoRaWAN_Join(void) {
    // Send Join Request
    // ...
    joined = true; // Mock success
}

void LoRaWAN_Send(uint8_t *data, uint8_t len) {
    if (!joined) return;
    
    // Send Uplink
    // LmHandlerSend(...)
}
