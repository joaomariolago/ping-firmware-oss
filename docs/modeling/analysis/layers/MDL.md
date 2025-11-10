# DRAFT - DO NOT USE

# **Modulation/Demodulation Layer (MDL)**

## RX Pipeline

Can capture data as u8, u16 or f32
Data enters as a input stream from the HAL
Data can enter by either sample by sample or as N samples (Buffered)
Data can be RAW or IF (I/Q)
If data is RAW it needs to be demodulated to IF (I/Q)
If data is IF it is directly passed to upper layers
Modulations supported:
- Monotone (Syncronous Detection)
- Chirp
- FSK
- PSK
- Custom (Just pass through)
Data is then passed to the DSPL for processing as a baseband stream
