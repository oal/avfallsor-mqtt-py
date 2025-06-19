# Avfall Sør MQTT

This Python application fetches waste collection dates from Avfall Sør's website and publishes them to MQTT as HomeAssistant sensors. It allows you to integrate your waste collection schedule into your Home Assistant dashboard.

## Note: This project was written by JetBrains Junie AI agent.

## Features

- Looks up your address on Avfall Sør's website
- Parses the waste collection calendar
- Determines the next upcoming collection date for each waste type
- Publishes the information to MQTT with Home Assistant auto-discovery

## Requirements

- Python 3.13 or higher
- MQTT broker (e.g., Mosquitto)
- Home Assistant (optional, for dashboard integration)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/avfallsor-mqtt-py.git
   cd avfallsor-mqtt-py
   ```

2. Install the dependencies:
   ```
   pip install -e .
   ```

## Configuration

1. Copy the example environment file:
   ```
   cp .env.example .env
   ```

2. Edit the `.env` file with your specific settings:
   - `ADDRESS`: Your street address in Norway
   - `MQTT_HOST`: The IP address or hostname of your MQTT broker
   - `MQTT_PORT`: The port of your MQTT broker (default: 1883)
   - `MQTT_USERNAME`: Your MQTT username (if authentication is enabled)
   - `MQTT_PASSWORD`: Your MQTT password (if authentication is enabled)
   - `MQTT_CLIENT_ID`: The client ID to use for MQTT (default: avfallsor-mqtt)
   - `MQTT_DISCOVERY_PREFIX`: The Home Assistant discovery prefix (default: homeassistant)

## Usage

### Running the Main Application

Run the script:

```
python main.py
```

The script will:
1. Look up your address on Avfall Sør's website
2. Parse the waste collection calendar
3. Determine the next upcoming collection date for each waste type
4. Publish the information to MQTT

### Testing Without MQTT Publishing

To test the address lookup and HTML parsing functionality without publishing to MQTT, you can use the test script:

```
python test_avfallsor.py
```

This will:
1. Test the address lookup functionality
2. Test the waste calendar parsing
3. Display the next collection dates for each waste type

This is useful for verifying your configuration before setting up the full MQTT integration.

## Home Assistant Integration

The script automatically creates sensors in Home Assistant using the MQTT discovery protocol. The sensors will appear with names like "Avfall Sør Restavfall", "Avfall Sør Papir", etc., and will show the next collection date for each waste type.

You can add these sensors to your dashboard or use them in automations to get notifications about upcoming waste collections.

## Running as a Service

To run this script automatically, you can set it up as a service using systemd (Linux) or Task Scheduler (Windows).

### Example systemd service (Linux)

Create a file at `/etc/systemd/system/avfallsor-mqtt.service`:

```
[Unit]
Description=Avfall Sør MQTT Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/avfallsor-mqtt-py/main.py
WorkingDirectory=/path/to/avfallsor-mqtt-py
Restart=always
User=yourusername
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```
sudo systemctl enable avfallsor-mqtt.service
sudo systemctl start avfallsor-mqtt.service
```

## Troubleshooting

If you encounter issues:

1. Check your `.env` file configuration
2. Verify that your MQTT broker is running and accessible
3. Check the logs for error messages
4. Ensure your address is correctly formatted and recognized by Avfall Sør

## License

This project is licensed under the MIT License - see the LICENSE file for details.
