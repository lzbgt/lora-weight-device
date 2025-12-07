#ifndef __HX711_DRIVER_H
#define __HX711_DRIVER_H

#include "main.h"

// Define Pins (mapped to HAL)
// These should ideally be passed in init, but for this specific firmware, macros are fine.
// DT: PA15, SCK: PB6
#define HX711_DT_PORT   GPIOA
#define HX711_DT_PIN    GPIO_PIN_15
#define HX711_SCK_PORT  GPIOB
#define HX711_SCK_PIN   GPIO_PIN_6

// Prototypes
void HX711_Init(void);
uint32_t HX711_Read(uint8_t gain); // gain: 128 (A), 32 (B), 64 (A)

#endif
