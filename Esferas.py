import numpy as np
from Rampas import line_curve_3d, parabolic_curve_3d, cycloid_curve_3d, RAMP_SEPARATION, A_METERS

# Constantes físicas
g = 9.8  # Gravedad en m/s²
MU_BASE = 0.008  # Coeficiente de fricción base
MU_RAMP_BASE = 0.016  # Coeficiente de fricción en rampa

class Esfera:
    def __init__(self, curve_func, color, name, z_offset=0.0, radius=0.15, masa=1.0, rozamiento_base=None):
        # Propiedades de la curva y apariencia
        self.curve_func = curve_func  # Función que define la curva de la rampa
        self.color = color  # Color RGB de la bola
        self.name = name  # Nombre identificador
        self.z_offset = z_offset  # Desplazamiento en Z para separar rampas
        
        # Atributos modificables
        self.radius = radius  # Radio de la bola
        self.masa = masa  # Masa de la bola
        
        # Parámetros de física y estado
        self.t = 0.0  # Parámetro de posición en la curva (0-1)
        self.finished = False  # Si la bola terminó su recorrido
        self.v = 0.0  # Velocidad actual
        self.direction = 1  # Dirección del movimiento (1 adelante, -1 atrás)
        self.first_impact_time = None  # Tiempo del primer impacto con el muro
        self.final_stop_time = None  # Tiempo cuando se detuvo completamente
        
        # Listas para precomputar geometría de la curva
        self.points_left = []  # Puntos del rail izquierdo
        self.points_right = []  # Puntos del rail derecho
        self.points_center = []  # Puntos del centro (para física)
        self.lengths = []  # Longitudes acumuladas
        self.length_meters = 0  # Longitud total de la curva
        self.slopes = []  # Pendientes en cada punto
        
        # FORZAR POSICIÓN INICIAL INMEDIATAMENTE
        self.base_pos = np.array([0, 0, 0])  # Posición temporal
        self._forzar_posicion_inicial()  # Posicionar en plataforma
        
        # Estado de la plataforma
        self.on_platform = True  # Si está en la plataforma inicial
        self.platform_released = False  # Si fue liberada de la plataforma
        
        # PARÁMETROS ESPECÍFICOS POR TIPO DE CURVA
        if rozamiento_base is not None:
            # Usar rozamiento personalizado si se especifica
            self.mu = rozamiento_base
            self.mu_ramp = rozamiento_base * 2.0
        elif name == "Línea Recta":
            self.mu = MU_BASE * 1.1  # Mayor fricción para línea recta
            self.mu_ramp = MU_RAMP_BASE * 1.1
        elif name == "Parábola":
            self.mu = MU_BASE  # Fricción media para parábola
            self.mu_ramp = MU_RAMP_BASE
        else:  # Cicloide
            self.mu = MU_BASE * 0.9  # Menor fricción para cicloide
            self.mu_ramp = MU_RAMP_BASE * 0.9
        
        # Parámetros de rebote
        self.restitution = 0.75  # Coeficiente de restitución (rebote)
        self.max_rebounds = 4  # Máximo número de rebotes
        self.rebounded = False  # Si ya rebotó al menos una vez
        self.rebound_count = 0  # Contador de rebotes
        self.min_velocity = 0.05  # Velocidad mínima para seguir rebotando
        self.wall_stopped = False  # Si se detuvo por el muro

    def _forzar_posicion_inicial(self):
        """FORZAR posición inicial en la plataforma usando la altura ACTUAL de A_METERS"""
        from Rampas import A_METERS
        
        # Calcular altura de plataforma (0.3m sobre punto A)
        platform_height = A_METERS[1] + 0.3
        # Posicionar en el inicio de la curva con radio incluido
        self.base_pos = np.array([A_METERS[0], platform_height + self.radius, self.z_offset])
        
        # Debug información
        print(f"{self.name} forzada a posición:")
        print(f"   - X: {self.base_pos[0]:.2f} (A_METERS[0])")
        print(f"   - Y: {self.base_pos[1]:.2f} (A_METERS[1] + 0.3 + radius)")
        print(f"   - Z: {self.base_pos[2]:.2f}")
        print(f"   - Altura A_METERS: {A_METERS[1]:.2f}")
        print(f"   - Radio bola: {self.radius:.2f}")

    def initialize_position(self):
        """Inicializar posición completa - SOLUCIÓN DEFINITIVA"""
        # Precomputar puntos con la altura actual
        self.points_left = []
        self.points_right = []
        self.points_center = []
        # Generar 1001 puntos a lo largo de la curva
        for i in range(1001):
            left, right = self.curve_func(i/1000.0, z_offset=self.z_offset)
            self.points_left.append(left)
            self.points_right.append(right)
            center = (left + right) / 2.0  # Punto central para física
            self.points_center.append(center)
            
        # Precomputar longitudes y pendientes
        self.lengths = self.precompute_lengths()
        self.length_meters = self.lengths[-1] if self.lengths else 0  # Longitud total
        self.slopes = self.precompute_slopes()
        
        # FORZAR POSICIÓN CORRECTA
        self._forzar_posicion_inicial()

    def get_initial_position(self):
        """Posición inicial en la plataforma"""
        platform_height = A_METERS[1] + 0.3
        return np.array([A_METERS[0], platform_height + self.radius, self.z_offset])

    def precompute_lengths(self):
        """Precalcular longitudes acumuladas a lo largo de la curva"""
        lengths = [0]  # Empezar en longitud 0
        if not self.points_center:
            return lengths
            
        prev = self.points_center[0]
        # Calcular longitud entre puntos consecutivos
        for i in range(1, len(self.points_center)):
            curr = self.points_center[i]
            segment_length = np.linalg.norm(curr - prev)  # Distancia euclidiana
            lengths.append(lengths[-1] + segment_length)  # Acumular
            prev = curr
        return lengths

    def precompute_slopes(self):
        """Precalcular pendientes en cada punto de la curva"""
        slopes = []
        if not self.points_center:
            return slopes
            
        for i in range(len(self.points_center)):
            # Calcular derivada (pendiente) usando diferencias finitas
            if i < len(self.points_center) - 1:
                dx = self.points_center[i+1][0] - self.points_center[i][0]
                dy = self.points_center[i+1][1] - self.points_center[i][1]
            else:
                # Para el último punto, usar diferencia hacia atrás
                dx = self.points_center[i][0] - self.points_center[i-1][0]
                dy = self.points_center[i][1] - self.points_center[i-1][1]
            
            # Evitar división por cero
            if abs(dx) > 1e-6:
                slope = dy / dx  # Pendiente = Δy/Δx
            else:
                slope = 1e6 if dy > 0 else -1e6  # Pendiente vertical
            slopes.append(slope)
        return slopes

    def get_center_position_at_t(self, t):
        """Obtener posición en el centro de la curva para parámetro t (0-1)"""
        if not self.points_center:
            return np.array([0, 0, 0])
            
        # Convertir parámetro continuo a índice discreto
        idx = int(t * (len(self.points_center) - 1))
        idx = min(idx, len(self.points_center) - 2)  # Evitar desborde
        
        # Interpolar entre puntos
        t_segment = t * (len(self.points_center) - 1) - idx
        pos_center_prev = self.points_center[idx]
        pos_center_next = self.points_center[idx + 1]
        
        # Interpolación lineal
        pos_center = pos_center_prev + t_segment * (pos_center_next - pos_center_prev)
        return pos_center

    def release_from_platform(self):
        """Liberar la bola de la plataforma"""
        self.on_platform = False
        self.platform_released = True
        self.t = 0.0  # Empezar desde el inicio
        self.base_pos = self.get_center_position_at_t(0.0)  # Posición en curva
        self.base_pos[1] += self.radius  # Ajustar por radio

    def update(self, dt, current_time):
        """Actualizar física de la bola - FÍSICA NORMAL PARA TODAS"""
        # No actualizar si terminó, está en plataforma o detenida
        if self.finished or self.on_platform or self.wall_stopped:
            return

        # Obtener posición y pendiente actual
        current_pos, current_slope = self.get_position_and_slope(self.t)
        
        # Calcular ángulo de la pendiente (siempre usar valor absoluto para gravedad)
        angle = np.arctan(abs(current_slope))
        
        # Aceleración debido a la gravedad (siempre positiva)
        acceleration = g * np.sin(angle)
        
        # Fricción (afectada por la masa)
        current_friction = (self.mu_ramp if self.rebounded else self.mu) * g * np.cos(angle)
        
        # Aplicar fricción en dirección opuesta al movimiento
        if abs(self.v) > 0:
            if self.v > 0:
                acceleration -= current_friction  # Frenar si va adelante
            else:
                acceleration += current_friction  # Frenar si va atrás
        
        # Actualizar velocidad (afectada por la masa)
        self.v += acceleration * dt * (1.0 / self.masa)
        
        # MOVIMIENTO A LO LARGO DE LA CURVA
        current_distance = self.t * self.length_meters  # Distancia recorrida
        new_distance = current_distance + self.v * dt  # Nueva distancia
        new_t = new_distance / self.length_meters  # Nuevo parámetro t
        
        # DETECCIÓN DE COLISIONES
        if new_t >= 1.0:  # Golpea el muro final
            if not self.rebounded:
                # Primer impacto
                self.rebounded = True
                self.rebound_count = 1
                self.first_impact_time = current_time
                self.v = -abs(self.v) * self.restitution  # Rebote
                self.t = 0.98  # Retroceder un poco
                print(f"{self.name} IMPACTO! t={current_time:.2f}s")
            elif self.rebound_count < self.max_rebounds and abs(self.v) > self.min_velocity:
                # Rebotes subsiguientes
                self.rebound_count += 1
                self.v = -abs(self.v) * (self.restitution ** self.rebound_count)  # Rebote más débil
                self.t = 1.0 - (0.1 / self.rebound_count)  # Retroceder según rebote
            else:
                # Detenerse completamente
                self.v = 0
                self.t = 1.0
                self.finished = True
                self.wall_stopped = True
                self.final_stop_time = current_time
                print(f"{self.name} DETENIDA! Tiempo final: {current_time:.2f}s")
        
        elif new_t <= 0.0:  # Vuelve al inicio
            self.v = abs(self.v) * self.restitution  # Rebote hacia adelante
            self.t = 0.01  # Avanzar un poco
        
        else:
            self.t = new_t  # Movimiento normal
        
        # Actualizar posición visual
        if not self.finished and 0 <= self.t <= 1:
            self.base_pos = self.get_center_position_at_t(self.t)
            self.base_pos[1] += self.radius  # Ajustar por radio

    def get_position_and_slope(self, t):
        """Obtener posición y pendiente para parámetro t"""
        pos = self.get_center_position_at_t(t)
        
        if not self.slopes:
            return pos, 0
            
        # Interpolar pendiente
        idx = int(t * (len(self.points_center) - 1))
        idx = min(idx, len(self.points_center) - 2)
        
        t_segment = t * (len(self.points_center) - 1) - idx
        slope_prev = self.slopes[idx]
        slope_next = self.slopes[idx + 1]
        slope = slope_prev + t_segment * (slope_next - slope_prev)
        
        return pos, slope

    def get_render_position(self):
        """Obtener posición para renderizado"""
        return self.base_pos.copy()

    def set_radius(self, nuevo_radius):
        """Cambiar radio de la bola"""
        self.radius = nuevo_radius
        
    def set_masa(self, nueva_masa):
        """Cambiar masa de la bola"""
        self.masa = nueva_masa
        
    def set_rozamiento(self, nuevo_rozamiento):
        """Cambiar coeficiente de rozamiento"""
        self.mu = nuevo_rozamiento
        self.mu_ramp = nuevo_rozamiento * 2.0

    def reset_to_platform(self):
        """Resetear la bola a la plataforma con la altura ACTUAL"""
        self.on_platform = True
        self.platform_released = False
        self.t = 0.0
        self.v = 0.0
        self.finished = False
        self.rebounded = False
        self.rebound_count = 0
        self.wall_stopped = False
        self.first_impact_time = None
        self.final_stop_time = None
        self._forzar_posicion_inicial()

def get_esferas(config_esferas=None):
    """Crear lista de esferas para la simulación"""
    if config_esferas is None:
        # Configuración por defecto: 3 esferas en rampas separadas
        return [
            Esfera(line_curve_3d, (1.0, 1.0, 0.0), "Línea Recta", z_offset=-RAMP_SEPARATION),
            Esfera(parabolic_curve_3d, (0.0, 0.0, 1.0), "Parábola", z_offset=0.0),
            Esfera(cycloid_curve_3d, (1.0, 0.0, 0.0), "Cicloide", z_offset=RAMP_SEPARATION)
        ]
    else:
        # Configuración personalizada
        esferas = []
        for config in config_esferas:
            esfera = Esfera(
                curve_func=config['curve_func'],
                color=config['color'],
                name=config['name'],
                z_offset=config.get('z_offset', 0.0),
                radius=config.get('radius', 0.15),
                masa=config.get('masa', 1.0),
                rozamiento_base=config.get('rozamiento')
            )
            esferas.append(esfera)
        return esferas