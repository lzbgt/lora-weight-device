#ifndef __STM32WLxx_HAL_H
#define __STM32WLxx_HAL_H

#include <stdint.h>
#include <stdbool.h>

// Mock GPIO
#define GPIO_PIN_0                 ((uint16_t)0x0001)
#define GPIO_PIN_1                 ((uint16_t)0x0002)
#define GPIO_PIN_2                 ((uint16_t)0x0004)
#define GPIO_PIN_3                 ((uint16_t)0x0008)
#define GPIO_PIN_4                 ((uint16_t)0x0010)
#define GPIO_PIN_5                 ((uint16_t)0x0020)
#define GPIO_PIN_6                 ((uint16_t)0x0040)
#define GPIO_PIN_7                 ((uint16_t)0x0080)
#define GPIO_PIN_8                 ((uint16_t)0x0100)
#define GPIO_PIN_9                 ((uint16_t)0x0200)
#define GPIO_PIN_10                ((uint16_t)0x0400)
#define GPIO_PIN_11                ((uint16_t)0x0800)
#define GPIO_PIN_12                ((uint16_t)0x1000)
#define GPIO_PIN_13                ((uint16_t)0x2000)
#define GPIO_PIN_14                ((uint16_t)0x4000)
#define GPIO_PIN_15                ((uint16_t)0x8000)

#define GPIO_PIN_RESET             0
#define GPIO_PIN_SET               1

typedef struct {
    uint32_t Pin;
    uint32_t Mode;
    uint32_t Pull;
    uint32_t Speed;
} GPIO_InitTypeDef;

// Mock GPIO Mode
#define GPIO_MODE_OUTPUT_PP        0x00000001U
#define GPIO_MODE_INPUT            0x00000000U // Default
#define GPIO_MODE_ANALOG           0x00000003U

// Mock GPIO Pull
#define GPIO_NOPULL                0x00000000U
#define GPIO_PULLUP                0x00000001U
#define GPIO_PULLDOWN              0x00000002U

// Mock GPIO Speed
#define GPIO_SPEED_FREQ_LOW        0x00000000U
#define GPIO_SPEED_FREQ_MEDIUM     0x00000001U
#define GPIO_SPEED_FREQ_HIGH       0x00000002U
#define GPIO_SPEED_FREQ_VERY_HIGH  0x00000003U

typedef struct {
} GPIO_TypeDef;

#define GPIOA ((GPIO_TypeDef *) 0x48000000)
#define GPIOB ((GPIO_TypeDef *) 0x48000400)

void HAL_GPIO_Init(GPIO_TypeDef  *GPIOx, GPIO_InitTypeDef *GPIO_Init);
void HAL_GPIO_WritePin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin, int PinState);
int HAL_GPIO_ReadPin(GPIO_TypeDef* GPIOx, uint16_t GPIO_Pin);
void HAL_Delay(uint32_t Delay);
void HAL_Init(void);
uint32_t HAL_GetTick(void);

// Power
#define PWR_MAINREGULATOR_ON 0
#define PWR_STOPENTRY_WFI    1
void HAL_PWR_EnterSTOP2Mode(uint8_t Regulator, uint8_t STOPEntry);

// Mock SPI
typedef struct {
} SPI_HandleTypeDef;
extern SPI_HandleTypeDef hspi1;

// Mock LoRaWAN
void MX_LoRaWAN_Init(void);

// Callbacks
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin);

#endif /* __STM32WLxx_HAL_H */
