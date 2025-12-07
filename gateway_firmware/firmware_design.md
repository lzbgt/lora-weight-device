# Plan B Gateway Firmware Design (ESP32-S3 + RAK5146 + W5500)

## 1. Architecture
The firmware is built on the **Espressif IoT Development Framework (ESP-IDF)**. It acts as a transparent bridge between the LoRa concentrator (RF) and the Network Server (IP).

### Core Components
1.  **Main Application:** Initializes hardware, manages the packet forwarder loop, and handles system health (LEDs, Watchdog).
2.  **HAL Layer (Hardware Abstraction):**
    *   **SPI Arbiter:** Manages access to the shared SPI bus for RAK5146 and W5500.
    *   **RAK5146 Driver:** Wraps the Semtech SX1302/SX1303 HAL library.
    *   **W5500 Driver:** Uses the standard ESP-IDF `esp_eth` component or WIZnet driver.
3.  **LoRa Packet Forwarder (Semtech):**
    *   **Upstream:** Polls the concentrator for RF packets -> Encapsulates in JSON/UDP -> Sends to LNS.
    *   **Downstream:** Listens for UDP from LNS -> Schedules TX on concentrator.

## 2. Pin Mapping (Matches `gateway_backup_design.md`)

| ESP32-S3 Pin | Function | Device |
| :--- | :--- | :--- |
| GPIO 1 | SPI_MOSI | Shared |
| GPIO 2 | SPI_MISO | Shared |
| GPIO 3 | SPI_CLK | Shared |
| GPIO 4 | CS | **RAK5146** |
| GPIO 5 | CS | **W5500** |
| GPIO 6 | RST | **RAK5146** |
| GPIO 7 | RST | **W5500** |
| GPIO 8 | INT | **W5500** |

## 3. Implementation Plan
Since we are simulating the build environment (no physical ESP32 connected), we will implement the **Main Application Structure** and **Mock Drivers** to demonstrate the logic.

### Directory Structure
```
/gateway_firmware
├── CMakeLists.txt
├── main/
│   ├── CMakeLists.txt
│   ├── main.c              # Entry point
│   ├── loragw_hal.c        # Mock SX1303 HAL
│   ├── packet_forwarder.c  # Packet handling logic
│   └── network_manager.c   # Ethernet/WiFi logic
└── components/             # (Optional custom components)
```

## 4. Logical Flow
1.  **Boot:** Init SPI, Reset W5500, Reset RAK5146.
2.  **Network Connect:**
    *   Try Ethernet (W5500) via DHCP.
    *   If fail, try Wi-Fi (Fallback).
    *   Wait for IP address.
3.  **Concentrator Init:**
    *   Load calibration/config (EU868/US915 params).
    *   Start SX1303.
4.  **Forwarder Loop:**
    *   **Fetch:** `lgw_receive()` from concentrator.
    *   **Process:** If packet exists, format JSON (Semtech UDP Protocol).
    *   **Send:** `sendto()` UDP packet to LNS IP:1700.
    *   **Receive:** Non-blocking `recvfrom()` for Downlinks.
    *   **Heartbeat:** Send status JSON every 30s.
