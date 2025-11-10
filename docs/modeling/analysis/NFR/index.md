# List of Non-Functional Requirements (NFRs)

| **ID** | **Description** |
| -------- | -------- |
| [**NFR-01**](./NFR-01.md) | The standard communication interface shall remain operational after receiving a corrupted or invalid message. |
| [**NFR-02**](./NFR-02.md) | All *GET* messages shall not alter the state of the system. |
| [**NFR-03**](./NFR-03.md) | The system shall apply and store updated configuration parameters only if they are valid. |
| [**NFR-04**](./NFR-04.md) | Important configuration parameters shall be stored in non-volatile memory. |
| [**NFR-05**](./NFR-05.md) | Boolean parameters shall be represented as unsigned 8-bit integers (`u8`), where `0` = *false* and `1` = *true*. |
