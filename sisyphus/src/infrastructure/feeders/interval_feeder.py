import time
from typing import Callable, Any
from domain.events.market import PriceUpdate

class IntervalFeeder:
    """
    RACIONADOR DE TIEMPO Y PARSER DE DATOS (FEEDER)

    ¿QUÉ ES UN RACIONADOR?
    En un entorno de trading basado en eventos reales (ticks de mercado), los precios fluctúan
    de manera asíncrona y con intervalos aleatorios. Calcular medias móviles o indicadores
    estadísticos directamente sobre ticks destruye la integridad matemática del análisis
    (ej. un SMA de 20 ticks podría representar 3 segundos de mercado en un momento volatil,
    y 1 hora en un mercado sin volumen).
    El racionador acumula estos ticks y emite un evento consolidado ÚNICAMENTE cuando se
    cumple una ventana de tiempo estricta (ej. cada 60 segundos).

    ¿QUÉ ES UN PARSER?
    Las estrategias a menudo no operan directamente con el Precio del activo, sino con 
    sus derivadas (Retornos absolutos, Log-Retornos, Volatilidad). 
    Este Feeder actúa como Parser aplicando funciones de transformación (inyectadas) 
    sobre los datos racionados, emitiendo a la estrategia la métrica final lista para consumir.
    """

    def __init__(self, symbol: str, interval_seconds: int, strategy_callback: Callable[[Any], None], parser_func: Callable[[float, float], float] = None):
        """
        :param interval_seconds: Ventana de tiempo estricta para racionar (ej. 60 para 1 min).
        :param strategy_callback: La función de la estrategia (ej. strategy.update) que recibirá el evento.
        :param parser_func: Función opcional para parsear los datos (ej. log_return(current, previous)).
                            Si es None, se pasará el precio crudo directamente.
        """
        self.symbol = symbol
        self.interval_seconds = interval_seconds
        self.strategy_callback = strategy_callback
        self.parser_func = parser_func
        
        self.last_emit_time = time.time()
        
        # Estado acumulado
        self.last_price = None
        self.previous_close = None


    def update(self, event: PriceUpdate):
        self.on_price_update(event)

    def on_price_update(self, event: PriceUpdate):
        """
        Método que recibe los ticks sueltos de mercado.
        Agrupa y evalúa si se ha cumplido el intervalo de tiempo estricto.
        """
        self.last_price = float(event.price)
        current_time = time.time()

        # Si superamos la ventana estricta de tiempo (ej. 1 minuto exacto)
        if (current_time - self.last_emit_time) >= self.interval_seconds:
            self._emit()
            self.last_emit_time = current_time

    def _emit(self):
        """
        Ejecuta el parsing de los datos y empuja el insumo a la estrategia.
        """
        if self.last_price is None:
            return

        if self.parser_func and self.previous_close is not None:
            # Ejemplo: parser_func = log_return(final_value, initial_value)
            parsed_value = self.parser_func(self.last_price, self.previous_close)
        else:
            # Pasa el precio crudo si no hay parser, o si es la primera iteración
            parsed_value = self.last_price

        # Actualiza la memoria para el próximo intervalo
        self.previous_close = self.last_price

        # Inyecta a la estrategia el valor purificado y espaciado temporalmente
        self.strategy_callback(parsed_value)
