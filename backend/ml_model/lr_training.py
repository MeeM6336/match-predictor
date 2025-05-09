from ml_util import get_historical_matches, process_matches, getDateStamp
from lr_model import lr_train_model, evaluate_model, lr_train_final_model


def main():
    df_matches = get_historical_matches()
    matches = process_matches(df_matches)
    lr_train_model(matches)
    evaluate_model(f'lr_model_data/lr_classifier_{getDateStamp()}.pkl', f'lr_model_data/test_data_{getDateStamp()}.npz')
    lr_train_final_model(f'lr_model_data/lr_classifier_{getDateStamp()}.pkl', matches)
    
if __name__ == "__main__":
    main()