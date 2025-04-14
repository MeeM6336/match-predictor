import joblib
import pandas as pd
import os
import mysql.connector
from sklearn.linear_model import LogisticRegression
from dotenv import load_dotenv
from pathlib import Path
from ml_util import get_hth_wins

def predict_match(model):
    try:
        team_encoder = joblib.load("encoders/team_encoder.pkl")
    
    except OSError as e:
        print("Error opening encoder:", e)

    try:
        env_path = Path(__file__).resolve().parent.parent / '.env'
        load_dotenv(env_path)

        db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        cursor = db.cursor()

    except mysql.connector.Error as e:
        print("Database connection error:", e)
    
    try:
        df_matches = pd.read_sql_query("SELECT * FROM upcoming_matches WHERE outcome IS NULL", db)

    except Exception as e:
        print("Error:", e)

    for i, match_row in enumerate(df_matches.itertuples(index=False)):
        try:
            encoded_team_a = team_encoder.transform([match_row.team_a])[0]
        except:
            encoded_team_a = -1
            print("Team A not found:", match_row.team_a)
        
        try:
            encoded_team_b = team_encoder.transform([match_row.team_b])[0]
        except:
            encoded_team_b = -1
            print("Team B not found:", match_row.team_b)
        
        # Checks teams validity
        if encoded_team_a == -1 or encoded_team_b == -1:
            df_matches.iloc[i, df_matches.columns.get_loc("outcome")] = -1
            continue

        match_stat = [
            encoded_team_a, 
            encoded_team_b, 
        ]

        # Get hth wins
        hth_wins = get_hth_wins(cursor, match_row.team_a, match_row.team_b)

        # Get avg of stats
        for j, team in enumerate([match_row.team_a, match_row.team_b]):
            query = f"""
            SELECT 
                AVG(team_rating) AS team_rating, 
                AVG(avg_kda) AS avg_kda, 
                AVG(avg_kast) AS avg_kast, 
                AVG(avg_adr) AS avg_adr
            FROM (
                SELECT *
                FROM match_team_stats
                WHERE team_name = %s
                ORDER BY match_id DESC
                LIMIT 10
            ) AS recent_matches;
            """
            
            try:
                cursor.execute(query, [team])
                team_stats = cursor.fetchone()

                match_stat.extend([
                    float(team_stats[0]),
                    float(team_stats[1]),
                    float(team_stats[2]),
                    float(team_stats[3]),
                    float(hth_wins[j])
                ])

            except Exception as e:
                print("Error:", e)

        proba = model.predict_proba([match_stat])[0]
        prediction = int(proba[1] >= 0.5)
        confidence = proba[prediction]

        query = f"""
        UPDATE upcoming_matches 
            SET outcome = %s, 
            confidence = %s 
        WHERE 
            team_a = %s AND
            team_b = %s AND
            date = %s AND
            tournament_name = %s
        """
        try:
            cursor.execute(query, (
                int(prediction),
                float(confidence),
                match_row.team_a,
                match_row.team_b,
                match_row.date,
                match_row.tournament_name
            ))
            db.commit()

        except mysql.connector.Error as e:
            db.rollback()
            print("Error inserting info:", e)


def main():
    try:
        model = joblib.load("lr_model_data/lr_final_classifier_04-10-2025.pkl")
    
    except OSError as e:
        print("Error opening encoder:", e)

    predict_match(model)

if __name__ == "__main__":
    main()