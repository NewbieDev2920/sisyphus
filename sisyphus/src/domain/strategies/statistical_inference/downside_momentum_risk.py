from domain.strategies.base import Base
from computations.ewma import next_ewma_point_alpha
from computations.rolling_std import rolling_std_point
from domain.events.discord_notification import DiscordNotification
from domain.events.strategy import SignalEvent
from domain.events.market import PriceUpdate
from domain.signals import Signal
from datetime import datetime
from domain.events.event import Event
import math

class DownsideMomentumRisk(Base):

    """
    This is a crossover strategy. It takes two mobile ewmas with different time windows.
    The ewmas depend on downside standard deviation.

    ewma_l(downside_std)
    ewma_s(downside_std)

    Then we check the following.

    ewma_s - ewma_l > 0 (This means downside volatility is getting dangerous)

    Although, to differ from noise, we check if this comparison is statistically significant:

    (ewma_s - ewma_l) / std(ewma_l) > threshold

    We assume Z-score, not because it follows the gaussian distribution, but because 
    it is a distribution that reacts rapidly to unusual values. In this case, severely negative values.

    --- IMPLEMENTATION DETAILS ---
    
    Reducing computational complexity.

    To compute the Downside Standard Deviation (Semi-deviation) online (without storing historical arrays), 
    we track the Expected Value of the squared downside returns: E[min(0, log_return)^2].
    Since we are using Exponential Weighted Moving Averages (EWMA), we track these Expected Values 
    for the squared downside returns.

    Variables explained:
    - E2_s: Expected squared value (E[X^2]) of the downside return 
            using the short-term alpha (alpha_s). Used to compute `ewma_s` = sqrt(E2_s).
    - E2_l: Expected squared value (E[X^2]) of the downside return 
            using the long-term alpha (alpha_l). Used to compute `ewma_l` = sqrt(E2_l).
    - E_ewma_l, E2_ewma_l: Expected value and Expected squared value of `ewma_l` itself. 
                           Used to compute `std_ewma_l` (the standard deviation of the long-term downside std),
                           which is the denominator for our Z-score calculation.
    """


    def __init__(self, symbol: str, fsm, short_alpha: float, long_alpha: float, threshold: float, data_type: str = "Raw Prices", interval: str = "1m"):
        # Se inicializan las variables base de la estrategia, como el símbolo, máquina de estados (FSM) y periodicidad
        self.symbol = symbol
        self.fsm = fsm
        self.data_type = data_type
        self.interval = interval
        self.name = self.__class__.__name__
        self.qty = 0
        
        # Parámetros alfa para corto y largo plazo (rango de 0 a 1) para el decaimiento exponencial
        self.alpha_s = short_alpha
        self.alpha_l = long_alpha
        
        # Umbral Z-Score para decidir el punto de crossover
        self.threshold = threshold
        
        # Bandera y estado de la tendencia del activo (None al inicio, luego True=Bull o False=Bear)
        self.trend = None
        
        # Bandera para rastrear si ya emitimos la advertencia de peligro (crossover simple)
        self.is_warning = False
        
        # Precio actual y bandera de inicialización para tener un precio previo en la primera iteración
        self.asset_price: float = 0.0
        self.is_initialized = False
        self.prev_price = 0.0

        # EWMA variables for downside variance (short)
        # E2_s rastrea la media móvil exponencial de los retornos negativos al cuadrado (corto plazo)
        self.E2_s = 0.0

        # EWMA variables for downside variance (long)
        # E2_l rastrea la media móvil exponencial de los retornos negativos al cuadrado (largo plazo)
        self.E2_l = 0.0

        # EWMA variables for standard deviation of ewma_l
        # E_ewma_l y E2_ewma_l rastrean la media y la varianza de la ewma_l para sacar la desviación estándar (std)
        self.E_ewma_l = 0.0
        self.E2_ewma_l = 0.0

        # Resultados finales: volatilidad a corto (ewma_s), a largo (ewma_l) y la std a largo (std_ewma_l)
        self.ewma_s = 0.0
        self.ewma_l = 0.0
        self.std_ewma_l = 0.0

    def update(self, event: Event):
        # Punto de entrada de la estrategia cuando llega un evento. Verificamos si es una actualización de precio.
        if isinstance(event, PriceUpdate):
            # Guardamos el nuevo precio recibido
            self.asset_price = float(event.price)
            # Consultamos y actualizamos la cantidad actual de activos mediante la máquina de estados
            self.qty = self.fsm.asset_qty()
            # Delegamos el cálculo y la lógica central del crossover a nuestra función funcional
            self.ewma_crossover(self.asset_price)

    def compute_signal(self, signal: Signal, numeric_value):
        # Transmite una señal (ej. Signal.SELL) y la cantidad a la máquina de estados
        self.fsm.on_event(SignalEvent(signal, numeric_value))
        
    def notify(self, message:str):
        # Transmite una notificación a Discord mediante la máquina de estados
        self.fsm.on_event(DiscordNotification(message))

    def configuration_map(self) -> str:
        # Devuelve una representación en texto (string) del estado actual y parámetros de la estrategia para logging o debugging
        config = f"""-------
        STRATEGY: {self.name} \U0001fa84
        -------
        SYMBOL: {self.symbol}
        DATA TYPE: {self.data_type}
        TIME INTERVAL: {self.interval}
        QTY: {self.qty}
        ASSET PRICE : {self.asset_price}
        SHORT ALPHA : {self.alpha_s}
        LONG ALPHA : {self.alpha_l}
        THRESHOLD : {self.threshold}
        LONG EWMA: {self.ewma_l}
        SHORT EWMA: {self.ewma_s}
        STD LONG EWMA: {self.std_ewma_l}
        TREND {"BULL" if self.trend else "BEAR"}
        """
        return config

    def ewma_crossover(self, value: float):
        # O(1) Inicialización: si es el primer precio recibido, lo guardamos y salimos porque no podemos calcular retornos
        if not self.is_initialized:
            self.prev_price = value
            self.is_initialized = True
            return

        # Computations
        # Fórmula Log-Retorno: r_t = ln(P_t / P_{t-1})
        if self.prev_price > 0:
            ret = math.log(value / self.prev_price)
        else:
            ret = 0.0
        
        # Filtramos solo los retornos negativos (downside). Si es positivo, será 0.0.
        # Fórmula: downside_ret_t = min(0, r_t)
        downside_ret = min(0.0, ret)
        
        # Guardamos el precio actual como precio previo para la próxima iteración
        self.prev_price = value

        # Update short downside EWMA
        # 1. Calculamos la nueva media móvil exponencial para los retornos negativos al cuadrado (corto plazo)
        # Fórmula EWMA: E2_s_{t} = alpha_s * (downside_ret_t)^2 + (1 - alpha_s) * E2_s_{t-1}
        self.E2_s = next_ewma_point_alpha(self.E2_s, downside_ret**2, self.alpha_s)
        # 2. La volatilidad negativa (semi-desviación) a corto plazo es la raíz cuadrada del valor esperado
        # Fórmula: ewma_s_t = sqrt(E2_s_t)
        self.ewma_s = math.sqrt(self.E2_s)

        # Update long downside EWMA
        # 1. Calculamos la nueva media móvil exponencial para los retornos negativos al cuadrado (largo plazo)
        # Fórmula EWMA: E2_l_{t} = alpha_l * (downside_ret_t)^2 + (1 - alpha_l) * E2_l_{t-1}
        self.E2_l = next_ewma_point_alpha(self.E2_l, downside_ret**2, self.alpha_l)
        # 2. La volatilidad negativa a largo plazo es la raíz cuadrada del valor esperado
        # Fórmula: ewma_l_t = sqrt(E2_l_t)
        self.ewma_l = math.sqrt(self.E2_l)

        # Update std of ewma_l
        # Para el Z-score, necesitamos la desviación estándar de la volatilidad a largo plazo (ewma_l) a lo largo del tiempo.
        # 1. Actualizamos la media móvil de ewma_l
        # Fórmula: E_ewma_l_{t} = alpha_l * ewma_l_t + (1 - alpha_l) * E_ewma_l_{t-1}
        self.E_ewma_l = next_ewma_point_alpha(self.E_ewma_l, self.ewma_l, self.alpha_l)
        
        # 2. Actualizamos la media móvil de ewma_l al cuadrado
        # Fórmula: E2_ewma_l_{t} = alpha_l * (ewma_l_t)^2 + (1 - alpha_l) * E2_ewma_l_{t-1}
        self.E2_ewma_l = next_ewma_point_alpha(self.E2_ewma_l, self.ewma_l**2, self.alpha_l)
        
        # 3. Calculamos la desviación estándar mediante Var(X) = E[X^2] - (E[X])^2
        # Nos aseguramos de que el término dentro de la raíz cuadrada no sea negativo (problemas de flotantes)
        # Fórmula: std_ewma_l_t = sqrt( E2_ewma_l_t - (E_ewma_l_t)^2 )
        self.std_ewma_l = rolling_std_point(self.E2_ewma_l, self.E_ewma_l**2) if self.E2_ewma_l > self.E_ewma_l**2 else 0.0

        # Prevención de división por cero en el inicio, cuando aún no hay varianza en la ewma_l
        if self.std_ewma_l == 0:
            return

        # Calculamos el Z-score para ver si la diferencia entre la volatilidad a corto y largo plazo es estadísticamente significativa
        # Fórmula: z_score_t = (ewma_s_t - ewma_l_t) / std_ewma_l_t
        z_score = (self.ewma_s - self.ewma_l) / self.std_ewma_l

        # Lógica de Trading (Decisión de tendencia y Notificaciones)
        
        # CASO 2: Crossover simple de riesgo (Advertencia)
        # Cuando ewma_s > ewma_l, significa que el riesgo a la baja a corto plazo superó al largo plazo.
        if self.ewma_s > self.ewma_l and not self.is_warning:
            self.is_warning = True
            self.notify(f" \u26A0\uFE0F {self.symbol} WARNING: Short-term downside risk crossed long-term (ewma_s > ewma_l). Potential danger ahead! {str(datetime.now())}")
        elif self.ewma_s <= self.ewma_l and self.is_warning:
            self.is_warning = False # Restablecemos si el peligro disminuye

        # CASO 1: Crossover estadísticamente significativo (Cambio de tendencia y Venta)
        # Un z_score altamente positivo indica una tendencia "Bear" (bajista). Vendemos todo.
        # Un z_score altamente negativo indica una tendencia "Bull" (alcista).

        # Si aún no hemos definido ninguna tendencia, esperamos a que el z-score supere el umbral
        if self.trend is None:
            if z_score > self.threshold:
                self.trend = False
                self.notify(f"\U0001F6A8 {self.symbol} BEAR TREND CONFIRMED: Z-score {z_score:.2f} > {self.threshold}. Selling all positions! {str(datetime.now())}")
                if self.qty > 0:
                    self.compute_signal(Signal.SELL, self.qty)
            elif z_score < -self.threshold:
                self.trend = True
                self.notify(f"\U0001F7E2 {self.symbol} BULL TREND CONFIRMED: Z-score {z_score:.2f} < -{self.threshold}. {str(datetime.now())}")
        else:
            # Cambio a Bull Trend
            if z_score < -self.threshold and not self.trend:
                self.trend = True
                self.notify(f"\U0001F7E2 {self.symbol} CHANGED TO BULL TREND: Z-score {z_score:.2f} < -{self.threshold}. {str(datetime.now())}")
                
            # Cambio a Bear Trend (Significativo)
            if z_score > self.threshold and self.trend:
                self.trend = False
                self.notify(f"\U0001F6A8 {self.symbol} CHANGED TO BEAR TREND: Z-score {z_score:.2f} > {self.threshold}. Selling all positions! {str(datetime.now())}")
                if self.qty > 0:
                    self.compute_signal(Signal.SELL, self.qty)
