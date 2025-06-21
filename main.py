#!/usr/bin/env python3
"""
Avfall Sør MQTT

This script fetches waste collection dates from Avfall Sør's website
and publishes them to MQTT as HomeAssistant sensors.
"""

import os
import json
import logging
from datetime import datetime
import re
import time
import requests
from bs4 import BeautifulSoup
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class AvfallSorMQTT:
    """Class to handle fetching waste collection dates and publishing to MQTT."""
    
    def __init__(self):
        """Initialize the class by loading environment variables."""
        # Load environment variables
        load_dotenv()
        
        # Get MQTT settings from environment variables
        self.mqtt_host = os.getenv("MQTT_HOST")
        self.mqtt_port = int(os.getenv("MQTT_PORT", 1883))
        self.mqtt_username = os.getenv("MQTT_USERNAME")
        self.mqtt_password = os.getenv("MQTT_PASSWORD")
        self.mqtt_client_id = os.getenv("MQTT_CLIENT_ID", "avfallsor-mqtt")
        self.mqtt_discovery_prefix = os.getenv("MQTT_DISCOVERY_PREFIX", "homeassistant")
        
        # Get address from environment variables
        self.address = os.getenv("ADDRESS")
        
        if not self.address:
            raise ValueError("ADDRESS environment variable is required")
        
        if not self.mqtt_host:
            raise ValueError("MQTT_HOST environment variable is required")
        
        # Initialize MQTT client
        self.mqtt_client = mqtt.Client(client_id=self.mqtt_client_id)
        if self.mqtt_username and self.mqtt_password:
            self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
    
    def lookup_address(self):
        """Lookup address and get the href value."""
        url = f"https://avfallsor.no/wp-json/addresses/v1/address?lookup_term={self.address}"
        logger.info(f"Looking up address: {self.address}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # The response has only one key, which is the address
            if not data:
                raise ValueError(f"No address found for: {self.address}")
            
            # Get the first (and only) key
            address_key = next(iter(data))
            href = data[address_key].get("href")
            
            if not href:
                raise ValueError(f"No href found for address: {self.address}")
            
            logger.info(f"Found href: {href}")
            return href
        
        except requests.RequestException as e:
            logger.error(f"Error looking up address: {e}")
            raise
    
    def fetch_waste_calendar(self, href):
        """Fetch and parse the waste calendar HTML page."""
        logger.info(f"Fetching waste calendar from: {href}")
        
        try:
            response = requests.get(href)
            response.raise_for_status()

            html = response.text
            # Find lines with <h3 ...> that also contains </h1> and replace </h1> with </h3> (Avfall Sør's HTML is invalid)
            html = re.sub(r'<h3([^>]*)>(.*?)</h1>', r'<h3\1>\2</h3>', html)
            
            soup = BeautifulSoup(html, "html.parser")
            
            # Dictionary to store dates and waste types
            waste_calendar = {}
            
            # Find all date headings
            date_headings = soup.select(".wp-block-site-pickup-calendar__date")
            
            for heading in date_headings:
                # Extract just the text directly from the heading, without considering its structure.
                date_text = heading.get_text(strip=True)

                # Find the waste types for this date
                waste_types = []
                
                # The waste types are in icons with class "waste-icon--{type}"
                # They should be siblings or children of the heading
                waste_container = heading.find_next_sibling()
                if waste_container:
                    waste_icons = waste_container.select("[class*='waste-icon--']")
                    
                    for icon in waste_icons:
                        # Extract the waste type from the class name
                        for class_name in icon.get("class", []):
                            if class_name.startswith("waste-icon--"):
                                waste_type = class_name.replace("waste-icon--", "")
                                waste_types.append(waste_type)
                
                if waste_types:
                    waste_calendar[date_text] = waste_types
            
            logger.info(f"Found {len(waste_calendar)} dates with waste collection")
            return waste_calendar
        
        except requests.RequestException as e:
            logger.error(f"Error fetching waste calendar: {e}")
            raise
    
    def get_next_dates(self, waste_calendar):
        """
        Get the next upcoming date for each waste type.
        
        Args:
            waste_calendar: Dictionary with dates as keys and lists of waste types as values
            
        Returns:
            Dictionary with waste types as keys and next dates as values
        """
        logger.info("Determining next collection dates for each waste type")
        
        # Dictionary to store the next date for each waste type
        next_dates = {}
        
        # Current date for comparison
        now = datetime.now()
        
        # Norwegian month names for parsing
        norwegian_months = {
            "januar": 1, "februar": 2, "mars": 3, "april": 4,
            "mai": 5, "juni": 6, "juli": 7, "august": 8,
            "september": 9, "oktober": 10, "november": 11, "desember": 12
        }
        
        # Parse dates and find the next one for each waste type
        for date_text, waste_types in waste_calendar.items():
            # Parse Norwegian date format (e.g., "Mandag 1. januar")
            # Extract day and month
            match = re.search(r'(\d+)\.\s+(\w+)', date_text)
            if match:
                day = int(match.group(1))
                month_name = match.group(2).lower()
                month = norwegian_months.get(month_name)
                
                if month:
                    # Assume current year, but handle December-January transition
                    year = now.year
                    if month < now.month:
                        year += 1
                    
                    try:
                        date = datetime(year, month, day)
                        
                        # Only consider future dates
                        if date >= now:
                            for waste_type in waste_types:
                                # If we haven't seen this waste type yet, or this date is earlier
                                # than the one we have, update it
                                if waste_type not in next_dates or date < next_dates[waste_type]["date"]:
                                    next_dates[waste_type] = {
                                        "date": date,
                                        "date_text": date_text
                                    }
                    except ValueError as e:
                        logger.warning(f"Invalid date: {date_text}, error: {e}")
        
        logger.info(f"Found next dates for {len(next_dates)} waste types")
        return next_dates
    
    def publish_to_mqtt(self, next_dates):
        """
        Publish waste collection dates to MQTT as HomeAssistant sensors.
        
        Args:
            next_dates: Dictionary with waste types as keys and next dates as values
        """
        logger.info("Publishing waste collection dates to MQTT")
        
        try:
            # Connect to MQTT broker
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port)
            
            for waste_type, date_info in next_dates.items():
                # Create a unique ID for this sensor
                sensor_id = f"avfallsor_{waste_type}"
                
                # Format the date for display
                date_str = date_info["date"].strftime("%Y-%m-%d")
                
                # Create the discovery topic
                discovery_topic = f"{self.mqtt_discovery_prefix}/sensor/{sensor_id}/config"
                
                # Create the state topic
                state_topic = f"avfallsor/sensor/{sensor_id}/state"
                
                # Create the discovery message
                discovery_message = {
                    "name": f"Avfall Sør {waste_type.capitalize()}",
                    "unique_id": sensor_id,
                    "state_topic": state_topic,
                    "icon": f"mdi:trash-can",
                    "device_class": "date",
                    "value_template": "{{ value }}",
                    "device": {
                        "identifiers": ["avfallsor"],
                        "name": "Avfall Sør",
                        "manufacturer": "Avfall Sør",
                        "model": "Waste Collection Calendar"
                    }
                }
                
                # Publish the discovery message
                self.mqtt_client.publish(
                    discovery_topic,
                    json.dumps(discovery_message),
                    retain=True
                )
                time.sleep(0.250)

                # Publish the state
                self.mqtt_client.publish(state_topic, date_str, retain=True)
                time.sleep(0.250)

                logger.info(f"Published {waste_type} collection date: {date_str}")
            
            # Disconnect from MQTT broker
            self.mqtt_client.disconnect()
            
        except Exception as e:
            logger.error(f"Error publishing to MQTT: {e}")
            raise
    
    def run(self):
        """Run the main process."""
        try:
            # Step 1-3: Lookup address and get href
            href = self.lookup_address()
            
            # Step 4-6: Fetch and parse waste calendar
            waste_calendar = self.fetch_waste_calendar(href)
            
            # Step 7: Get next dates for each waste type
            next_dates = self.get_next_dates(waste_calendar)
            
            # Step 8: Publish to MQTT
            self.publish_to_mqtt(next_dates)
            
            logger.info("Process completed successfully")
            
        except Exception as e:
            logger.error(f"Error in main process: {e}")
            raise

def main():
    """Main entry point."""
    try:
        avfallsor_mqtt = AvfallSorMQTT()
        avfallsor_mqtt.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())