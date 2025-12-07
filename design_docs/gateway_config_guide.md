# RAK7268V2 Gateway Configuration Guide
## Hospital Urine Bag Monitoring System

### 1. Objective
Configure the **RAK7268V2 WisGate Edge Lite 2** to act as a **Packet Forwarder**. It will receive LoRaWAN RF packets from the sensor nodes and forward them via Ethernet/Wi-Fi to the central **ChirpStack Network Server (LNS)**.

### 2. Physical Setup
1.  **Antenna:** Connect the LoRa Antenna to the **RP-SMA** connector (Labelled "LoRa").
2.  **Power:** Connect via **PoE (Ethernet Port)** OR **12V DC Adapter**.
3.  **Network:** Connect Ethernet cable to the hospital LAN (if using PoE/Ethernet).

### 3. Accessing the Web UI
1.  **Default Wi-Fi:** The gateway broadcasts an AP named `RAK7268_xxxx` (last 4 bytes of MAC).
2.  **Connect:** Join this Wi-Fi network (Password usually `rakwireless` or printed on the label).
3.  **Browser:** Open `http://192.168.230.1`.
4.  **Login:**
    *   User: `root`
    *   Password: `root` (Change this immediately upon first login!).

### 4. Network Configuration (Uplink/Backhaul)
Navigate to **Network -> WAN**.
*   **Protocol:** `DHCP Client` (typical for Hospital LAN) or `Static IP` (if required by IT).
*   **Failover (Important):**
    *   Go to **Network -> Interface**.
    *   Enable **"Uplink Backup"**.
    *   Primary: `Ethernet (eth0)`.
    *   Backup: `WWAN` (LTE) or `Wireless` (Wi-Fi Client) if available.
    *   *Ping Watchdog:* Enable. Host: `8.8.8.8` (or LNS IP). Interval: `60s`.

### 5. LoRaWAN Configuration
Navigate to **LoRa -> Configuration**.

#### A. Mode Selection
*   **Work Mode:** `Packet Forwarder`. (Do *not* select "Built-in Network Server" unless running a standalone demo).

#### B. Channel Plan
*   **Region:** Select matches your sensors (e.g., `US915` or `EU868`).
*   **Sub-band:**
    *   **US915:** Usually **Sub-band 2** (Channels 8-15 + 65). *Crucial: Must match Firmware setting.*
    *   **EU868:** Standard.

#### C. Server Setup (Pointing to ChirpStack)
*   **Protocol:** `Semtech UDPGW` (Standard) or `Basics Station` (More secure, TLS).
*   **Server Address:** IP address or Domain of your ChirpStack LNS (e.g., `192.168.10.50` or `lora.hospital-sys.com`).
*   **Uplink Port:** `1700` (Default for UDP).
*   **Downlink Port:** `1700`.

### 6. Verification
1.  Save & Apply.
2.  Go to **Status -> LoRa**.
3.  Check **"Packet Forwarder Status"**: Should be `Up` / `Connected`.
4.  Check **"Traffic"**: Trigger a sensor node (Press Button). You should see an entry in the "Traffic" log (even if it says "CRC Error" or "Bad MIC" initially, receiving RF proves hardware works).
