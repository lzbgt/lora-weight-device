#include "hx711_driver.h"

void HX711_Init(void) {
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    // SCK Output
    GPIO_InitStruct.Pin = HX711_SCK_PIN;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(HX711_SCK_PORT, &GPIO_InitStruct);

    // DT Input
    GPIO_InitStruct.Pin = HX711_DT_PIN;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(HX711_DT_PORT, &GPIO_InitStruct);

    // Idle state
    HAL_GPIO_WritePin(HX711_SCK_PORT, HX711_SCK_PIN, GPIO_PIN_RESET);
}

uint32_t HX711_Read(uint8_t gain) {
    uint32_t count = 0;
    
    // Wait for DT to go low (ready)
    // Timeout handling should be added in production
    // while(HAL_GPIO_ReadPin(HX711_DT_PORT, HX711_DT_PIN) == GPIO_PIN_SET);

    // Pulse 24 times to read data
    for (int i = 0; i < 24; i++) {
        HAL_GPIO_WritePin(HX711_SCK_PORT, HX711_SCK_PIN, GPIO_PIN_SET);
        // Delay? 48MHz MCU -> 20ns cycle. HX711 needs ~0.2us. 
        // Simple loop delay or no delay might work if GPIO is slow enough. 
        // For safety, minimal delay.
        // HAL_Delay(0) is 1ms, too slow. Just busy loop.
        for(volatile int x=0; x<10; x++); 
        
        count = count << 1;
        HAL_GPIO_WritePin(HX711_SCK_PORT, HX711_SCK_PIN, GPIO_PIN_RESET);
        for(volatile int x=0; x<10; x++);

        if (HAL_GPIO_ReadPin(HX711_DT_PORT, HX711_DT_PIN)) {
            count++;
        }
    }

    // Additional pulses for gain selection
    // 1 pulse = Gain 128 (A)
    // 2 pulses = Gain 32 (B)
    // 3 pulses = Gain 64 (A)
    
    int pulses = 1;
    if (gain == 32) pulses = 2;
    else if (gain == 64) pulses = 3;

    for (int i = 0; i < pulses; i++) {
        HAL_GPIO_WritePin(HX711_SCK_PORT, HX711_SCK_PIN, GPIO_PIN_SET);
        for(volatile int x=0; x<10; x++);
        HAL_GPIO_WritePin(HX711_SCK_PORT, HX711_SCK_PIN, GPIO_PIN_RESET);
        for(volatile int x=0; x<10; x++);
    }

    // Convert 24-bit 2's complement to 32-bit int
    if (count & 0x800000) {
        count |= 0xFF000000;
    }
    
    return count;
}
