cmake_minimum_required(VERSION 3.16)

# This is a standard ESP-IDF project structure
set(CMAKE_C_STANDARD 11)

# Include the main component
idf_component_register(SRCS "main.c"
                       INCLUDE_DIRS ".")
