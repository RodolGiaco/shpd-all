from collections import deque
from collections import Counter
from collections import deque, Counter

from collections import deque, Counter

class GestureBuffer:
    def __init__(self, buffer_len=2, min_consistency=0.2):
        self.buffer_len = buffer_len
        self.min_consistency = min_consistency
        self._buffer = deque(maxlen=buffer_len)
        self.last_valid_gesture = None  # Almacenar como None, no como 'No gesture'

    def add_gesture(self, gesture_id):
        """Agregar un gesto al buffer."""
        self._buffer.append(gesture_id)

    def get_gesture(self):
        """Devolver el gesto consistente si cumple con el umbral."""
        if len(self._buffer) < self.buffer_len:
            return self.last_valid_gesture  # Devolver None si aún no hay datos suficientes

        # Contar los gestos más comunes
        counter = Counter(self._buffer).most_common(1)[0]
        gesture_id, count = counter

        # Verificar si cumple el umbral de consistencia
        if count >= self.min_consistency * self.buffer_len:
            self.last_valid_gesture = gesture_id  # Actualizar el último gesto válido
            self._buffer.clear()  # Limpiar buffer después de confirmar la pose
            return gesture_id
        else:
            return self.last_valid_gesture  # Mantener el último gesto válido
