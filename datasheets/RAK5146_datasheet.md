# RAK5146 LoRaWAN Gateway Module Datasheet | Specs & Features[1]

## Overview[1]
The RAK5146 is an LPWAN Concentrator Module in a mini-PCIe form factor, featuring the Semtech SX1303 and SX126X for the Listen Before Talk (LBT) feature. It allows seamless integration into existing routers or other network equipment with LPWAN Gateway capabilities. This module can be used with any embedded platform that has an available mini-PCIe slot with SPI/USB connectivity and includes an onboard ZOE-M8Q GPS chip.[1]

This concentrator offers a comprehensive and cost-efficient gateway solution, providing up to 10 programmable parallel demodulation paths, an 8 x 8 channel LoRa packet detector, 8 x SF5-SF12 LoRa demodulators, and 8 x SF5-SF10 LoRa demodulators. It can detect an uninterrupted combination of packets at 8 different spreading factors and 10 channels, and continuously demodulate up to 16 packets, making it suitable for smart metering fixed networks and Internet-of-Things (IoT) applications.[1]

## Product Features[1]
*   Designed based on Mini PCI-e form factor[1]
*   SX1303 baseband processor emulates 8 x 8 channels LoRa packet detectors, 8x SF5-SF12 LoRa demodulators, 8x SF5-SF10 LoRa demodulators, one 125/250/500 kHz high-speed LoRa demodulator, and one (G)FSK demodulator[1]
*   3.3 V Mini PCI-e, compatible with 3G/LTE card of Mini PCI-e type[1]
*   Tx power up to 27 dBm, Rx sensitivity down to -139 dBm @ SF12, BW 125 kHz[1]
*   Supports global license-free frequency band: EU868, EU433, RU864, CN470, US915, AS923, AU915, KR920, and IN865[1]
*   Supports optional SPI/USB interfaces.[1]
*   Listen Before Talk[1]
*   Fine Timestamp[1]
*   Built-in ZOE-M8Q GPS module[1]

## Specifications[1]

### Overview[1]
The overview shows the top and back views of the RAK5146 board and presents a block diagram.[1]

#### Board Overview[1]
The RAK5146 is a compact LPWAN Gateway Module suitable for integration in systems with mass and size constraints. It is designed with the PCI Express Mini Card form factor, allowing it to be part of products complying with the standard, provided they allow cards with a thickness of at least 5.5 mm. The board has two UFL interfaces for the LoRa and GNSS antennas and a standard 52-pin connector (mPCIe).[1]

#### Block Diagram[1]
The RAK5146 concentrator is equipped with one SX1303 chip and two SX1250 chips. The SX1303 chip is used for RF signal processing and serves as the core, while the SX1250 chips handle related LoRa modem and processing functionalities. Additional signal conditioning circuitry is implemented to comply with the PCI Express Mini Card standard, and one UFL connector is provided for external antenna integration.[1]

### Hardware[1]
The hardware section is categorized into seven parts, discussing interfacing, pinouts, functions, diagrams, parameters, and standard values.[1]

#### Interfaces[1]
*   **Power Supply:** The RAK5146 concentrator module must be powered through the 3.3 Vaux pins by a DC power supply. Voltage stability is crucial due to varying current draw.[1]
*   **SPI Interface:** Provides access to the SX1303 configuration register via a synchronous full-duplex protocol, with only the slave side implemented.[1]
*   **USB Interface:** Provides access to the SX1303 configuration register via an MCU STM32L412KBU6, with only the slave side implemented.[1]
*   **UART and I2C Interface:** The RAK5146 integrates a ZOE-M8Q GPS module supporting both UART and I2C interfaces. The PINs on the golden finger provide direct access to the GPS module. The PPS (Pulse Per Second) signal is connected internally to the SX1303 and the golden finger.[1]
*   **GPS_PPS:** Includes GPS_PPS input for received packets time-stamped and Fine timestamp.[1]
*   **RESET:** The RAK5146 SPI card includes a RESET active-high input signal to reset radio operations. The RAK5146 USB card's RESET is controlled by the MCU.[1]
*   **Antenna RF Interface:** The module has one RF interface over a standard UFL connector (Hirose U. FL-R-SMT) with a characteristic impedance of 50 Ω. The RF port (J1) supports both Tx and Rx.
[1]
#### Pin Definition
[1]A table defines the pinout, including mPCIe Pin Rev. 2.0, RAK5146 Pin, Type, Description, and Remarks for each pin.
[1]
#### LED Definition
[1]A figure illustrates the RAK5146 LED Definition.
[1]
### RF Characteristics
[1]
#### Operating Frequencies
[1]The board supports the following LoRaWAN frequency channels:
[1]*   **Europe:** EU868, EU433
[1]*   **North America:** US915
[1]*   **Russia:** RU864
[1]*   **Asia:** AS923
[1]*   **Australia:** AU915
[1]*   **Korea:** KR920
[1]*   **India:** IN865
[1]*   **China:** CN470
[1]
#### RF Characteristics
[1]A table provides typical sensitivity levels of the RAK5146 concentrator module for different signal bandwidths and spreading factors.
[1]
### Electrical Requirements
[1]Exceeding specified limits in the Absolute Maximum Ratings can permanently damage the device. These ratings are for stress testing only, and operation outside the defined Operating Conditions should be avoided.
[1]
#### Absolute Maximum Rating
[1]A table lists the limiting values according to the Absolute Maximum Rating System (IEC 134) for module supply voltage, USB D+/D- pins, RESET input, SPI interface, GPS_PPS input, antenna ruggedness, and storage temperature.
[1]
**Warning:** The product is not protected against overvoltage or reversed voltages.
[1]
#### Maximum ESD
[1]A table lists the maximum ESD values for ESD_HBM and ESD_CDM.
[1]
**Note:** The module is susceptible to damage from electrostatic discharge (ESD).
[1]
#### Power Consumption
[1]A table shows the power consumption in Active Mode (TX) and Active Mode (RX).
[1]
#### Power Supply Range
[1]A table specifies the minimum, typical, and maximum module supply operating input voltage.
[1]
### Mechanical Characteristics
[1]The board weighs 16.3 grams, is 30 mm wide, and 50.96 mm tall. Its dimensions fall within the PCI Express Mini Card Electromechanical Specification, except for its thickness (5.5 mm at its thickest).
[1]
### Environmental Requirements
[1]
#### Operating Conditions
[1]A table specifies the normal operating temperature range.
[1]
**Note:** All operating condition specifications are based on an ambient temperature of 25° C unless otherwise specified.

[1]### Schematic Diagram
T[1]he RAK5146 concentrator module is based on Semtech's reference design for the SX1303. The SPI interface is available on the PCIe connector. A figure illustrates the minimum application schematic, requiring at least 3.3 V / 1 A DC power and the SPI interface connected to the main processor.

[1]### Models / Bundles
T[1]he RAK5146's variation is defined as RAK5146 - XYZ, where X, Y, Z represent the model variant. Tables explain the different variants and their specifications based on supported region, interface type, and additional features (LBT, GPS).

[1]### Certification
T[1]he product has various certifications, including ANATEL, CE, FCC, IMDA, ISED, JRL, KC, MIC, MOC, NCC, NCC, RCM, REACH, RoHS, SIRIM, SUTEL, UKCA, and WPC.[1]

Sources:
[1] RAK5146 LoRaWAN Gateway Module Datasheet | Specs &amp; Features (https://docs.rakwireless.com/product-categories/wislink/rak5146/datasheet/)