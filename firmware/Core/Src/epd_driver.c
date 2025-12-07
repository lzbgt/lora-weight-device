#include "epd_driver.h"

void EPD_Init(void) {
    // Reset
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_RESET);
    HAL_Delay(10);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_SET);
    HAL_Delay(10);
    
    // Busy Wait
    // ...
    
    // SPI Init Command (Mock)
    // 0x12 SWRESET
    // 0x01 Driver Output Control
    // ...
}

void EPD_ShowLogo(void) {
    // Draw bitmap buffer to display RAM
    // ...
    // Update Display
}

void EPD_UpdateWeight(float weight, bool is_kg) {
    // Render text to buffer
    // Update Partial window or Full
    // ...
}

void EPD_Sleep(void) {
    // Deep Sleep command
}
