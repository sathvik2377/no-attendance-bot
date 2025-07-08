#!/usr/bin/env python3
"""
Bot Scheduler - Manages BITSAT bot to run only during active hours (9 AM - 1 AM)
This saves Railway hours by completely stopping the bot during inactive hours.
"""

import time
import logging
import subprocess
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_active_hours():
    """Check if bot should be active (9 AM to 1 AM)"""
    now = datetime.now()
    current_hour = now.hour
    
    # Active from 9 AM (09:00) to 1 AM (01:00) next day
    # This means active: 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0
    if 9 <= current_hour <= 23 or current_hour == 0:
        return True
    return False

def wait_until_active():
    """Wait until active hours and log the waiting"""
    while not is_active_hours():
        current_time = datetime.now().strftime("%H:%M")
        logger.info(f"Waiting for active hours... Current time: {current_time} (Active: 9 AM - 1 AM)")
        time.sleep(300)  # Check every 5 minutes
    
    current_time = datetime.now().strftime("%H:%M")
    logger.info(f"Active hours reached! Starting bot at {current_time}")

def run_bot():
    """Run the main bot and handle its lifecycle"""
    try:
        logger.info("Starting BITSAT bot process...")
        
        # Run the bot as a subprocess
        process = subprocess.Popen(
            [sys.executable, 'reddit_bot.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor the bot process
        while True:
            output = process.stdout.readline()
            if output:
                # Log bot output
                print(output.strip())
            
            # Check if process has ended
            if process.poll() is not None:
                logger.info("Bot process ended")
                break
                
            # Double-check if we should still be active
            if not is_active_hours():
                logger.info("Inactive hours reached, terminating bot process")
                process.terminate()
                process.wait()
                break
        
        return process.returncode
        
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        return 1

def main():
    """Main scheduler loop"""
    logger.info("🤖 BITSAT Bot Scheduler Started")
    logger.info("⏰ Schedule: Active 9 AM - 1 AM (saves Railway hours)")
    logger.info("💰 This keeps usage under 500 hours/month for free tier")
    
    while True:
        try:
            # Wait until active hours
            if not is_active_hours():
                wait_until_active()
            
            # Run the bot during active hours
            logger.info("🚀 Starting bot for active period...")
            return_code = run_bot()
            
            if return_code != 0:
                logger.warning(f"Bot exited with code {return_code}")
            
            # After bot stops, wait until next active period
            current_time = datetime.now().strftime("%H:%M")
            logger.info(f"😴 Bot stopped at {current_time}. Waiting for next active period...")
            
            # Small delay before checking again
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            logger.info("Restarting scheduler in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()
