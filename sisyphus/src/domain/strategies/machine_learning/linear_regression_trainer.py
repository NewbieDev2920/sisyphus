from domain.strategies.base import Base
from domain.events.event import Event
from domain.events.market import PriceUpdate
from domain.events.model import TrainingUpdate
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error
from datetime import datetime, timedelta
from domain.events.discord_notification import DiscordNotification

class LinearRegressionTrainer(Base):
    """
    Entrenador síncrono para el modelo de Regresión Lineal.
    Acumula datos internamente y ejecuta el entrenamiento del modelo en intervalos
    o a horas específicas del día, emitiendo un TrainingUpdate cuando finaliza.

    WARNING: ACTUALMENTE EL ENTRENAMIENTO ES SÍNCRONO. 
    ESTO SIGNIFICA QUE DURANTE LA FUNCIÓN `fit()`, EL HILO PRINCIPAL DEL BOT 
    QUEDARÁ BLOQUEADO. SE RECOMIENDA CONFIGURAR EL ENTRENAMIENTO EXCLUSIVAMENTE 
    PARA HORAS DE MERCADO CERRADO PARA EVITAR LATENCIA EN LA EJECUCIÓN DE ÓRDENES.

    Transformaciones Personalizadas Soportadas en `regressors`:
    Para definir los factores, debes inyectar tuplas que contengan una función de transformación.
    Ejemplos de funciones trascendentales usando `np` o `lambda`:
      - Polinomios (Potencia): `lambda x: x ** 2` o `lambda x: x ** 3`
      - Exponencial: `np.exp`
      - Logaritmos: `np.log` (Nota: asegurar valores > 0)
      - Trigonométricas: `np.sin`, `np.cos`, `np.tan`
      - Lineal (Sin transformación): `lambda x: x`

    Ejemplo de `regressors`:
    [
        ('potencia_2', FunctionTransformer(lambda x: x ** 2), ['precio']),
        ('logaritmo', FunctionTransformer(np.log), ['volumen']),
        ('seno', FunctionTransformer(np.sin), ['hora_dia'])
    ]
    """

    def __init__(self, symbol: str, fsm, predictor_target: str, regressors: list, 
                 target_meaning: str, regressors_meaning: dict,
                 train_interval_minutes: int = None, train_time_of_day: str = None,
                 min_r2_threshold: float = 0.3):
        """
        :param min_r2_threshold: Límite inferior de R^2 en el conjunto de validación. 
                                 Si el rendimiento cae por debajo, se alerta vía Discord.
        :param target_meaning: Significado semántico del target (ej. "Retorno porcentual a 5 periodos").
        :param regressors_meaning: Diccionario con el significado de cada feature (ej. {'x1': 'Volumen', 'x2': 'SMA 20'}).
        :param train_interval_minutes: Entrena cada X minutos (ej. 60). Ignorado si train_time_of_day está presente.
        :param train_time_of_day: Hora exacta en formato "HH:MM" (ej. "16:30" para cierre de mercado).
        """
        self.symbol = symbol
        self.fsm = fsm
        self.name = self.__class__.__name__
        self.predictor_target = predictor_target
        self.target_meaning = target_meaning
        self.regressors = regressors
        self.regressors_meaning = regressors_meaning
        
        # Mapeo de transformaciones matemáticas
        self.regressors_transformations = {
            col: t_name
            for t_name, transformer, cols in self.regressors
            for col in cols
        }
        
        # Configuración de triggers de entrenamiento
        self.train_interval_minutes = train_interval_minutes
        self.train_time_of_day = train_time_of_day
        
        self.last_train_time = datetime.now()
        self.has_trained_today = False
        
        # Monitoreo de Rendimiento
        self.min_r2_threshold = min_r2_threshold
        self.last_metrics = {
            'train_r2': None, 'train_mse': None,
            'val_r2': None, 'val_mse': None
        }
        
        # DataFrame interno para cumplir SRP
        self.historical_data = pd.DataFrame()
        self.max_memory_rows = 10000  # Evitar desbordamiento de memoria RAM
        
    def update(self, event: Event):
        # 1. Alimentar la memoria interna con nuevos datos (ej. un Candle o PriceUpdate)
        # Aquí asumimos que recibes un evento enriquecido o vas guardando precios.
        # Para el propósito de ML, necesitas acumular el 'y' y las 'X'.
        if isinstance(event, PriceUpdate):
            # Ejemplo simplificado: acumulamos el precio y alguna métrica.
            # En producción, este evento debería traer los factores pre-calculados o se calculan aquí.
            new_row = {
                'timestamp': datetime.now(),
                self.predictor_target: float(event.price), # Simulación: y es el precio
                # Aquí irían las variables X1, X2, etc. (En la vida real vendrían del FSM o Feeders)
                'x1': float(event.price) * 0.9,
                'x2': float(event.price) * 1.1
            }
            new_df = pd.DataFrame([new_row])
            if self.historical_data.empty:
                self.historical_data = new_df
            else:
                self.historical_data = pd.concat([self.historical_data, new_df], ignore_index=True)
            
            # Recortar memoria
            if len(self.historical_data) > self.max_memory_rows:
                self.historical_data = self.historical_data.iloc[-self.max_memory_rows:]

        # 2. Verificar si es momento de entrenar
        self._check_training_trigger()

    def _check_training_trigger(self):
        now = datetime.now()
        should_train = False

        if self.train_time_of_day:
            # Entrenamiento a hora específica (ej. "16:30")
            target_time = datetime.strptime(self.train_time_of_day, "%H:%M").time()
            if now.time() >= target_time and not self.has_trained_today:
                should_train = True
                self.has_trained_today = True
            
            # Reset al cambiar de día
            if now.time() < target_time:
                self.has_trained_today = False

        elif self.train_interval_minutes:
            # Entrenamiento por intervalo
            if (now - self.last_train_time) >= timedelta(minutes=self.train_interval_minutes):
                should_train = True
                self.last_train_time = now

        if should_train and not self.historical_data.empty:
            self.train_model()

    def train_model(self):
        """
        Ejecuta el entrenamiento del pipeline de Sklearn. Bloqueante.
        """
        print(f"[{datetime.now()}] Iniciando entrenamiento SÍNCRONO de LinearRegression...")
        
        # Nombres de las columnas que forman X
        feature_columns = []
        for regressor in self.regressors:
            # regressor = ('nombre', transformador, ['columna1', 'columna2'])
            feature_columns.extend(regressor[2])
            
        feature_columns = list(set(feature_columns)) # Unicos
        
        # Validar que tenemos los datos necesarios
        missing_cols = [c for c in feature_columns + [self.predictor_target] if c not in self.historical_data.columns]
        if missing_cols:
            print(f"Faltan columnas en los datos históricos: {missing_cols}")
            return

        X = self.historical_data[feature_columns]
        y = self.historical_data[self.predictor_target]

        # Evitar entrenar con muy pocos datos
        if len(X) < 20:
            print("Datos insuficientes para realizar un split de validación confiable.")
            return

        # Train/Validation Split (80% / 20%) Cronológico
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        try:
            # Ensamblar Pipeline
            transformaciones_personalizadas = ColumnTransformer(
                transformers=self.regressors,
                remainder='drop'
            )
            
            modelo_personalizado = Pipeline(steps=[
                ('ingenieria_caracteristicas', transformaciones_personalizadas),
                ('regresion', LinearRegression())
            ])

            # FIT (Entrenamiento Bloqueante) en Train
            modelo_personalizado.fit(X_train, y_train)

            # --- EVALUACIÓN DE MÉTRICAS ---
            pred_train = modelo_personalizado.predict(X_train)
            pred_val = modelo_personalizado.predict(X_val)
            
            self.last_metrics['train_r2'] = r2_score(y_train, pred_train)
            self.last_metrics['train_mse'] = mean_squared_error(y_train, pred_train)
            self.last_metrics['val_r2'] = r2_score(y_val, pred_val)
            self.last_metrics['val_mse'] = mean_squared_error(y_val, pred_val)

            # Evaluar Rendimiento Deplorable
            if self.last_metrics['val_r2'] < self.min_r2_threshold:
                alert_msg = (f"🚨 ALERTA: Modelo Regresión Lineal ({self.symbol}) colapsado.\n"
                             f"R² en Validación: {self.last_metrics['val_r2']:.4f} "
                             f"(Umbral: {self.min_r2_threshold})\n"
                             f"MSE: {self.last_metrics['val_mse']:.6f}")
                self.fsm.on_event(DiscordNotification(alert_msg))

            # Extraer los pesos del modelo
            lr_model = modelo_personalizado.named_steps['regresion']
            model_weights = dict(zip(feature_columns, lr_model.coef_))
            model_weights['intercept'] = lr_model.intercept_

            # Emitir Evento con el modelo y la metadata semántica
            self.fsm.on_event(TrainingUpdate(
                model_name=self.name,
                fitted_pipeline=modelo_personalizado,
                target=self.predictor_target,
                features=feature_columns,
                target_meaning=self.target_meaning,
                regressors_meaning=self.regressors_meaning,
                regressors_transformations=self.regressors_transformations,
                weights=model_weights
            ))
            
            print(f"[{datetime.now()}] Entrenamiento completado y modelo emitido.")

        except Exception as e:
            print(f"Error durante el entrenamiento: {e}")

    def configuration_map(self) -> str:
        meanings = "\\n        ".join([f"{k}: {v} (Transform: {self.regressors_transformations.get(k, 'Linear')})" for k, v in self.regressors_meaning.items()])
        
        # Formatear métricas si existen
        m = self.last_metrics
        if m['train_r2'] is not None:
            metrics_str = f"TRAIN [R²: {m['train_r2']:.4f} | MSE: {m['train_mse']:.6f}]\n        VAL   [R²: {m['val_r2']:.4f} | MSE: {m['val_mse']:.6f}]"
        else:
            metrics_str = "No entrenado aún."
            
        config = f"""-------
        TRAINER: {self.name}
        -------
        SYMBOL: {self.symbol}
        TRIGGERS: {self.train_time_of_day or str(self.train_interval_minutes) + 'm'}
        PREDICTOR (y^): {self.predictor_target} -> {self.target_meaning}
        REGRESSORS (X): 
        {meanings}
        
        RENDIMIENTO DEL MODELO:
        {metrics_str}
        (Alerta Discord si Val_R² < {self.min_r2_threshold})
        """
        return config
