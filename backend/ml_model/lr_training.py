from ml_util import process_matches, getDateStamp
from lr_model import lr_train_model, evaluate_model, lr_train_final_model


def main():
    match_feature_lists = process_matches()
    lr_train_model(match_feature_lists)
    evaluate_model(f'lr_model_data/lr_classifier_{getDateStamp()}.pkl', f'lr_model_data/test_data_{getDateStamp()}.npz', model_name="logistic_regression")
    lr_train_final_model(f'lr_model_data/lr_classifier_{getDateStamp()}.pkl', match_feature_lists)
    
if __name__ == "__main__":
    main()