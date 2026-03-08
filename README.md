# turtlebot_dashboard
ESP32 web server for monitoring a fleet of turtlebots. Viewable at http://turtlebot-status.dyn.wpi.edu.

## Updating Files + Flashing Firmware
This project relies on the SPIFFS file system library for ESP32. In order to update the files stored on the ESP32, run this command using the PlatformIO CLI"
```bash
pio run --target uploadfs
```

## API
more on this coming soon...

## Add/Remove Turtlebots
Open `data/turtlebots.txt` and add or remove names in order of the turtlebot numbers. Make sure to leave commas and a "N" for DNS status as this file is the config file for the status table. Also update the constant `num_turtlebots` in `main.cpp` to make sure everyhting renders properly.