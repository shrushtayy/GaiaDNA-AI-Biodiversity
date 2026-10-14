"""Biodiversity record analysis and explicitly experimental classification."""
import io
import html
import numpy as np
import pandas as pd
import folium
from folium.plugins import HeatMap
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from analysis_core import analyze

BASE_FEATURES = ['env_temperature', 'env_precipitation', 'env_elevation', 'env_soil_pH', 'env_humidity', 'env_vegetation', 'env_seasonality']

class GaiaDNAPlatform:
    def __init__(self):
        self.df = None
        self.prediction_model = None
        self.model_results = None
        self.training_features = []
        self.synthetic_features = []

    def load_data(self, raw, filename='data.csv'):
        if len(raw) > 20 * 1024 * 1024:
            raise ValueError('Use a file smaller than 20 MB.')
        if filename.lower().endswith('.xlsx'):
            frame = pd.read_excel(io.BytesIO(raw), engine='openpyxl')
            raw = frame.to_csv(index=False).encode()
        self.df = pd.DataFrame(analyze(raw))
        for column in BASE_FEATURES:
            if column in self.df:
                self.df[column] = pd.to_numeric(self.df[column], errors='coerce').replace([np.inf, -np.inf], np.nan)
        self.prediction_model = self.model_results = None
        self.training_features = []
        self.synthetic_features = []
        self.detect_ghost_species()
        return True

    def detect_ghost_species(self):
        self.df['is_ghost'] = self.df.review_status.eq('Needs species identification')
        self.ghost_count = int(self.df.is_ghost.sum())
        self.identified_count = int(self.df.review_status.eq('Species named').sum())
        self.unclassified_count = int(self.df.review_status.eq('Missing genus and species').sum())
        return self.ghost_count, self.identified_count

    def generate_environmental_data(self):
        """Opt-in simulation; never overwrite supplied columns or values."""
        rng = np.random.default_rng(42)
        n = len(self.df)
        defaults = [(15, 3), (800, 150), (350, 100), (6.2, .4), (75, 5), (.7, .1), (2.5, .5)]
        for feature, (mean, spread) in zip(BASE_FEATURES, defaults):
            if feature not in self.df:
                self.df[feature] = rng.normal(mean, spread, n)
                self.synthetic_features.append(feature)
        self.prediction_model = self.model_results = None

    @staticmethod
    def features(frame):
        result = frame.reindex(columns=BASE_FEATURES).apply(pd.to_numeric, errors='coerce').copy()
        result['temp_precip_ratio'] = result.env_temperature / (result.env_precipitation + 1)
        result['climate_diversity_index'] = result.env_temperature * result.env_precipitation / 1000
        return result.replace([np.inf, -np.inf], np.nan)

    def train_prediction_model(self):
        if self.model_results is not None:
            return self.model_results
        eligible = self.df[self.df.review_status.ne('Missing genus and species')]
        y = eligible.is_ghost.astype(int)
        counts = y.value_counts()
        if len(counts) != 2 or counts.min() < 5 or len(y) < 20:
            raise ValueError('Training needs at least 20 eligible records and at least five in each class: species named and needs species identification.')
        X = self.features(eligible)
        features = [c for c in X if X[c].notna().any()]
        if len([c for c in BASE_FEATURES if c in features]) < 3:
            raise ValueError('Provide at least three numeric environmental columns, or enable the clearly labeled simulation in the sidebar.')
        X = X[features]
        train_x, test_x, train_y, test_y = train_test_split(X, y, test_size=.25, random_state=42, stratify=y)
        # Selection and imputation depend only on training data.
        features = [c for c in features if train_x[c].notna().any()]
        train_x, test_x = train_x[features], test_x[features]
        model = make_pipeline(SimpleImputer(strategy='median', keep_empty_features=True), RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced', random_state=42, n_jobs=1))
        folds = min(5, int(train_y.value_counts().min()))
        scores = cross_val_score(model, train_x, train_y, cv=StratifiedKFold(folds, shuffle=True, random_state=42), scoring='balanced_accuracy')
        model.fit(train_x, train_y)
        predicted = model.predict(test_x)
        self.training_features = features
        self.prediction_model = model
        self.feature_importance = pd.DataFrame({'feature': features, 'importance': model[-1].feature_importances_}).sort_values('importance', ascending=False)
        self.model_results = dict(test_accuracy=accuracy_score(test_y, predicted), balanced_accuracy=balanced_accuracy_score(test_y, predicted), cv_mean_accuracy=float(scores.mean()), n_samples=len(y), available_features=features, feature_importance=self.feature_importance)
        return self.model_results

    def predict_discovery_potential(self, environmental_data):
        """Legacy method name; score predicts incomplete identification, not discovery."""
        if self.prediction_model is None:
            return None
        if len(environmental_data) != len(BASE_FEATURES):
            raise ValueError('Supply exactly seven base environmental values.')
        frame = pd.DataFrame([environmental_data], columns=BASE_FEATURES)
        X = self.features(frame).reindex(columns=self.training_features)
        probabilities = dict(zip(self.prediction_model.classes_, self.prediction_model.predict_proba(X)[0]))
        return {'low_potential': float(probabilities.get(0, 0)), 'high_potential': float(probabilities.get(1, 0)), 'prediction': int(self.prediction_model.predict(X)[0])}

    def create_conservation_map(self, heatmap=False):
        data = self.df[self.df.valid_coordinates].copy()
        if data.empty:
            return None
        m = folium.Map(location=[data.latitude.mean(), data.longitude.mean()], zoom_start=4, tiles='OpenStreetMap')
        sample = data.sample(min(1000, len(data)), random_state=42)
        for _, row in sample.iterrows():
            color = 'red' if row.is_ghost else 'blue' if row.review_status == 'Species named' else 'gray'
            label = html.escape(f'{row.genus or "Unknown genus"}: {row.review_status}')
            folium.CircleMarker([row.latitude, row.longitude], radius=4, color=color, fill=True, popup=label).add_to(m)
        if heatmap:
            unresolved = data[data.is_ghost]
            if not unresolved.empty:
                HeatMap(unresolved[['latitude', 'longitude']].values.tolist()).add_to(m)
        return m
