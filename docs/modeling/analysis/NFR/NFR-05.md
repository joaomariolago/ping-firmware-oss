# NFR-05: Boolean Parameter Representation

## Requirement Statement

Boolean parameters shall be represented as unsigned 8-bit integers (`u8`), where `0` = *false* and `1` = *true*.

## Description

The system shall standardize all boolean parameter representations used in the **standard communication interface** using unsigned 8-bit integers with consistent value mapping. All boolean configuration parameters, status flags, and control states shall use `0` to represent false or disabled states and `1` to represent true or enabled states.

The system shall validate boolean parameter values and shall reject any values other than `0` or `1`. This standardization applies to all boolean parameters when they are used in the **standard communication interface**.

## Rationale

Boolean parameter representation standardization ensures:
* Consistent data interpretation across all system interfaces and protocols
* Clear and unambiguous boolean state representation
