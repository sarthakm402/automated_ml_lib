
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, PowerTransformer,FunctionTransformer
# Feature Engineering
from sklearn.feature_selection import VarianceThreshold
import seaborn as sns
from sklearn.linear_model import LinearRegression,LogisticRegression
from sklearn.ensemble import RandomForestRegressor,RandomForestClassifier
from xgboost import XGBRegressor, XGBClassifier
from sklearn.svm import SVR
import optuna
from sklearn.model_selection import cross_val_score,train_test_split
# Model Evaluation
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    accuracy_score,
    f1_score,
)
# path=r"C:\Users\sarthak mohapatra\Downloads\archive\creditcard.csv"
# model=DataExplorer(path)
# model.stat()
# df=pd.read_csv(path)
# print(df.isnull().sum())
# print(df.isnull().mean()*100)
def detect_anomaly(df):
    """
    Detects anomalies in a dataset using the Interquartile Range (IQR) method.

    This function identifies outliers in each column of the dataframe by calculating the
    IQR and then replacing values outside the lower and upper bounds with NaN.

    Parameters:
    - df (pd.DataFrame): The dataset to process. Each column is evaluated for outliers.
    
    Returns:
    - pd.DataFrame: The processed dataset with anomalies (outliers) replaced by NaN.

    Side effects:
    - Modifies the input dataframe by replacing outliers with NaN values in place.

    Example:
    ```
    df = pd.read_csv("data.csv")
    detect_anomaly(df)
    ```

    Notes:
    - The IQR method detects outliers as those values which are more than 1.5 times the IQR above Q3 or below Q1.
    - The function applies this process column-wise, and anomalies are replaced with `np.nan`.
    """
    for i in df.columns:
           Q1= df[i].quantile(0.25)
           Q3= df[i].quantile(0.75)
           IQR=Q3-Q1
           lower_bound=Q1-(1.5*IQR)
           upper_bound=Q3+(1.5*IQR)
           df.loc[(df[i] < lower_bound) | (df[i] > upper_bound),
                  i]=np.nan
           print(f"Anomalies detected in column {i}")
def missing_values(data, impute=True, strategy="mean", drop_threshold=None):
    """
    Handles missing values in a dataset.

    Parameters:
    - data (pd.DataFrame): The dataset to process.
    - impute (bool): Whether to impute missing values.
    - strategy (str): Strategy for imputation ('mean', 'median', 'most_frequent').
    - drop_threshold (float): If specified, drops columns with missingness above this threshold.

    Returns:
    - pd.DataFrame: The processed dataset.
    """
    if drop_threshold is not None:
        missing_percentages = data.isnull().mean()
        to_drop = missing_percentages[missing_percentages > drop_threshold].index
        data = data.drop(columns=to_drop)
        print(f"Dropped columns: {list(to_drop)}")
    
    if impute:
        imputer = SimpleImputer(strategy=strategy)
        data = pd.DataFrame(imputer.fit_transform(data), columns=data.columns)
        print(f"Imputed missing values using strategy: {strategy}")
    
    return data
def scale(data, standard=True, min_max=False, power_transform=False, one_hot=False, power_method='yeo-johnson', log_transform=False, categories='auto'):
    """
    Scales or encodes the input data using various preprocessing techniques based on the specified parameters.

    This function applies a transformation or encoding to the dataset using one of the following methods:
    - StandardScaler: Scales features to have zero mean and unit variance.
    - MinMaxScaler: Scales features to a specific range, typically between 0 and 1.
    - PowerTransformer: Applies a power transformation to stabilize variance and make data more Gaussian-like.
      Supports 'yeo-johnson' (default) and 'box-cox' methods.
    - Log1p Transform: Applies a natural log transformation (log(x + 1)) to handle skewed data.
    - OneHotEncoder: Encodes categorical features into one-hot numeric arrays.

    Parameters:
    - data (pd.DataFrame or np.ndarray): The dataset to preprocess. This can be a pandas DataFrame or numpy array.
    - s (bool): If True, StandardScaler will be applied. Default is True.
    - m (bool): If True, MinMaxScaler will be applied. Default is False.
    - p (bool): If True, PowerTransformer will be applied. Default is False.
    - o (bool): If True, OneHotEncoder will be applied to categorical data. Default is False.
    - power_method (str): Method for PowerTransformer ('yeo-johnson' or 'box-cox'). Default is 'yeo-johnson'.
      'box-cox' requires all input data to be positive.
    - log_transform (bool): If True, applies the log1p transformation (log(x + 1)). Default is False.
    - categories (str or list of lists): Used by OneHotEncoder to specify how categories are handled. Default is 'auto'.

    Returns:
    - np.ndarray or pd.DataFrame: The preprocessed dataset. Returns a numpy array for scaling transformations 
      or a sparse matrix/numpy array for one-hot encoding.

    Example:
    ```python
    df = pd.read_csv("data.csv")

    # Apply PowerTransformer with 'box-cox'
    transformed_data = scale(df, s=False, p=True, power_method='box-cox')

    # Apply log1p transformation
    transformed_data = scale(df, s=False, p=False, log_transform=True)

    # Apply OneHotEncoder
    encoded_data = scale(df, s=False, o=True)
    ```

    Notes:
    - Ensure the input data is numeric for scaling and power transformations.
    - OneHotEncoder is applicable for categorical features only.
    - If multiple flags are True, the priority order is StandardScaler > MinMaxScaler > PowerTransformer > Log1p Transform > OneHotEncoder.
    """
    if standard:
        scaler = StandardScaler()
        data_transformed = scaler.fit_transform(data)
    elif min_max:
        scaler = MinMaxScaler()
        data_transformed = scaler.fit_transform(data)
    elif power_transform:
        transformer = PowerTransformer(method=power_method)
        data_transformed = transformer.fit_transform(data)
    elif log_transform:
        transformer = FunctionTransformer(func=np.log1p, validate=True)
        data_transformed = transformer.fit_transform(data)
    elif one_hot:
        encoder = OneHotEncoder(categories=categories, sparse=False)
        data_transformed = encoder.fit_transform(data)
    else:
        raise ValueError("At least one transformation method (s, m, p, log_transform, or o) must be set to True.")
    
    return data_transformed

def preprocess_features(data,variance=False,correlatiom=False, variance_threshold=0.01, correlation_threshold=0.9):
    """
    Removes low-variance features and highly correlated features from the dataset.
    
    Parameters:
    - data (pd.DataFrame): The input dataset.
    - variance_threshold (float): Minimum variance required for a feature to be retained.
    - correlation_threshold (float): Correlation threshold above which features are dropped.
    
    Returns:
    - pd.DataFrame: Dataset with low-variance and highly correlated features removed.
    """
    if variance:
     selector = VarianceThreshold(threshold=variance_threshold)
     low_variance_data = selector.fit_transform(data)
     retained_features = data.columns[selector.get_support()]
     filtered_data = pd.DataFrame(low_variance_data, columns=retained_features)

    if correlatiom:
     corr_matrix = filtered_data.corr()
     upper_tri = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
     )
     to_drop = [column for column in upper_tri.columns if any(upper_tri[column].abs() > correlation_threshold)]
     filtered_data = filtered_data.drop(columns=to_drop)

    return filtered_data
def regression_model(train, labels, models=['linear', 'random_forest', 'xgboost', 'svr'], n_trials=50):
    """
    Trains multiple regression models with hyperparameter tuning using Optuna and evaluates their performance.
    """
    X_train, X_test, y_train, y_test = train_test_split(train, labels, test_size=0.3, random_state=42)

    results = {}
    if isinstance(models, str):
        models = [models]

    def objective(trial, model_type):
        if model_type == 'random_forest':
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 20),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
            }
            model = RandomForestRegressor(**params, random_state=42)
        elif model_type == 'xgboost':
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 20),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                'subsample': trial.suggest_float('subsample', 0.5, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            }
            model = XGBRegressor(**params, random_state=42)
        elif model_type == 'svr':
            params = {
                'C': trial.suggest_float('C', 0.1, 10),
                'epsilon': trial.suggest_float('epsilon', 0.01, 1),
                'kernel': trial.suggest_categorical('kernel', ['linear', 'poly', 'rbf', 'sigmoid']),
            }
            model = SVR(**params)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        scores = cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_squared_error')
        return -np.mean(scores)

    for model_type in models:
        if model_type == 'linear':
            model = LinearRegression()
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)
            mse = mean_squared_error(y_test, predictions)
            mae = mean_absolute_error(y_test, predictions)
            r2 = r2_score(y_test, predictions)
            results['linear'] = {'model': model, 'params': None, 'mse': mse, 'mae': mae, 'r2': r2, 'predictions': predictions}
        else:
            study = optuna.create_study(direction='minimize')
            study.optimize(lambda trial: objective(trial, model_type), n_trials=n_trials)
            best_params = study.best_params
            
            if model_type == 'random_forest':
                best_model = RandomForestRegressor(**best_params, random_state=42)
            elif model_type == 'xgboost':
                best_model = XGBRegressor(**best_params, random_state=42)
            elif model_type == 'svr':
                best_model = SVR(**best_params)

            best_model.fit(X_train, y_train)
            predictions = best_model.predict(X_test)
            mse = mean_squared_error(y_test, predictions)
            mae = mean_absolute_error(y_test, predictions)
            r2 = r2_score(y_test, predictions)
            results[model_type] = {'model': best_model, 'params': best_params, 'mse': mse, 'mae': mae, 'r2': r2, 'predictions': predictions}
    print(results)
    return results


def classification_model(train, labels, models=['logistic', 'random_forest', 'xgboost'], n_trials=50):
    """
    Trains multiple classification models with hyperparameter tuning using Optuna and evaluates their performance.
    """
    X_train, X_test, y_train, y_test = train_test_split(train, labels, test_size=0.3, random_state=42)

    results = {}
    if isinstance(models, str):
        models = [models]

    def objective(trial, model_type):
        if model_type == 'random_forest':
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 20),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
            }
            model = RandomForestClassifier(**params, random_state=42)
        elif model_type == 'xgboost':
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 20),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                'subsample': trial.suggest_float('subsample', 0.5, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            }
            model = XGBClassifier(**params, random_state=42, use_label_encoder=False, eval_metric='logloss')
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
        return -np.mean(scores)

    for model_type in models:
        if model_type == 'logistic':
            model = LogisticRegression(random_state=42)
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)
            acc = accuracy_score(y_test, predictions)
            f1 = f1_score(y_test, predictions, average='weighted')
            results['logistic'] = {'model': model, 'params': None, 'accuracy': acc, 'f1_score': f1, 'predictions': predictions}
        else:
            study = optuna.create_study(direction='minimize')
            study.optimize(lambda trial: objective(trial, model_type), n_trials=n_trials)
            best_params = study.best_params

            if model_type == 'random_forest':
                best_model = RandomForestClassifier(**best_params, random_state=42)
            elif model_type == 'xgboost':
                best_model = XGBClassifier(**best_params, random_state=42, use_label_encoder=False, eval_metric='logloss')

            best_model.fit(X_train, y_train)
            predictions = best_model.predict(X_test)
            acc = accuracy_score(y_test, predictions)
            f1 = f1_score(y_test, predictions, average='weighted')
            results[model_type] = {'model': best_model, 'params': best_params, 'accuracy': acc, 'f1_score': f1, 'predictions': predictions}
    print(results)
    return results





     
     


