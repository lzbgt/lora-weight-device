#ifndef __EPD_DRIVER_H
#define __EPD_DRIVER_H

#include "main.h"

void EPD_Init(void);
void EPD_ShowLogo(void);
void EPD_UpdateWeight(float weight, bool is_kg);
void EPD_Sleep(void);

#endif
