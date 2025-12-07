#include "stm32wlxx_hal.h"
#include <stdio.h>

void HAL_Init(void) {
    printf("HAL_Init called\n");
}

void HAL_GPIO_Init(GPIO_TypeDef  *GPIOx, GPIO_InitTypeDef *GPIO_Init) {
    // Mock
}

void HAL_GPIO_WritePin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin, int PinState) {
    // Mock
}

int HAL_GPIO_ReadPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin) {
    return 0; // Mock Low
}

void HAL_Delay(uint32_t Delay) {
    // Mock
}

uint32_t tick = 0;
uint32_t HAL_GetTick(void) {
    return tick++;
}

void HAL_PWR_EnterSTOP2Mode(uint8_t Regulator, uint8_t STOPEntry) {
    printf("Entering STOP2 Mode\n");
}

SPI_HandleTypeDef hspi1;

void Error_Handler(void) {
    while(1);
}

