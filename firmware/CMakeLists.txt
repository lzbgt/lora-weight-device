cmake_minimum_required(VERSION 3.16)
project(UrineMonitor C CXX)

set(CMAKE_C_STANDARD 11)
# set(MCU_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")

add_definitions(-DUSE_HAL_DRIVER -DSTM32WLE5xx)

# Source Files
file(GLOB_RECURSE APP_SOURCES "Core/Src/*.c")
# Note: Drivers and Middlewares sources would be included here in a real setup
# file(GLOB_RECURSE HAL_SOURCES "Drivers/STM32WLxx_HAL_Driver/Src/*.c")
# file(GLOB_RECURSE LORA_SOURCES "Middlewares/Third_Party/LoRaWAN/LrMac/*.c")

# Include Paths
include_directories(
    Core/Inc
    Drivers/STM32WLxx_HAL_Driver/Inc
    Middlewares/Third_Party/LoRaWAN/LrMac/Inc
)

add_executable(${PROJECT_NAME}.elf 
    ${APP_SOURCES}
    # ${HAL_SOURCES}
    # ${LORA_SOURCES}
    # Core/Src/system_stm32wlxx.c
)

# target_compile_options(${PROJECT_NAME}.elf PRIVATE ${MCU_FLAGS} -Wall -Os)
# target_link_options(${PROJECT_NAME}.elf PRIVATE ${MCU_FLAGS} -T${CMAKE_SOURCE_DIR}/STM32WLE5CCUx_FLASH.ld -Wl,--gc-sections)
