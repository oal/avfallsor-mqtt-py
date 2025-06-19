# Avfall Sør MQTT

## Development plan

1. Load .env file where you can find address and MQTT settings.
2. Load https://avfallsor.no/wp-json/addresses/v1/address?lookup_term={address}
3. Take the value of the returned key (there is only one key), and keep track of the .href value
4. Load the href value from the previous step, which will return a HTML page.
5. Parse the HTML and get the text value of all headings ".wp-block-site-pickup-calendar__date". These are dates in plain text (Norwegian).
6. Below each heading there's any number of icons with class ".waste-icon--{type}". Keep track of all types per date.
7. Take the next upcoming date for each type, and store it in a dictionary with the type as key and the date as value.
8. Publish each type and date to MQTT as a HomeAssistant sensor.