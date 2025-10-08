import psycopg2
from config.config import Config
from typing import List, Tuple, Optional, Any

class DBAdmin:
    @staticmethod
    def execute_query(queries: List[Tuple[str, Optional[Tuple]]], autocommit: bool = False, fetch: bool = False) -> Any:
        conn = None
        try:
            conn = psycopg2.connect(Config.get_durl())
            if autocommit:
                conn.autocommit = True
            cur = conn.cursor()
            
            results = []
            for query, params in queries:
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                
                if fetch:
                    results.append(cur.fetchall())
            
            if not autocommit:
                conn.commit()
            
            cur.close()
            conn.close()
            return results if fetch else None
        except Exception as e:
            if conn:
                conn.close()
            raise e

    def clean_db(self):
        self.execute_query([
            (f'DROP TABLE IF EXISTS {Config.TABLE_NAME} CASCADE;', None),
            (f'DROP TABLE IF EXISTS {Config.DOCSTORE_TABLE} CASCADE;', None)
        ], autocommit=True)

    def check_index_in_db(self):
        try:
            results = self.execute_query([
                (f"""SELECT column_name, data_type 
                     FROM information_schema.columns 
                     WHERE table_name = '{Config.TABLE_NAME}'
                     ORDER BY ordinal_position;""", None),
                (f"SELECT COUNT(*) FROM {Config.TABLE_NAME}", None),
                (f"SELECT COUNT(*) FROM {Config.TABLE_NAME} WHERE embedding IS NOT NULL", None)
            ], fetch=True)
            
            print("Table columns:")
            for col_name, col_type in results[0]:
                print(f"  {col_name}: {col_type}")
            print(f"Total rows: {results[1][0][0]}")
            print(f"Rows with embeddings: {results[2][0][0]}")
            
            return True
        except Exception as e:
            print(f"Database verification failed: {e}")
            return False
