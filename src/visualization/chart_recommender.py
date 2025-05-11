"""
Chart Recommender

This module provides logic for recommending the most appropriate chart type
based on the characteristics of the data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple, Set

from .types import ChartType, ChartPurpose, ChartOptions
from .exceptions import ChartRecommendationError


class ChartRecommender:
    """
    Chart recommendation engine that analyzes data characteristics and suggests
    the most appropriate visualization type.
    """
    
    def __init__(self):
        """Initialize the chart recommender."""
        # Map of chart purposes to appropriate chart types
        self.purpose_chart_map = {
            ChartPurpose.COMPARISON: [
                ChartType.BAR, ChartType.LINE, ChartType.RADAR, 
                ChartType.HEATMAP, ChartType.BOX
            ],
            ChartPurpose.TREND: [
                ChartType.LINE, ChartType.AREA, ChartType.BAR
            ],
            ChartPurpose.DISTRIBUTION: [
                ChartType.HISTOGRAM, ChartType.BOX, ChartType.VIOLIN, 
                ChartType.SCATTER
            ],
            ChartPurpose.COMPOSITION: [
                ChartType.PIE, ChartType.DONUT, ChartType.AREA, 
                ChartType.BAR  # Stacked bar
            ],
            ChartPurpose.RELATIONSHIP: [
                ChartType.SCATTER, ChartType.BUBBLE, ChartType.HEATMAP, 
                ChartType.LINE
            ],
            ChartPurpose.GEOGRAPHIC: [
                # Geographical charts would be handled separately
                # or through specialized renderers
            ]
        }
    
    def infer_purpose(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> ChartPurpose:
        """
        Infer the primary purpose of the visualization based on the data.
        
        Args:
            data: The data to analyze
            metadata: Optional metadata about the data and its context
            
        Returns:
            The inferred chart purpose
        """
        # Default purpose if we can't infer
        default_purpose = ChartPurpose.COMPARISON
        
        # If metadata explicitly specifies a purpose, use that
        if metadata and 'purpose' in metadata:
            try:
                return ChartPurpose(metadata['purpose'])
            except (ValueError, TypeError):
                pass
        
        # Convert to pandas DataFrame for easier analysis
        df = self._to_dataframe(data)
        
        # Check for time series data (trend)
        if self._is_time_series(df):
            return ChartPurpose.TREND
        
        # Check for categorical vs numerical data
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()
        
        # If only one numeric column, likely a distribution
        if len(num_cols) == 1 and not cat_cols:
            return ChartPurpose.DISTRIBUTION
        
        # If multiple numeric columns, likely a relationship
        if len(num_cols) > 1 and not cat_cols:
            return ChartPurpose.RELATIONSHIP
        
        # If one categorical and one numeric, likely a comparison
        if len(cat_cols) == 1 and len(num_cols) == 1:
            return ChartPurpose.COMPARISON
        
        # If percentages or parts of a whole, likely composition
        if metadata and metadata.get('is_percentage', False):
            return ChartPurpose.COMPOSITION
        
        # Check if data sums to 100 or close to it (composition)
        if len(num_cols) == 1 and df[num_cols[0]].sum() > 95 and df[num_cols[0]].sum() < 105:
            return ChartPurpose.COMPOSITION
        
        # Fall back to default
        return default_purpose
    
    def recommend_chart_type(self, data: Any, options: Optional[Dict[str, Any]] = None) -> Tuple[ChartType, Dict[str, Any]]:
        """
        Recommend the most appropriate chart type for the given data.
        
        Args:
            data: The data to visualize
            options: Optional metadata and preferences
            
        Returns:
            Tuple containing the recommended chart type and options dict with additional settings
        """
        options = options or {}
        recommendations = {}
        
        # If explicitly specified, use that chart type
        if 'chart_type' in options:
            try:
                chart_type = ChartType(options['chart_type'])
                return chart_type, recommendations
            except ValueError:
                pass
        
        try:
            # Convert to pandas DataFrame for analysis
            df = self._to_dataframe(data)
            
            # Extract data characteristics
            characteristics = self._analyze_data_characteristics(df, options)
            
            # Infer the purpose of the visualization
            purpose = options.get('purpose')
            if purpose is None:
                purpose = self.infer_purpose(df, options)
            elif isinstance(purpose, str):
                try:
                    purpose = ChartPurpose(purpose)
                except ValueError:
                    purpose = self.infer_purpose(df, options)
            
            # Get appropriate chart types for this purpose
            appropriate_charts = self.purpose_chart_map.get(purpose, [ChartType.BAR])
            if not appropriate_charts:
                appropriate_charts = [ChartType.BAR]  # Default fallback
            
            # Score each chart type based on data characteristics
            chart_scores = self._score_chart_types(characteristics, appropriate_charts)
            
            # Get the highest scoring chart type
            if not chart_scores:
                chart_type = ChartType.BAR  # Default fallback
            else:
                chart_type = max(chart_scores.items(), key=lambda x: x[1])[0]
            
            # Add recommendations based on the selected chart and data
            recommendations = self._generate_recommendations(df, chart_type, characteristics)
            
            return chart_type, recommendations
            
        except Exception as e:
            raise ChartRecommendationError(f"Failed to recommend chart type: {str(e)}")
    
    def _to_dataframe(self, data: Any) -> pd.DataFrame:
        """Convert input data to a pandas DataFrame for analysis."""
        # Already a DataFrame
        if isinstance(data, pd.DataFrame):
            return data
        
        # Dictionary
        if isinstance(data, dict):
            if 'x' in data and 'y' in data:
                return pd.DataFrame({
                    'x': data['x'],
                    'y': data['y']
                })
            elif 'series' in data:
                # Multi-series data
                df_parts = []
                for series_name, series_data in data['series'].items():
                    if isinstance(series_data, dict) and 'x' in series_data and 'y' in series_data:
                        series_df = pd.DataFrame({
                            'x': series_data['x'],
                            'y': series_data['y'],
                            'series': [series_name] * len(series_data['x'])
                        })
                        df_parts.append(series_df)
                if df_parts:
                    return pd.concat(df_parts, ignore_index=True)
            else:
                # Use keys as x and values as y
                return pd.DataFrame({
                    'x': list(data.keys()),
                    'y': list(data.values())
                })
        
        # List of dictionaries
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return pd.DataFrame(data)
        
        # List of lists or tuples
        if isinstance(data, list) and data and isinstance(data[0], (list, tuple)):
            if len(data[0]) == 2:
                return pd.DataFrame(data, columns=['x', 'y'])
            else:
                return pd.DataFrame(data)
        
        # Simple list (use index as x)
        if isinstance(data, list):
            return pd.DataFrame({'y': data})
        
        # NumPy array
        if isinstance(data, np.ndarray):
            if data.ndim == 2:
                cols = ['x', 'y']
                if data.shape[1] > 2:
                    cols.extend([f'col_{i}' for i in range(2, data.shape[1])])
                return pd.DataFrame(data, columns=cols[:data.shape[1]])
            elif data.ndim == 1:
                return pd.DataFrame({'y': data})
        
        raise ValueError(f"Cannot convert data of type {type(data)} to DataFrame")
    
    def _is_time_series(self, df: pd.DataFrame) -> bool:
        """
        Check if the data appears to be a time series.
        
        Returns True if any column contains date/time data or is numeric
        and sorted in ascending order (like time).
        """
        # Check for datetime columns
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        if datetime_cols:
            return True
        
        # Check if column names suggest time
        time_indicators = ['time', 'date', 'year', 'month', 'day', 'hour', 'minute', 'second']
        for col in df.columns:
            col_lower = str(col).lower()
            if any(indicator in col_lower for indicator in time_indicators):
                return True
        
        # Check if first column is strictly increasing (like a time index)
        if df.shape[1] > 0:
            first_col = df.columns[0]
            if pd.api.types.is_numeric_dtype(df[first_col]):
                # Check if strictly increasing
                vals = df[first_col].dropna()
                if len(vals) > 3 and vals.is_monotonic_increasing and not vals.is_monotonic_decreasing:
                    return True
        
        return False
    
    def _analyze_data_characteristics(self, df: pd.DataFrame, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the characteristics of the data to inform chart selection.
        
        Returns a dictionary of characteristics.
        """
        characteristics = {}
        
        # Basic data shape
        characteristics['row_count'] = len(df)
        characteristics['column_count'] = len(df.columns)
        
        # Data types
        characteristics['has_categorical'] = len(df.select_dtypes(include=['object', 'category']).columns) > 0
        characteristics['has_numeric'] = len(df.select_dtypes(include=np.number).columns) > 0
        characteristics['has_datetime'] = len(df.select_dtypes(include=['datetime64']).columns) > 0
        
        # Count of each type
        characteristics['numeric_column_count'] = len(df.select_dtypes(include=np.number).columns)
        characteristics['categorical_column_count'] = len(df.select_dtypes(include=['object', 'category']).columns)
        characteristics['datetime_column_count'] = len(df.select_dtypes(include=['datetime64']).columns)
        
        # Series information
        characteristics['has_series'] = 'series' in df.columns or options.get('has_series', False)
        characteristics['series_count'] = df['series'].nunique() if 'series' in df.columns else 0
        
        # Specific characteristics
        if characteristics['has_numeric']:
            num_cols = df.select_dtypes(include=np.number).columns
            # Analyze the first numeric column (usually the 'y' values)
            main_col = num_cols[0] if len(num_cols) > 0 else None
            if main_col is not None:
                characteristics['min'] = df[main_col].min()
                characteristics['max'] = df[main_col].max()
                characteristics['mean'] = df[main_col].mean()
                characteristics['std'] = df[main_col].std()
                characteristics['is_zero_based'] = abs(df[main_col].min()) < 1e-10
                characteristics['all_positive'] = df[main_col].min() >= 0
                characteristics['has_negative'] = df[main_col].min() < 0
                
                # Check for percentages or parts of a whole
                sum_vals = df[main_col].sum()
                characteristics['sums_to_100'] = abs(sum_vals - 100) < 5
                characteristics['is_percentage'] = options.get('is_percentage', False) or (
                    df[main_col].max() <= 100 and df[main_col].min() >= 0 and 
                    (abs(sum_vals - 100) < 5 or abs(sum_vals - 1) < 0.05)
                )
        
        # Category characteristics
        if characteristics['has_categorical']:
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            main_cat_col = cat_cols[0] if len(cat_cols) > 0 else None
            if main_cat_col is not None:
                characteristics['category_count'] = df[main_cat_col].nunique()
                characteristics['many_categories'] = df[main_cat_col].nunique() > 10
        
        # Time characteristics
        characteristics['is_time_series'] = self._is_time_series(df)
        
        # Check for high cardinality in x values
        if 'x' in df.columns:
            characteristics['x_cardinality'] = df['x'].nunique()
            characteristics['high_x_cardinality'] = df['x'].nunique() > 20
        
        return characteristics
    
    def _score_chart_types(self, characteristics: Dict[str, Any], 
                          chart_candidates: List[ChartType]) -> Dict[ChartType, float]:
        """
        Score each chart type based on how well it fits the data characteristics.
        
        Returns a dictionary mapping chart types to scores.
        """
        scores = {}
        
        for chart_type in chart_candidates:
            score = 0.0
            
            # Scoring for BAR charts
            if chart_type == ChartType.BAR:
                # Bar charts work well for categorical data
                if characteristics.get('has_categorical', False):
                    score += 5.0
                # For comparing values across categories
                if not characteristics.get('many_categories', False):
                    score += 3.0
                else:
                    score -= 2.0  # Too many categories is bad for bar charts
                # Bar charts prefer fewer data points
                if characteristics.get('row_count', 0) <= 20:
                    score += 2.0
                if characteristics.get('row_count', 0) > 50:
                    score -= 3.0
                # Good for comparison of positive values
                if characteristics.get('all_positive', False):
                    score += 1.0
            
            # Scoring for LINE charts
            elif chart_type == ChartType.LINE:
                # Line charts are ideal for time series
                if characteristics.get('is_time_series', False):
                    score += 10.0
                # Line charts work well with many data points
                if characteristics.get('row_count', 0) > 20:
                    score += 3.0
                # Good for data with trends
                if characteristics.get('has_numeric', False):
                    score += 2.0
                # Good for multiple series
                if characteristics.get('has_series', False):
                    score += 3.0
            
            # Scoring for SCATTER charts
            elif chart_type == ChartType.SCATTER:
                # Scatter plots need at least two numeric variables
                if characteristics.get('numeric_column_count', 0) >= 2:
                    score += 5.0
                else:
                    score -= 10.0  # Heavily penalize if not enough numeric vars
                # Good for showing relationships
                score += 3.0
                # Better with more data points
                if characteristics.get('row_count', 0) > 20:
                    score += 2.0
            
            # Scoring for PIE charts
            elif chart_type == ChartType.PIE:
                # Pie charts work best with few categories
                if characteristics.get('category_count', 0) <= 7:
                    score += 5.0
                else:
                    score -= 5.0  # Too many categories is bad for pie charts
                # Pie charts are for parts of a whole
                if characteristics.get('is_percentage', False) or characteristics.get('sums_to_100', False):
                    score += 8.0
                else:
                    score -= 5.0  # Not for data that doesn't sum to 100%
                # Must have all positive values
                if not characteristics.get('all_positive', True):
                    score -= 10.0  # Cannot have negative values
            
            # Scoring for DONUT charts (similar to pie)
            elif chart_type == ChartType.DONUT:
                # Same as pie chart, with slight preference
                if characteristics.get('category_count', 0) <= 7:
                    score += 5.0
                else:
                    score -= 5.0
                if characteristics.get('is_percentage', False) or characteristics.get('sums_to_100', False):
                    score += 8.0
                else:
                    score -= 5.0
                if not characteristics.get('all_positive', True):
                    score -= 10.0
                # Slight preference over pie for aesthetic reasons
                score += 0.5
            
            # Scoring for AREA charts
            elif chart_type == ChartType.AREA:
                # Area charts work well for time series
                if characteristics.get('is_time_series', False):
                    score += 8.0
                # Good for showing magnitude over time
                if characteristics.get('has_numeric', False):
                    score += 2.0
                # Good for multiple series that stack
                if characteristics.get('has_series', False) and characteristics.get('all_positive', False):
                    score += 4.0
                # Better with more data points
                if characteristics.get('row_count', 0) > 20:
                    score += 2.0
                # Not good with negative values
                if characteristics.get('has_negative', False):
                    score -= 3.0
            
            # Scoring for HISTOGRAM charts
            elif chart_type == ChartType.HISTOGRAM:
                # Histograms require numeric data
                if characteristics.get('has_numeric', False):
                    score += 5.0
                else:
                    score -= 10.0
                # Best for showing distribution
                score += 3.0
                # Better with more data points
                if characteristics.get('row_count', 0) > 20:
                    score += 2.0
            
            # Scoring for BOX charts
            elif chart_type == ChartType.BOX:
                # Box plots are good for showing distribution with summary statistics
                if characteristics.get('has_numeric', False):
                    score += 5.0
                else:
                    score -= 10.0
                # Good for comparing distributions across categories
                if characteristics.get('has_categorical', False):
                    score += 3.0
                # Better with more data points
                if characteristics.get('row_count', 0) > 20:
                    score += 2.0
            
            # Scoring for VIOLIN charts
            elif chart_type == ChartType.VIOLIN:
                # Similar to box plots but better showing the full distribution
                if characteristics.get('has_numeric', False):
                    score += 5.0
                else:
                    score -= 10.0
                if characteristics.get('has_categorical', False):
                    score += 3.0
                # Better with more data points
                if characteristics.get('row_count', 0) > 50:  # Need more data than box plots
                    score += 3.0
                elif characteristics.get('row_count', 0) <= 20:
                    score -= 3.0  # Not enough data for a meaningful violin plot
            
            # Scoring for HEATMAP charts
            elif chart_type == ChartType.HEATMAP:
                # Heatmaps need at least two categorical or one categorical and one numeric
                if characteristics.get('categorical_column_count', 0) >= 2:
                    score += 5.0
                elif (characteristics.get('categorical_column_count', 0) >= 1 and 
                      characteristics.get('numeric_column_count', 0) >= 1):
                    score += 4.0
                else:
                    score -= 5.0
                # Good for showing patterns in 2D data
                score += 2.0
                # Better with more data points in a grid structure
                if characteristics.get('row_count', 0) > 10:
                    score += 2.0
            
            # Scoring for BUBBLE charts
            elif chart_type == ChartType.BUBBLE:
                # Bubble charts need at least three numeric variables
                if characteristics.get('numeric_column_count', 0) >= 3:
                    score += 8.0
                elif characteristics.get('numeric_column_count', 0) >= 2:
                    # Can work with 2 numeric if we use color for categories
                    score += 3.0
                else:
                    score -= 10.0
                # Better with reasonable number of data points
                if characteristics.get('row_count', 0) > 5 and characteristics.get('row_count', 0) < 100:
                    score += 2.0
            
            # Scoring for RADAR charts
            elif chart_type == ChartType.RADAR:
                # Radar charts work best with multiple dimensions and few categories
                if characteristics.get('numeric_column_count', 0) >= 3:
                    score += 5.0
                else:
                    score -= 3.0
                # Better with fewer data points
                if characteristics.get('row_count', 0) <= 10:
                    score += 3.0
                elif characteristics.get('row_count', 0) > 20:
                    score -= 5.0  # Too many categories is bad for radar
            
            scores[chart_type] = score
        
        return scores
    
    def _generate_recommendations(self, df: pd.DataFrame, chart_type: ChartType, 
                                 characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate chart-specific recommendations based on the data and selected chart type.
        
        Returns a dictionary of recommendation options.
        """
        recommendations = {}
        
        # General recommendations based on the data
        if characteristics.get('row_count', 0) > 1000:
            recommendations['sample'] = True
            recommendations['sample_size'] = min(1000, characteristics.get('row_count', 0))
        
        # Set stacking for bar/area charts if appropriate
        if chart_type in [ChartType.BAR, ChartType.AREA]:
            if characteristics.get('has_series', False) and characteristics.get('all_positive', False):
                recommendations['stacked'] = True
        
        # Set orientation for bar charts
        if chart_type == ChartType.BAR:
            if characteristics.get('many_categories', False):
                recommendations['orientation'] = 'horizontal'  # Better for many categories
            else:
                recommendations['orientation'] = 'vertical'
        
        # Set log scale for data with large range
        if chart_type in [ChartType.LINE, ChartType.SCATTER, ChartType.BAR]:
            if characteristics.get('has_numeric', False):
                num_cols = df.select_dtypes(include=np.number).columns
                main_col = num_cols[0] if len(num_cols) > 0 else None
                if main_col is not None:
                    max_val = df[main_col].max()
                    min_val = df[main_col].min()
                    if min_val > 0 and max_val / min_val > 100:
                        recommendations['y_axis_type'] = 'log'
        
        # Set appropriate theme
        if chart_type in [ChartType.PIE, ChartType.DONUT]:
            recommendations['theme'] = 'light'  # Better for composition charts
        
        # Recommend color palette based on data
        if characteristics.get('has_series', False):
            series_count = characteristics.get('series_count', 0)
            if series_count:
                if series_count <= 10:
                    recommendations['colors'] = None  # Use default color palette
                else:
                    # For many series, recommend categorical color palette
                    recommendations['colors'] = 'category20'  # Will be handled by renderer
        
        # Recommend animation for time series with many points
        if characteristics.get('is_time_series', False) and characteristics.get('row_count', 0) > 50:
            recommendations['animation'] = True
        
        # Interactive charts for complex data
        if ((chart_type in [ChartType.SCATTER, ChartType.BUBBLE, ChartType.HEATMAP]) or
            (characteristics.get('row_count', 0) > 50)):
            recommendations['interactive'] = True
        
        return recommendations 