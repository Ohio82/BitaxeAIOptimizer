#!/usr/bin/env python3
"""
Bitaxe Gamma 601 Mining Monitor By ANDREW FREEMAN
Main entry point for the desktop application
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
import threading
import time
from config import Config
from database import Database
from gui.main_window import MainWindow
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bitaxe_monitor.log'),
        logging.StreamHandler()
    ]
)

class BitaxeMonitorApp:
    def __init__(self):
        self.config = Config()
        self.database = Database()
        self.root = None
        self.main_window = None
        self.running = False
        
    def initialize(self):
        """Initialize the application"""
        try:
            # Initialize database
            self.database.initialize()
            
            # Create main window
            self.root = tk.Tk()
            self.root.title("Bitaxe Gamma 601 Monitor")
            self.root.geometry("1200x800")
            self.root.minsize(800, 600)
            
            # Set application icon (optional, only if you have an icon file)
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            if os.path.exists(icon_path):
                try:
                    self.root.iconbitmap(default=icon_path)
                except Exception as e:
                    logging.warning(f"Could not set icon: {e}")
            # else: skip setting icon
            
            # Initialize main window
            self.main_window = MainWindow(self.root, self.config, self.database)
            
            # Configure close event
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            logging.info("Application initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize application: {e}")
            # Only show messagebox if Tkinter root is initialized
            try:
                if self.root:
                    messagebox.showerror("Initialization Error", 
                                         f"Failed to initialize application:\n{e}")
            except Exception as mb_e:
                logging.error(f"Could not show error messagebox: {mb_e}")
            return False
    
    def run(self):
        """Run the application"""
        if not self.initialize():
            return
        
        self.running = True
        
        try:
            # Start the main window
            self.main_window.start()
            
            # Start GUI main loop
            self.root.mainloop()
            
        except KeyboardInterrupt:
            logging.info("Application interrupted by user")
        except Exception as e:
            logging.error(f"Application error: {e}")
            try:
                if self.root:
                    messagebox.showerror("Application Error", f"An error occurred: {e}")
            except Exception as mb_e:
                logging.error(f"Could not show error messagebox: {mb_e}")
        finally:
            self.cleanup()
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.cleanup()
            self.root.destroy()
    
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        if self.main_window:
            try:
                self.main_window.stop()
            except Exception as e:
                logging.warning(f"Error stopping main window: {e}")
        if self.database:
            try:
                self.database.close()
            except Exception as e:
                logging.warning(f"Error closing database: {e}")
        logging.info("Application cleanup completed")

def main():
    """Main entry point"""
    try:
        app = BitaxeMonitorApp()
        app.run()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        # Only show messagebox if Tkinter root is initialized
        try:
            if 'app' in locals() and getattr(app, 'root', None):
                messagebox.showerror("Fatal Error", f"A fatal error occurred: {e}")
        except Exception as mb_e:
            logging.error(f"Could not show error messagebox: {mb_e}")
        sys.exit(1)

if __name__ == "__main__":
    main()