from ml_util import process_matches_nn, getDateStamp, db_connect
from nn_model import nn_train_model


def main():
	match_feature_lists = process_matches_nn()
	print(match_feature_lists)

	nn_train_model(match_feature_lists)
    
if __name__ == "__main__":
	main()