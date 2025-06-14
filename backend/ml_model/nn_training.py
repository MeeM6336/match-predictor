from ml_util import process_matches_nn
from nn_model import nn_cross_validate, nn_train_final_model


def main():
	X, y, df_match_id = process_matches_nn()
	best_config_overall, all_configurations_results = nn_cross_validate(X, y, df_match_id)
	nn_train_final_model(X, y, best_config_overall)
    
if __name__ == "__main__":
	main()