#!/usr/bin/env python3
"""
Test script for Avfall Sør MQTT

This script tests the address lookup and HTML parsing functionality
without actually publishing to MQTT.
"""

import os
import logging
from dotenv import load_dotenv
from main import AvfallSorMQTT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_address_lookup():
    """Test the address lookup functionality."""
    # Load environment variables
    load_dotenv()
    
    # Get address from environment variables
    address = os.getenv("ADDRESS")
    
    if not address:
        logger.error("ADDRESS environment variable is required")
        return False
    
    logger.info(f"Testing address lookup for: {address}")
    
    try:
        # Create an instance of AvfallSorMQTT
        avfallsor = AvfallSorMQTT()
        
        # Test address lookup
        href = avfallsor.lookup_address()
        logger.info(f"Address lookup successful. Found href: {href}")
        
        return True
    except Exception as e:
        logger.error(f"Address lookup failed: {e}")
        return False

def test_waste_calendar(href=None):
    """Test the waste calendar parsing functionality."""
    # Load environment variables
    load_dotenv()
    
    try:
        # Create an instance of AvfallSorMQTT
        avfallsor = AvfallSorMQTT()
        
        # If href is not provided, get it from address lookup
        if not href:
            href = avfallsor.lookup_address()
        
        # Test waste calendar parsing
        waste_calendar = avfallsor.fetch_waste_calendar(href)
        
        if not waste_calendar:
            logger.warning("No waste collection dates found")
            return False
        
        logger.info(f"Found {len(waste_calendar)} waste collection dates:")
        for date, waste_types in waste_calendar.items():
            logger.info(f"  {date}: {', '.join(waste_types)}")
        
        # Test next dates calculation
        next_dates = avfallsor.get_next_dates(waste_calendar)
        
        if not next_dates:
            logger.warning("No upcoming waste collection dates found")
            return False
        
        logger.info(f"Next collection dates for each waste type:")
        for waste_type, date_info in next_dates.items():
            date_str = date_info["date"].strftime("%Y-%m-%d")
            logger.info(f"  {waste_type}: {date_str} ({date_info['date_text']})")
        
        return True
    except Exception as e:
        logger.error(f"Waste calendar parsing failed: {e}")
        return False

def main():
    """Main entry point."""
    logger.info("Starting Avfall Sør MQTT test")
    
    # Test address lookup
    if not test_address_lookup():
        logger.error("Address lookup test failed")
        return 1
    
    # Test waste calendar parsing
    if not test_waste_calendar():
        logger.error("Waste calendar parsing test failed")
        return 1
    
    logger.info("All tests completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())