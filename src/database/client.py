import sqlite3
import pandas as pd
import json
import os
import numpy as np
import google.generativeai as genai
from datetime import datetime
import streamlit as st

from src.utils.api_keys import get_google_api_key

class ProductionDB:
    def __init__(self, db_path="data/mission_critical.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Needs Table with Vector Column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS needs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                urgency INTEGER,
                category TEXT,
                latitude REAL,
                longitude REAL,
                description TEXT,
                status TEXT DEFAULT 'Pending',
                verified BOOLEAN DEFAULT 1,
                assigned_to TEXT,
                assigned_at TEXT,
                embedding BLOB,
                last_modified_at TEXT
            )
        ''')
        
        # Assignments Table for Conflict Resolution
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volunteer_name TEXT,
                need_id INTEGER,
                assigned_at TEXT,
                dispatcher_id TEXT,
                UNIQUE(need_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_all_needs(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM needs", conn)
        conn.close()
        return df

    def add_need(self, data: dict):
        """Adds a need and generates its semantic embedding."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate Embedding using Gemini
        embedding = self.generate_embedding(data['description'])
        embedding_blob = np.array(embedding).tobytes() if embedding else None
        
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO needs (urgency, category, latitude, longitude, description, status, verified, embedding, last_modified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['urgency'], data['category'], data['latitude'], data['longitude'], 
              data['description'], data.get('status', 'Pending'), data.get('verified', 1), 
              embedding_blob, now))
        
        conn.commit()
        conn.close()

    def generate_embedding(self, text: str):
        """Uses Gemini to get semantic vector embeddings."""
        try:
            api_key = get_google_api_key()
            if not api_key:
                return None
            
            genai.configure(api_key=api_key)
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding Error: {e}")
            return None

    def assign_volunteer(self, need_id, volunteer_name, dispatcher_id="System"):
        """
        Conflict Resolution: Prevents duplicate assignments using atomic DB transactions.
        If need_id is already in 'assignments', it fails.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        try:
            # 1. Start Transaction
            cursor.execute("BEGIN")
            
            # 2. Check current status
            cursor.execute("SELECT status FROM needs WHERE id = ?", (need_id,))
            res = cursor.fetchone()
            if not res or res[0] != 'Pending':
                raise Exception("Conflict: This need is no longer available for assignment.")
            
            # 3. Insert assignment (UNIQUE constraint handles race conditions)
            cursor.execute('''
                INSERT INTO assignments (volunteer_name, need_id, assigned_at, dispatcher_id)
                VALUES (?, ?, ?, ?)
            ''', (volunteer_name, need_id, now, dispatcher_id))
            
            # 4. Update need status
            cursor.execute('''
                UPDATE needs 
                SET status = 'Matched', assigned_to = ?, assigned_at = ?, last_modified_at = ?
                WHERE id = ?
            ''', (volunteer_name, now, now, need_id))
            
            conn.commit()
            return True, "Assignment Successful."
        except sqlite3.IntegrityError:
            conn.rollback()
            return False, "Conflict: This task is already assigned to someone else."
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    def semantic_search(self, query: str, top_n=5):
        """Vector Search: Finds needs matching the semantic meaning of the query."""
        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            return self.get_all_needs().head(top_n) # Fallback
            
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM needs WHERE status = 'Pending'", conn)
        conn.close()
        
        if df.empty: return df
        
        # Calculate Cosine Similarity
        def calculate_sim(blob):
            if blob is None: return 0.0
            vec = np.frombuffer(blob, dtype=np.float64)
            # Resize if necessary (model versioning check)
            if len(vec) != len(query_embedding): return 0.0
            return np.dot(vec, query_embedding) / (np.linalg.norm(vec) * np.linalg.norm(query_embedding))
            
        df['similarity'] = df['embedding'].apply(calculate_sim)
        return df.sort_values(by='similarity', ascending=False).head(top_n)

    def update_need_verification(self, need_id, status: bool):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE needs 
            SET verified = ?
            WHERE id = ?
        ''', (1 if status else 0, need_id))
        conn.commit()
        conn.close()

    def delete_need(self, need_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM needs WHERE id = ?", (need_id,))
        conn.commit()
        conn.close()

    def update_need_details(self, need_id, data: dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE needs 
            SET category = ?, urgency = ?, latitude = ?, longitude = ?, description = ?, verified = ?
            WHERE id = ?
        ''', (data['category'], data['urgency'], data['latitude'], data['longitude'], 
              data['description'], 1 if data.get('verified', True) else 0, need_id))
        conn.commit()
        conn.close()