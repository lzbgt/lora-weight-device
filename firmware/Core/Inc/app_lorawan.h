#ifndef __APP_LORAWAN_H
#define __APP_LORAWAN_H

#include "main.h"

void MX_LoRaWAN_Init(void);
void LoRaWAN_Send(uint8_t *data, uint8_t len);
void LoRaWAN_Join(void);

#endif
