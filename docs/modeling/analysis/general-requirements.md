This document defines requirements that were discussed not in formal way but rather as a high-level design guidelines of what the firmware should be able to do.

For more detailed specification, please refer to [analysis.md](./analysis.md).

## 1. Overview

This document defines the requirements and high-level design guidelines for a **platform-agnostic firmware** that supports multiple sonar modalities. The firmware must provide a flexible, modular architecture capable of operating across four generic sonar classes:

* **Echosounder**
* **Acoustic Modem**
* **Doppler Velocity Log (DVL)**
* **Multibeam Sonar**

The baseline reference hardware is the **STM32F303RETx microcontroller**, though the design must remain portable to other platforms. Platform-specific optimizations may be introduced, provided a **default C/C++ reference implementation** is available for portability.

The software architecture will be modeled using **UML diagrams** (developed with Umbrello).

---

## 2. General Requirements

1. **Multi-Transducer Support**: Compatible with at least **1 to 4 transducers**.
2. **DVL Capability**: Firmware must support Doppler Velocity Log functionality.
3. **Platform Independence**: Core functionality must remain agnostic of microcontroller family or architecture.
4. **Baseline MCU**: Reference design must run on **STM32F303RETx**.
5. **DSP Flexibility**:

   * Optimized DSP routines may target specific hardware.
   * A portable **default C/C++ fallback implementation** must always be provided.

---

## 3. Protocol Specification

The firmware must expose a **protocol interface** enabling flexible configuration and operation. Key parameters include:

* **Transmission Control**

  * Frequency range: configurable (float or BFLOAT16).
  * Transmit pattern: `uint8/16[]`
  * Transmit mode: selectable (frequency modulation, phase modulation, direct waveform, PSK, etc.).
  * Pulse duration: defines TX length and RX listening window.
  * Transmit command: includes repeat count (0 = infinite).

* **Reception Control**

  * Receive mode: echosounder, acoustic modem, frequency detector, hydrophone.
  * Raw sample rate: configurable as a multiple of TX frequency.
  * Sample precision: selectable resolution.
  * Aggregation: number of samples to accumulate.
  * Detector mode: amplitude trigger, peak trigger, transmit pattern correlation.
  * Maximum scanning distance: for automatic ranging.

* **Error Reporting**

  * NACK status codes: unsupported, invalid, etc.
  * Optional **field IDs** and **textual reasons** included in error responses.

---

## 4. Supported Features

The firmware must support the following operating modes:

1. **Echosounder**

   * Monotone Ping
   * Chirp (frequency sweep)
   * Encoded Pulses

2. **Acoustic Modem**

   * Modulation schemes: FSK, PSK, DPSK
   * Modes: TX, RX, TX/RX

3. **Hydrophone**

   * Passive receive functionality

4. **Doppler Velocity Log (DVL)**

   * Doppler velocity log functionality

5. **Multibeam Sonar**
   * Multibeam sonar functionality, TX/RX delays for beam forming

---

## 5. High-Level Control

The control subsystem must support both **manual** and **automatic** modes for:

* **Sensitivity Management**

  * TX Gain, TX Interval, RX Gain

* **Signal Profiling**

  * Profile formats: Raw, Normalized, Amplified Discrepancy, etc.
  * Profile length configurable
  * Continuous demodulation and DMA-buffered demodulation supported

---

## 6. Low-Level Control

### 6.1 Transmit (TX)

* TX Delay for beam forming
* Analog or Digital output (DAC or PWM)
* Auxiliary outputs for external references (I/Q)
* Configuration parameters:

  * Mode (MONOTONE, CHIRP, PSK, etc.)
  * Data buffering (single or double-buffered)
  * One-shot trigger
  * Gain control
  * Interval control

### 6.2 Receive (RX)

* RX Delay for beam forming
* Input can be raw or IF (I/Q hardware demodulated)
* Supported input paths: internal ADC, external ADC, analog input
* Must support internal OPAMP-based amplification and filtering
* Data acquisition:

  * DMA buffered capture (synchronous detection or full buffer)
  * Individual sample retrieval
* Configuration parameters:

  * Gain
  * Bias (DC offset)

---

## 7. Low-Level Interfaces

* **Transmit Interface**

  * `SetMode(MONOTONE, CHIRP, PSK, …)`
  * `SetData(buffer, length)`
  * `StartTX()`
  * `SetGain(value)`
  * `SetInterval(ms)`

* **Receive Interface**

  * `ConfigureDMA(buffer, size, sync_mode)`
  * `ReadSamples(N)`
  * `SetGain(value)`
  * `SetBias(offset)`

---
