# Firmware Design & Specification

## 1. Architecture: Professional SDK (CMake/STM32Cube)
The firmware will be developed as a standard C/C++ project using the **STM32CubeWL MCU Package** and built via **CMake**. This approach allows full control over the Sub-GHz radio stack, low-power modes, and memory layout.

### Toolchain & Environment
*   **Compiler:** `arm-none-eabi-gcc` (Latest stable).
*   **Build System:** **CMake** + **Ninja** / **Make**.
*   **SDK:** **STM32CubeWL Firmware Package** (HAL + LL Drivers).
*   **LoRaWAN Stack:** **LoRaMac-node** (Reference implementation from Semtech/ST) integrated within STM32Cube.
*   **IDE (Optional):** VS Code (with CMake Tools extension) or STM32CubeIDE (headless build support).

### Project Structure
```text
/firmware
├── CMakeLists.txt          # Main build script
├── Drivers/                # STM32 HAL/LL, CMSIS
├── Middlewares/            # LoRaWAN Stack, FreeRTOS (optional)
├── Core/
│   ├── Inc/                # Application Headers
│   └── Src/                # Application Source
│       ├── main.c          # Entry point & System Clock
│       ├── app_lorawan.c   # LoRaWAN Task/Callbacks
│       ├── hx711_driver.c  # Bit-banged or SPI-based driver
│       └── epd_driver.c    # SSD1680 E-Ink Driver
└── tools/                  # Flashing/Debugging scripts (OpenOCD/JLink)
```

## 2. Operating Logic (State Machine)
To ensure <2uA sleep current, the application will use the **STM32 Low Power Manager (LPM)** utility or a custom `EnterStopMode` routine.

### Main Loop (Bare Metal or RTOS)
Given the simplicity, a **Super-Loop with Interrupts** or a light **FreeRTOS** implementation is suitable. The logic follows:

1.  **Bootloader:** Verify system integrity, jump to App.
2.  **System Init:**
    *   Clock: MSI Range 11 (48MHz) for active, LSE (32.768kHz) for RTC/LoRa.
    *   GPIO: Set all unused pins to Analog mode (High-Z) to save power.
    *   ADC: Calibrate VREFINT.
    *   Display: Init SPI, Clear screen (White), Show Logo, then Deep Sleep Display.
3.  **LoRaWAN Join:**
    *   Load Keys from Flash/EEPROM.
    *   Send Join Request (OTAA).
    *   Wait for Join Accept.
4.  **Deep Sleep Loop:**
    *   **RTC Alarm** wakes MCU every 60 seconds.
    *   **Wakeup Action:**
        *   Enable Power Gate (`PB5` LOW).
        *   **Wait 400ms** (HX711 Output Settling Time @ 10SPS, ref: **Datasheet Table 2, Note 1**).
        *   Read HX711 (Bit-bang `PB6`/`PA15` or Hardware SPI).
        *   Disable Power Gate (`PB5` HIGH).
        *   **CRITICAL:** Set `PB6` (SCK) Low/Analog.
        *   Measure Battery (ADC `PB4`).
    *   **Logic:**
        *   **Button Event (Interrupt):**
            *   **Short Press (< 2s):** Tare (Zero current weight).
            *   **Long Press (> 2s):** Toggle Measurement Mode (Standard 2000mL <-> Extended 8.5kg).
            *   *Note:* Extended range is hardware-limited to ~8.5kg due to HX711 Gain 32 saturation at 3.3V excitation.
        *   **Artifact Rejection:**
            *   Compare `Current_Weight` vs `Previous_Weight`.
            *   If delta > `MAX_FLOW_PER_MIN` (e.g., 50ml) AND not a "Reset/Empty" event:
            *   Ignore reading (assume tube pull/bed shake).
            *   Schedule rapid re-check (e.g., in 10 seconds).
        *   Delta check: Has weight changed > 50g (Stable)? -> Update Display.
        *   Alarm check: Weight > Threshold? -> Buzzer PWM (`PA8`) + Uplink.

## 4. Pseudocode (RUI3 Style)

```cpp
#include "RAK3172_RUI3.h"

// Settings
#define REPORT_INTERVAL (60 * 60 * 1000) // 1 hour
#define ALARM_THRESHOLD_ML 1800         // 80% of 2L bag

// Pin Definitions (Match Hardware Design)
#define PIN_POWER_GATE  PB5             // P-MOSFET (Low=ON, High=OFF)
#define PIN_BUZZER      PA8             // PWM
#define PIN_HX711_SCK   PB6
#define PIN_HX711_DT    PA15            // Data
#define PIN_EINK_BUSY   PA0             // Input
#define PIN_EINK_CS     PA4
#define PIN_EINK_DC     PA1
#define PIN_EINK_RST    PB12
#define PIN_BUTTON      PB3

// HX711 Config
// FX1901 Sensitivity = 20mV/V. Full Scale V_out = 66mV (at 3.3V).
// Gain 32 Range = +/- 51.5mV.
// Max Measurable Weight = (51.5 / 66) * 11kg = ~8.5kg.

// Global Flags
volatile bool evt_tare = false;
volatile bool evt_toggle_mode = false;
volatile uint32_t press_start_time = 0;

// Global Data
int32_t tare_offset = 0;
bool display_is_kg = false; // Default: mL (approx g)

void setup() {
    // ... Init code ...
    pinMode(PIN_BUTTON, INPUT_PULLUP);
    attachInterrupt(PIN_BUTTON, buttonPressHandler, FALLING);
    attachInterrupt(PIN_BUTTON, buttonReleaseHandler, RISING);
}

void buttonPressHandler() {
    press_start_time = millis();
}

void buttonReleaseHandler() {
    uint32_t duration = millis() - press_start_time;
    // Debounce: Ignore presses < 50ms
    if (duration > 50 && duration < 2000) {
        evt_tare = true;
    } else if (duration >= 2000) {
        evt_toggle_mode = true;
    }
}

void wakeUpHandler(void *data) {
    // 1. Power Up Sensor
    digitalWrite(PIN_POWER_GATE, LOW);
    // Wait 400ms (HX711 Output Settling Time @ 10SPS, ref: Datasheet Table 2, Note 1)
    delay(400); 
    
    // 2. Read Sensor (Channel B - Gain 32)
    // WARNING: FX1901 Full Scale (11kg) Output (66mV) > HX711 Range (51.5mV).
    // Sensor will SATURATE at > 8.5kg.
    int32_t raw_reading = readHX711_ChannelB();
    
    // 3. Power Down
    digitalWrite(PIN_POWER_GATE, HIGH);
    digitalWrite(PIN_HX711_SCK, LOW);

    // 4. Handle Input
    if (evt_tare) {
        tare_offset = raw_reading;
        evt_tare = false;
        // Refresh display to show 0
        updateDisplay(0, display_is_kg);
    }
    
    if (evt_toggle_mode) {
        display_is_kg = !display_is_kg;
        evt_toggle_mode = false;
        // Force update to show new unit icon
        float weight = (raw_reading - tare_offset) * CALIBRATION_FACTOR;
        updateDisplay(weight, display_is_kg);
    }

    // 5. Process Weight
    currentWeight = (raw_reading - tare_offset) * CALIBRATION_FACTOR;
    
    // ... Logic ...
}

void updateDisplay(float val, bool is_kg) {
    // Driver code to update E-Ink with value and "mL" or "kg" icon...
}
```

## 3. Key Driver Implementation Details

### A. E-Ink (SSD1680)
*   **Driver:** Port the GoodDisplay/Waveshare C routines to STM32 HAL SPI.
*   **Optimization:** Use **Partial Refresh** for volume updates (faster, less flickering) and **Full Refresh** only once every 6 hours to clear ghosting.
*   **Power:** Ensure the display is put into "Deep Sleep Mode" (command `0x10`, data `0x01`) before the MCU sleeps.

### B. HX711 (Load Cell)
*   **Config:** **Gain 32 (Channel B)**.
    *   **Gain Calculation:**
        *   **Sensor:** FX1901 (20mV/V). Excitation 3.3V. Full Scale Output = 66mV (at 11kg/25lb).
        *   **HX711 Range (Gain 32, 3.3V):** $\pm 0.5 \times (3.3V / 32) = \pm 51.5mV$.
        *   **Analysis:** The sensor's full 11kg output (66mV) technically exceeds the ADC range (51.5mV).
        *   **Application Reality:** Max urine bag weight is ~2kg (2000mL).
        *   **Operating Point:** At 2kg, signal is approx $66mV \times (2kg / 11kg) \approx 12mV$.
        *   **Conclusion:** Gain 32 provides **best resolution** for the primary 0-2kg target. Saturation at >8.5kg is a known trade-off.
        *   *Mitigation:* If >8.5kg measurement is required, firmware must switch to Gain 64 (Channel A) or hardware must reduce excitation voltage.
*   Since the RAK3172 is fast (48MHz), bit-banging the 24-bit readout requires delays to match the HX711 timing (max 400kHz SCK).
*   **GPIO Initialization:** All GPIO pins associated with the HX711 driver (SCK, DT) must be initialized using standard HAL enumerations (e.g., `GPIO_MODE_OUTPUT_PP`, `GPIO_NOPULL`) to ensure correct and robust pin configuration.
*   **Conversion:** `Weight_g = (Raw_Value - Tare_Offset) / Calibration_Factor`.

### C. LoRaWAN (LoRaMac-node)
*   **Region:** `LORAMAC_REGION_US915` or `LORAMAC_REGION_EU868` (defined in CMake).
*   **Class:** Class A.
*   **ADR:** Enabled (Adaptive Data Rate) to save power if close to gateway.

### D. Calibration Strategy (Dual-Slope)
To ensure maximum accuracy in the primary application range (0-2000mL) while supporting extended loads:
1.  **Zone 1 (0 - 2000g):** Calibrated with a 2kg master weight. This slope is optimized for the linear region of the sensor where urine volume matters most.
2.  **Zone 2 (2000g - 8500g):** A secondary correction factor is applied to handle potential non-linearity or droop in the sensor response at higher loads.

## 4. Payload Format (Packed)
*Same as previous design, consistent with CayenneLPP or Custom.*

| Byte | Function | Range / Value |
| :--- | :--- | :--- |
| **0** | Status Flags | Bit 0: Low Batt, Bit 1: Full Alarm, Bit 2: Blockage |
| **1** | Battery % | 0-100 (derived from V_measure vs V_full) |
| **2-3** | Volume (mL) | uint16_t (Little Endian) |
| **4-5** | Flow (mL/h) | uint16_t (Little Endian) |

## 5. CMakeLists.txt Snippet
```cmake
cmake_minimum_required(VERSION 3.16)
project(UrineMonitor C CXX)

set(CMAKE_C_STANDARD 11)
set(MCU_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")

add_definitions(-DUSE_HAL_DRIVER -DSTM32WLE5xx)

# Include STM32CubeWL Sources
file(GLOB_RECURSE HAL_SOURCES "Drivers/STM32WLxx_HAL_Driver/Src/*.c")
file(GLOB_RECURSE LORA_SOURCES "Middlewares/Third_Party/LoRaWAN/LrMac/*.c")

add_executable(${PROJECT_NAME}.elf 
    Core/Src/main.c
    Core/Src/system_stm32wlxx.c
    ${HAL_SOURCES}
    ${LORA_SOURCES}
)

target_compile_options(${PROJECT_NAME}.elf PRIVATE ${MCU_FLAGS} -Wall -Os)
target_link_options(${PROJECT_NAME}.elf PRIVATE ${MCU_FLAGS} -T${CMAKE_SOURCE_DIR}/STM32WLE5CCUx_FLASH.ld -Wl,--gc-sections)
```