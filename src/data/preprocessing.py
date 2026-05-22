import pandas as pd
import numpy as np
import re
import yaml
import os
import sys

from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataPreprocessor:
    """
    A class to handle all preprocessing for the uncleaned Amazon sales dataset.  The class
    can be configured upon initialization and transforms a raw DataFrame into a clean,
    analysis-ready format.
    """
    def __init__(self, currency_symbol: str = '₹', sales_volume_keyword: str = 'k'):
        """
        Initialize the DataPreprocessor with specific cleaning configurations.

        Args:
            currency_symbol (str): The currency symbol to be stripped from price columns.
            sales_volume_keyword (str): The keyword indicating thousands in sales/review counts.
        """
        self.currency_symbol = currency_symbol
        self.sales_volume_keyword = sales_volume_keyword.lower()
        logger.info(f"DataProcessor initialized.  Currency: '{self.currency_symbol}', Thousands keyword: '{self.sales_volume_keyword}' ")

    def _clean_sales_volume(self, val: any) -> float:
        """
        Extract numeric volume from strings
        """
        if pd.isna(val) or val == '': return 0
        if isinstance(val, (int, float)):
            return float(val)

        val = str(val).lower().replace(',', '')
        numbers = re.findall(r'(\d+\.?\d*)', val)
        if not numbers: 
            return 0.0

        num = float(numbers[0])
        if self.sales_volume_keyword in val:
            num *= 1000

        return num

    def _clean_currency(self, val: any) -> float:
        """
        Removes currency symbols and commas, returns float
        """
        if pd.isna(val) or val == '': return np.nan
        if isinstance(val, (int,float)): return float(val)

        match = re.search(r'\d+\.?\d*', val.replace(',', ''))
        return float(match.group()) if match else np.nan

    def _clean_percentage(self, val: any) -> float:
        """
        Converts '-63%' or '63 % off' to 0.63 float
        """
        if pd.isna(val) or val == '': return 0.0
        if isinstance(val, (int, float)): return float(val) / 100 if val > 1 else float(val)

        val = str(val)
        numbers = re.findall(r'(\d+\.?\d*)', val)
        return float(numbers[0]) / 100 if numbers else 0.0

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pipeline method to apply all cleaning and transformation steps.

        Args:
            df (pd.DataFrame): The raw DataFrame
        
        Returns:
            pd.DataFrame: The processed DataFrame
        """

        logger.info(f"Starting preprocessing on DataFrame with Shape {df.shape}")

        # Copies of the DataFrame is used so the original dataFrame is not modified
        clean_df = df.copy()

        # Clean Numeeric Columns
        logger.info(f"Clean numeric and currency columns")
        numeric_map = {
                        'purchased_last_month': self._clean_sales_volume,
                        'discounted_price': self._clean_currency,
                        'original_price': self._clean_currency,
                        'discounted_percentage': self._clean_percentage,
                        'total_reviews': self._clean_sales_volume,
                        'product_rating': lambda x: pd.to_numeric(str(x).split()[0], errors='coerce')
                    }
        
        for col, func in numeric_map.items():
            if col in clean_df.columns:
                clean_df[col] = clean_df[col].apply(func)
        
        # Handle Boolean Flags
        logger.info("Standardizing boolean flag columns")
        bool_cols = ['is_best_seller', 'is_sponsored', 'has_coupon', 'buy_box_availability']
        for col in bool_cols:
            if col in clean_df.columns:
                clean_df[col] = clean_df[col].fillna(False).astype(bool)
        
        # Categorical Simplification
        logger.info("Extracting product category")
        if 'product_category' in clean_df.columns:
            clean_df['main_category'] = clean_df['product_category'].astype(str).apply(lambda x: x.split('|')[0] if '|' in x else x)
        
        # Drop rows with missing critical values
        logger.info("Dropping rows with missing target or price")
        initial_rows = len(clean_df)
        clean_df.dropna(subset=['purchased_last_month', 'discounted_price'], inplace=True)
        final_rows = len(clean_df)
        logger.info(f"Dropped {initial_rows - final_rows} rows due to missing critical values.")
        logger.info(f"Preprocessing Complete. Final DataFrame Shape: {clean_df.shape}")

        return clean_df



if __name__ == "__main__":
    # Load Project Configuration
    try:
        with open('configs/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("config.yaml not found!")
        exit()
    
    # Load Raw DataSet
    raw = config['paths']['raw_data']
    try:
        df_raw = pd.read_csv(raw)
        logger.info(f"Raw data loaded from {raw}")
    except FileNotFoundError:
        logger.error(f"Raw data file not found at {raw}")
        exit()
    
    # Instantiate The Preprocessor
    preprocessor = DataPreprocessor(currency_symbol='₹', sales_volume_keyword='k')

    # Run The Transformation Pipeline
    df_clean = preprocessor.transform(df_raw)

    # Save The Processed Data
    processed_dir = config['paths']['processed_data']
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
    
    out = os.path.join(processed_dir, 'cleaned_sales_data.csv')
    df_clean.to_csv(out, index=False)

    logger.info(f"Successfully saved clean data to {out}")