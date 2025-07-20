"""
Database management for Bitaxe Monitor
SQLite database for storing historical mining data
"""

import sqlite3
import logging
import datetime
from typing import List, Dict, Any, Optional
import threading

class Database:
    def __init__(self, db_file="bitaxe_data.db"):
        self.db_file = db_file
        self.connection = None
        self.lock = threading.Lock()
    
    def initialize(self):
        """Initialize database and create tables"""
        try:
            self.connection = sqlite3.connect(self.db_file, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self._create_tables()
            logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")
            raise
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        with self.lock:
            cursor = self.connection.cursor()
            
            # Mining data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mining_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    hashrate REAL,
                    temperature REAL,
                    power REAL,
                    voltage REAL,
                    frequency INTEGER,
                    difficulty REAL,
                    shares_accepted INTEGER,
                    shares_rejected INTEGER,
                    uptime INTEGER,
                    fan_speed INTEGER,
                    chip_temperature REAL,
                    pool_url TEXT,
                    worker_name TEXT
                )
            ''')
            
            # Settings optimization history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    frequency INTEGER,
                    voltage REAL,
                    hashrate_before REAL,
                    hashrate_after REAL,
                    temperature_before REAL,
                    temperature_after REAL,
                    improvement_percent REAL,
                    success BOOLEAN
                )
            ''')
            
            # Share submissions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS share_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    share_type TEXT,
                    difficulty REAL,
                    accepted BOOLEAN,
                    response_time REAL
                )
            ''')
            
            # Alerts and notifications
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_type TEXT,
                    message TEXT,
                    severity TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE
                )
            ''')
            
            self.connection.commit()
    
    def insert_mining_data(self, data: Dict[str, Any]):
        """Insert mining data record"""
        with self.lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute('''
                    INSERT INTO mining_data (
                        hashrate, temperature, power, voltage, frequency,
                        difficulty, shares_accepted, shares_rejected, uptime,
                        fan_speed, chip_temperature, pool_url, worker_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('hashrate', 0),
                    data.get('temperature', 0),
                    data.get('power', 0),
                    data.get('voltage', 0),
                    data.get('frequency', 0),
                    data.get('difficulty', 0),
                    data.get('shares_accepted', 0),
                    data.get('shares_rejected', 0),
                    data.get('uptime', 0),
                    data.get('fan_speed', 0),
                    data.get('chip_temperature', 0),
                    data.get('pool_url', ''),
                    data.get('worker_name', '')
                ))
                self.connection.commit()
            except Exception as e:
                logging.error(f"Error inserting mining data: {e}")
    
    def get_recent_data(self, hours: int = 24) -> List[Dict]:
        """Get recent mining data"""
        with self.lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute('''
                    SELECT * FROM mining_data 
                    WHERE timestamp > datetime('now', '-' || ? || ' hours')
                    ORDER BY timestamp DESC
                ''', (hours,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logging.error(f"Error fetching recent data: {e}")
                return []
    
    def get_chart_data(self, hours: int = 24, limit: int = 100) -> Dict[str, List]:
        """Get data formatted for charts"""
        with self.lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute('''
                    SELECT timestamp, hashrate, temperature, power
                    FROM mining_data 
                    WHERE timestamp > datetime('now', '-' || ? || ' hours')
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (hours, limit))
                
                rows = cursor.fetchall()
                
                # Reverse to get chronological order
                rows = rows[::-1]
                
                return {
                    'timestamps': [row['timestamp'] for row in rows],
                    'hashrates': [row['hashrate'] for row in rows],
                    'temperatures': [row['temperature'] for row in rows],
                    'power': [row['power'] for row in rows]
                }
            except Exception as e:
                logging.error(f"Error fetching chart data: {e}")
                return {'timestamps': [], 'hashrates': [], 'temperatures': [], 'power': []}
    
    def insert_share_submission(self, share_data: Dict[str, Any]):
        """Insert share submission record"""
        with self.lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute('''
                    INSERT INTO share_submissions (share_type, difficulty, accepted, response_time)
                    VALUES (?, ?, ?, ?)
                ''', (
                    share_data.get('share_type', 'regular'),
                    share_data.get('difficulty', 0),
                    share_data.get('accepted', True),
                    share_data.get('response_time', 0)
                ))
                self.connection.commit()
                return cursor.lastrowid
            except Exception as e:
                logging.error(f"Error inserting share submission: {e}")
                return None
    
    def get_share_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get share submission statistics"""
        with self.lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_shares,
                        SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted_shares,
                        SUM(CASE WHEN accepted = 0 THEN 1 ELSE 0 END) as rejected_shares,
                        AVG(response_time) as avg_response_time
                    FROM share_submissions 
                    WHERE timestamp > datetime('now', '-{} hours')
                '''.format(hours))
                
                row = cursor.fetchone()
                if row:
                    total = row['total_shares'] or 0
                    accepted = row['accepted_shares'] or 0
                    rejected = row['rejected_shares'] or 0
                    
                    return {
                        'total_shares': total,
                        'accepted_shares': accepted,
                        'rejected_shares': rejected,
                        'acceptance_rate': (accepted / total * 100) if total > 0 else 0,
                        'avg_response_time': row['avg_response_time'] or 0
                    }
                else:
                    return {
                        'total_shares': 0,
                        'accepted_shares': 0,
                        'rejected_shares': 0,
                        'acceptance_rate': 0,
                        'avg_response_time': 0
                    }
            except Exception as e:
                logging.error(f"Error fetching share stats: {e}")
                return {
                    'total_shares': 0,
                    'accepted_shares': 0,
                    'rejected_shares': 0,
                    'acceptance_rate': 0,
                    'avg_response_time': 0
                }
    
    def insert_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Insert alert record"""
        with self.lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute('''
                    INSERT INTO alerts (alert_type, message, severity)
                    VALUES (?, ?, ?)
                ''', (alert_type, message, severity))
                self.connection.commit()
                return cursor.lastrowid
            except Exception as e:
                logging.error(f"Error inserting alert: {e}")
                return None
    
    def get_unacknowledged_alerts(self) -> List[Dict]:
        """Get unacknowledged alerts"""
        with self.lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute('''
                    SELECT * FROM alerts 
                    WHERE acknowledged = FALSE
                    ORDER BY timestamp DESC
                ''')
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logging.error(f"Error fetching alerts: {e}")
                return []
    
    def acknowledge_alert(self, alert_id: int):
        """Mark alert as acknowledged"""
        with self.lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute('''
                    UPDATE alerts SET acknowledged = TRUE WHERE id = ?
                ''', (alert_id,))
                self.connection.commit()
            except Exception as e:
                logging.error(f"Error acknowledging alert: {e}")
    
    def cleanup_old_data(self, retention_days: int = 30):
        """Remove old data beyond retention period"""
        with self.lock:
            try:
                cursor = self.connection.cursor()
                
                # Clean mining data
                cursor.execute('''
                    DELETE FROM mining_data 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(retention_days))
                
                # Clean share submissions
                cursor.execute('''
                    DELETE FROM share_submissions 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(retention_days))
                
                # Clean old acknowledged alerts
                cursor.execute('''
                    DELETE FROM alerts 
                    WHERE timestamp < datetime('now', '-{} days') AND acknowledged = TRUE
                '''.format(retention_days))
                
                self.connection.commit()
                logging.info(f"Cleaned up data older than {retention_days} days")
            except Exception as e:
                logging.error(f"Error cleaning up old data: {e}")
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed")
