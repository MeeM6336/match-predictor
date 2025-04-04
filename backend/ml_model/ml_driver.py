from ml_util import get_historical_matches, process_matches
from logisticRegression import logisticRegressionClassifier

def main():
    df_matches, df_team_stats, df_map_stats = get_historical_matches()
    matches = process_matches(df_matches, df_team_stats, df_map_stats)
    logisticRegressionClassifier(matches)
    

if __name__ == "__main__":
    main()