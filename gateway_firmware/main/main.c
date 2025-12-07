#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_log.h"
#include "esp_eth.h"

// Constants
#define TAG "GW_MAIN"
#define LORAGW_SPI_HOST SPI2_HOST

// Pin Definitions (Matches Design)
#define PIN_SPI_MOSI 1
#define PIN_SPI_MISO 2
#define PIN_SPI_CLK  3
#define PIN_CS_RAK   4
#define PIN_CS_ETH   5
#define PIN_RST_RAK  6
#define PIN_RST_ETH  7
#define PIN_INT_ETH  8

// Global State
static bool network_connected = false;

// Mock LoRa HAL functions (Simulating semtech-loragw-hal)
int lgw_start(void) {
    ESP_LOGI(TAG, "SX1303 Concentrator Started");
    return 0; // Success
}

int lgw_receive(uint8_t max_pkt, void *pkt_data) {
    // Mock: Simulate receiving a packet every 10 seconds
    static uint32_t last_pkt_time = 0;
    uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
    
    if (now - last_pkt_time > 10000) {
        last_pkt_time = now;
        ESP_LOGI(TAG, "Simulated LoRa Packet Received (RSSI -50dBm)");
        return 1; // 1 Packet
    }
    return 0;
}

// Network Task
void network_task(void *pvParameters) {
    // In real FW: Init ESP-ETH with W5500 driver
    ESP_LOGI(TAG, "Initializing W5500 Ethernet...");
    vTaskDelay(pdMS_TO_TICKS(1000));
    
    ESP_LOGI(TAG, "Ethernet Connected. IP: 192.168.1.105");
    network_connected = true;
    
    while(1) {
        // Monitor link status
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

// Packet Forwarder Task
void packet_forwarder_task(void *pvParameters) {
    // Wait for network
    while(!network_connected) {
        vTaskDelay(pdMS_TO_TICKS(100));
    }
    
    // Start Concentrator
    if (lgw_start() != 0) {
        ESP_LOGE(TAG, "Failed to start LoRa Concentrator");
        vTaskDelete(NULL);
    }
    
    // Main Loop
    while(1) {
        // 1. Poll LoRa
        int nb_pkt = lgw_receive(1, NULL);
        
        if (nb_pkt > 0) {
            // 2. Format Semtech UDP Packet (JSON)
            // { "rxpk": [ { "tmst": ..., "freq": 915.2, ... "data": "..." } ] }
            char *json_payload = "{\"rxpk\":[{\"tmst\":12345,\"freq\":915.2,\"data\":\"AQE=\"}]}";
            
            // 3. Send UDP (Mock)
            ESP_LOGI(TAG, "Forwarding UDP Packet to Server: %s", json_payload);
        }
        
        // 4. Jitter Delay
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void app_main(void) {
    ESP_LOGI(TAG, "Starting Plan B Gateway Firmware...");
    
    // 1. Init GPIOs (Reset lines)
    gpio_config_t io_conf = {};
    io_conf.pin_bit_mask = (1ULL << PIN_RST_RAK) | (1ULL << PIN_RST_ETH);
    io_conf.mode = GPIO_MODE_OUTPUT;
    gpio_config(io_conf);
    
    // Reset Sequence
    gpio_set_level(PIN_RST_RAK, 1); // Assert Reset (Active High for RAK?) 
    // Wait...
    gpio_set_level(PIN_RST_RAK, 0); // Release
    
    // 2. Create Tasks
    xTaskCreate(network_task, "network_task", 4096, NULL, 5, NULL);
    xTaskCreate(packet_forwarder_task, "pkt_fwd_task", 4096, NULL, 5, NULL);
}
