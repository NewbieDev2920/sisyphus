from domain.strategies.base import Base
from domain.events.event import Event
from domain.events.market import PriceUpdate
from domain.events.model import TrainingUpdate
from domain.events.discord_notification import DiscordNotification
import pandas as pd
import numpy as np
from arch import arch_model
from datetime import datetime, timedelta

class EGARCHTrainer(Base):
    """
    Entrenador síncrono para el modelo de volatilidad EGARCH.
    Utiliza la librería `arch` para modelar varianza asimétrica.
    
    WARNING: EL ENTRENAMIENTO ES SÍNCRONO Y BLOQUEANTE.
    """

    def __init__(self, symbol: str, fsm, predictor_target: str, 
                 p: int = 1, o: int = 1, q: int = 1,
                 train_interval_minutes: int = None, train_time_of_day: str = None,
                 max_mse_threshold: float = 0.001):
        """
        :param p: Lags de la varianza pasada (GARCH).
        :param o: Lags asimétricos (EGARCH leverage effect).
        :param q: Lags de los errores al cuadrado (ARCH).
        :param max_mse_threshold: Umbral máximo permitido para MSE en validación. 
                                  Si se supera, alerta por Discord.
        """
        self.symbol = symbol
        self.fsm = fsm
        self.name = self.__class__.__name__
        self.predictor_target = predictor_target
        
        self.p = p
        self.o = o
        self.q = q
        
        self.train_interval_minutes = train_interval_minutes
        self.train_time_of_day = train_time_of_day
        self.max_mse_threshold = max_mse_threshold
        
        self.last_train_time = datetime.now()
        self.has_trained_today = False
        
        self.historical_data = pd.DataFrame()
        self.max_memory_rows = 10000
        
        self.last_metrics = {
            'aic': None, 'bic': None,
            'train_mse': None, 'val_mse': None, 'val_qlike': None
        }

    def update(self, event: Event):
        if isinstance(event, PriceUpdate):
            # Asumimos que predictor_target es el log_return.
            # En producción, esto se extrae de un Feeder real.
            new_row = {
                'timestamp': datetime.now(),
                self.predictor_target: float(event.price) # Simulación
            }
            new_df = pd.DataFrame([new_row])
            if self.historical_data.empty:
                self.historical_data = new_df
            else:
                self.historical_data = pd.concat([self.historical_data, new_df], ignore_index=True)
            
            if len(self.historical_data) > self.max_memory_rows:
                self.historical_data = self.historical_data.iloc[-self.max_memory_rows:]

        self._check_training_trigger()

    def _check_training_trigger(self):
        now = datetime.now()
        should_train = False

        if self.train_time_of_day:
            target_time = datetime.strptime(self.train_time_of_day, "%H:%M").time()
            if now.time() >= target_time and not self.has_trained_today:
                should_train = True
                self.has_trained_today = True
            
            if now.time() < target_time:
                self.has_trained_today = False
        elif self.train_interval_minutes:
            if (now - self.last_train_time) >= timedelta(minutes=self.train_interval_minutes):
                should_train = True
                self.last_train_time = now

        if should_train and not self.historical_data.empty:
            self.train_model()

    def train_model(self):
        print(f"[{datetime.now()}] Iniciando entrenamiento SÍNCRONO de EGARCH...")
        
        if self.predictor_target not in self.historical_data.columns:
            return
            
        y = self.historical_data[self.predictor_target].dropna()
        
        if len(y) < 50:
            print("Datos insuficientes para EGARCH (Mínimo recomendado 50).")
            return

        split_idx = int(len(y) * 0.8)
        
        try:
            # Entrenamiento en toda la serie, pero usando last_obs para definir out-of-sample
            # La librería arch permite pasar el array entero y decirle hasta dónde ajustar
            am = arch_model(y * 100, vol='EGARCH', p=self.p, o=self.o, q=self.q, dist='Normal')
            
            # El fit escala los datos a veces (por eso * 100), pero mantendremos la métrica internamente
            res = am.fit(last_obs=split_idx, disp="off")
            
            # Métricas In-Sample
            self.last_metrics['aic'] = res.aic
            self.last_metrics['bic'] = res.bic
            
            # Varianza In-Sample
            train_var = res.conditional_volatility[:split_idx]**2
            train_proxy = (y.iloc[:split_idx] * 100)**2
            self.last_metrics['train_mse'] = np.mean((train_proxy - train_var)**2)
            
            # Forecast Out-of-Sample (Validación)
            # Calculamos varianzas t+1 para el set de validación
            forecasts = res.forecast(start=split_idx, align='target')
            val_var = forecasts.variance[split_idx:].iloc[:, 0] # 1-step ahead
            val_proxy = (y.iloc[split_idx:] * 100)**2
            
            # Filtrar nans
            valid_idx = ~val_var.isna() & ~val_proxy.isna()
            val_var_clean = val_var[valid_idx]
            val_proxy_clean = val_proxy[valid_idx]
            
            if len(val_var_clean) > 0:
                self.last_metrics['val_mse'] = np.mean((val_proxy_clean - val_var_clean)**2)
                # QLIKE = proxy/var - log(proxy/var) - 1
                ratio = val_proxy_clean / val_var_clean
                self.last_metrics['val_qlike'] = np.mean(ratio - np.log(ratio) - 1)
            
            # Alerta Discord si MSE es desastroso
            if self.last_metrics['val_mse'] and self.last_metrics['val_mse'] > self.max_mse_threshold:
                alert_msg = (f"🚨 ALERTA: Modelo EGARCH ({self.symbol}) con alto error.\n"
                             f"MSE Validación: {self.last_metrics['val_mse']:.6f} "
                             f"(Umbral máx: {self.max_mse_threshold})\n"
                             f"AIC: {res.aic:.2f} | BIC: {res.bic:.2f}")
                self.fsm.on_event(DiscordNotification(alert_msg))

            # Extraer pesos/parámetros
            model_weights = res.params.to_dict()

            # Emitir Modelo a Predictors
            self.fsm.on_event(TrainingUpdate(
                model_name=self.name,
                fitted_pipeline=res,
                target=self.predictor_target,
                features=[], # EGARCH es univariado
                target_meaning="Varianza Condicional EGARCH",
                regressors_meaning={},
                regressors_transformations={},
                weights=model_weights
            ))
            
            print(f"[{datetime.now()}] EGARCH entrenado y modelo emitido.")

        except Exception as e:
            print(f"Error durante entrenamiento EGARCH: {e}")

    def configuration_map(self) -> str:
        m = self.last_metrics
        if m['train_mse'] is not None:
            metrics_str = (f"TRAIN [MSE: {m['train_mse']:.4f} | AIC: {m['aic']:.2f} | BIC: {m['bic']:.2f}]\n"
                           f"        VAL   [MSE: {m['val_mse']:.4f} | QLIKE: {m['val_qlike']:.4f}]")
        else:
            metrics_str = "No entrenado aún."
            
        config = f"""-------
        TRAINER: {self.name}
        -------
        SYMBOL: {self.symbol}
        TARGET: {self.predictor_target}
        Lags: p={self.p}, o={self.o}, q={self.q}
        
        RENDIMIENTO DEL MODELO:
        {metrics_str}
        (Alerta Discord si Val_MSE > {self.max_mse_threshold})
        """
        return config
