#include "main.h"
#include "app_lorawan.h"
#include "hx711_driver.h"
#include "epd_driver.h"

// Pin Definitions
#define PIN_POWER_GATE_PORT  GPIOB
#define PIN_POWER_GATE_PIN   GPIO_PIN_5

#define PIN_BUTTON_PORT      GPIOB
#define PIN_BUTTON_PIN       GPIO_PIN_3

#define PIN_BAT_ADC_PORT     GPIOB
#define PIN_BAT_ADC_PIN      GPIO_PIN_4

// Constants
#define CALIBRATION_FACTOR 100.0f // Placeholder
#define REPORT_INTERVAL 3600000 // 1 hour

// Global Flags
volatile bool evt_tare = false;
volatile bool evt_toggle_mode = false;
volatile uint32_t press_start_time = 0;
volatile bool button_pressed = false;

// Global Data
int32_t tare_offset = 0;
bool display_is_kg = false; // Default: mL (approx g)

void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_ADC_Init(void);

// Button Interrupt Callback
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
    if (GPIO_Pin == PIN_BUTTON_PIN) {
        // Simple logic: In a real HAL, we'd check edge
        // Assuming this is called on both edges for now, or just FALLING
        // For simplicity, let's assume we read the pin to determine state
        if (HAL_GPIO_ReadPin(PIN_BUTTON_PORT, PIN_BUTTON_PIN) == GPIO_PIN_RESET) {
            // Pressed (Active Low)
            press_start_time = HAL_GetTick();
            button_pressed = true;
        } else {
            // Released
            if (button_pressed) {
                uint32_t duration = HAL_GetTick() - press_start_time;
                if (duration > 50 && duration < 2000) {
                    evt_tare = true;
                } else if (duration >= 2000) {
                    evt_toggle_mode = true;
                }
                button_pressed = false;
            }
        }
    }
}

int main(void) {
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();
    MX_ADC_Init();
    
    // Init Drivers
    HX711_Init();
    MX_LoRaWAN_Init();
    EPD_Init();
    EPD_ShowLogo();
    
    // Initial Join
    LoRaWAN_Join();
    
    uint32_t last_uplink = 0;

    while (1) {
        // Wakeup Action
        
        // 1. Power Up Sensor
        HAL_GPIO_WritePin(PIN_POWER_GATE_PORT, PIN_POWER_GATE_PIN, GPIO_PIN_RESET); // Enable (Low)
        HAL_Delay(400); // Settling time
        
        // 2. Read Sensor (Gain 32)
        int32_t raw_reading = HX711_Read(32);
        
        // 3. Power Down
        HAL_GPIO_WritePin(PIN_POWER_GATE_PORT, PIN_POWER_GATE_PIN, GPIO_PIN_SET); // Disable (High)
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_6, GPIO_PIN_RESET); // Ensure SCK is Low
        
        // 4. Handle Input
        if (evt_tare) {
            tare_offset = raw_reading;
            evt_tare = false;
            EPD_UpdateWeight(0.0f, display_is_kg);
        }
        
        if (evt_toggle_mode) {
            display_is_kg = !display_is_kg;
            evt_toggle_mode = false;
        }
        
        // 5. Process Weight
        float weight = (float)(raw_reading - tare_offset) / CALIBRATION_FACTOR;
        if (weight < 0) weight = 0;
        
        // Update Display periodically or on change (Logic omitted for brevity)
        EPD_UpdateWeight(weight, display_is_kg);
        
        // 6. LoRaWAN Uplink
        if (HAL_GetTick() - last_uplink > REPORT_INTERVAL) {
            uint8_t payload[4]; // Dummy payload
            payload[0] = (uint8_t)weight;
            LoRaWAN_Send(payload, 4);
            last_uplink = HAL_GetTick();
        }
        
        // 7. Sleep
        // HAL_PWR_EnterSTOP2Mode(PWR_MAINREGULATOR_ON, PWR_STOPENTRY_WFI);
        // Note: In a real app, this halts execution until interrupt (RTC or Button)
        // For simulation/mock, we just delay
        HAL_Delay(100); 
    }
}

void SystemClock_Config(void) {
    // MSI 48MHz
}

static void MX_GPIO_Init(void) {
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    // Power Gate (PB5) - Output Push Pull, Pull Up (Default OFF)
    GPIO_InitStruct.Pin = PIN_POWER_GATE_PIN;
    GPIO_InitStruct.Mode = 0; // Output
    GPIO_InitStruct.Pull = 1; // Pull Up
    HAL_GPIO_Init(PIN_POWER_GATE_PORT, &GPIO_InitStruct);
    HAL_GPIO_WritePin(PIN_POWER_GATE_PORT, PIN_POWER_GATE_PIN, GPIO_PIN_SET); // Default OFF
    
    // Button (PB3) - Input Pull Up
    GPIO_InitStruct.Pin = PIN_BUTTON_PIN;
    GPIO_InitStruct.Mode = 0; // Input
    GPIO_InitStruct.Pull = 1; // Pull Up
    HAL_GPIO_Init(PIN_BUTTON_PORT, &GPIO_InitStruct);
}

static void MX_ADC_Init(void) {
    // Init ADC for battery
}