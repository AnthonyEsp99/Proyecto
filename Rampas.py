import numpy as np

# Valores por defecto para puntos A y B
A_METERS_DEFAULT = np.array([1.0, 5.0, 0.0], dtype=float)  # Punto inicial alto
B_METERS_DEFAULT = np.array([7.0, 1.0, 0.0], dtype=float)  # Punto final bajo (altura fija 1m)
RAMP_SEPARATION_DEFAULT = 1.0  # Separación entre rampas

# Variables globales que se actualizarán dinámicamente
A_METERS = A_METERS_DEFAULT.copy()
B_METERS = B_METERS_DEFAULT.copy()
RAMP_SEPARATION = RAMP_SEPARATION_DEFAULT

def line_curve_3d(t, width=0.5, z_offset=0.0):
    """Línea recta - de A (alto) a B (bajo)"""
    # Interpolación lineal entre A y B
    pos_meters = A_METERS + t * (B_METERS - A_METERS)
    # Crear rails izquierdo y derecho
    left_rail = np.array([pos_meters[0], pos_meters[1], -width/2 + z_offset])
    right_rail = np.array([pos_meters[0], pos_meters[1], width/2 + z_offset])
    return left_rail, right_rail

def parabolic_curve_3d(t, width=0.5, z_offset=0.0):
    """Parábola - de A (alto) a B (bajo) con caída vertical inicial"""
    # Interpolación lineal en X
    x_meters = A_METERS[0] + t * (B_METERS[0] - A_METERS[0])
    # Interpolación en Y con término parabólico para caída inicial
    y_meters = A_METERS[1] + t * (B_METERS[1] - A_METERS[1]) - 3.0 * t * (1 - t)
    # Crear rails
    left_rail = np.array([x_meters, y_meters, -width/2 + z_offset])
    right_rail = np.array([x_meters, y_meters, width/2 + z_offset])
    return left_rail, right_rail

def cycloid_curve_3d(t, width=0.5, z_offset=0.0):
    """Cicloide - de A (alto) a B (bajo) con pendiente vertical inicial"""
    # Calcular diferencias entre A y B
    dx_meters = B_METERS[0] - A_METERS[0]  # Diferencia en X
    dy_meters = A_METERS[1] - B_METERS[1]  # Diferencia en Y (positiva)
    
    # Parámetros de la cicloide
    R = dy_meters / 2  # Radio de la cicloide
    theta = np.pi * t  # Ángulo de 0 a π
    
    # Ecuaciones paramétricas de la cicloide
    x_cycloid = R * (theta - np.sin(theta))
    y_cycloid = -R * (1 - np.cos(theta))
    
    # Escalar para ajustar al ancho deseado
    x_final = R * np.pi  # Longitud total de la cicloide
    scale_x = dx_meters / x_final  # Factor de escala en X
    
    # Aplicar transformaciones
    x_meters = A_METERS[0] + x_cycloid * scale_x
    y_meters = A_METERS[1] + y_cycloid
    
    # Crear rails
    left_rail = np.array([x_meters, y_meters, -width/2 + z_offset])
    right_rail = np.array([x_meters, y_meters, width/2 + z_offset])
    
    return left_rail, right_rail

class RampaManager:
    def __init__(self):
        # Inicializar con valores por defecto
        self.punto_A = A_METERS_DEFAULT.copy()
        self.punto_B = B_METERS_DEFAULT.copy()
        self.separacion = RAMP_SEPARATION_DEFAULT
        self.rampas = {}  # Diccionario para almacenar rampas
        self.generar_rampas()  # Generar rampas iniciales

    def set_puntos(self, punto_A, separacion=None):
        """Configurar punto A (punto B se fija a altura 1 metro)"""
        self.punto_A = np.array(punto_A, dtype=float)
        
        # Punto B fijo: misma x relativa (a 6 metros de A) y altura fija 1.0
        self.punto_B = np.array([
            self.punto_A[0] + 6.0,  # 6 metros a la derecha del punto A
            1.0,  # Altura fija de 1.0 metro
            0.0
        ])
        
        if separacion is not None:
            self.separacion = separacion
        
        # Actualizar variables globales para las funciones de curva - ESTO ES CRÍTICO
        global A_METERS, B_METERS, RAMP_SEPARATION
        A_METERS = self.punto_A.copy()
        B_METERS = self.punto_B.copy()
        RAMP_SEPARATION = self.separacion
        
        self.generar_rampas()  # Regenerar rampas con nuevos puntos
        print(f"Rampas generadas: A{self.punto_A} -> B{self.punto_B}, separación: {self.separacion}m")

    def generar_rampas(self):
        """Genera automáticamente las tres rampas en orden: Cicloide, Parábola, Recta"""
        self.rampas = {
            "Cicloide": {
                "geometria": self._generar_geometria_rampa(cycloid_curve_3d, z_offset=self.separacion),
                "funcion": cycloid_curve_3d,
                "z_offset": self.separacion,
                "color": (0.4, 0.7, 1.0) # Rojo
            },
            "Parábola": {
                "geometria": self._generar_geometria_rampa(parabolic_curve_3d, z_offset=0.0),
                "funcion": parabolic_curve_3d,
                "z_offset": 0.0,
                "color": (0.0, 1.0, 1.0)  # Azul
            },
            "Recta": {
                "geometria": self._generar_geometria_rampa(line_curve_3d, z_offset=-self.separacion),
                "funcion": line_curve_3d,
                "z_offset": -self.separacion,
                "color": (1.0, 1.0, 0.0)  # Amarillo
            }
        }

    def _generar_geometria_rampa(self, curve_func, z_offset=0.0, segments=100):
        """Genera la geometría completa de una rampa"""
        vertices = []
        # Generar puntos a lo largo de la curva
        for i in range(segments + 1):
            t = i / segments  # Parámetro de 0 a 1
            left, right = curve_func(t, z_offset=z_offset)
            vertices.append((left, right))  # Almacenar par de rails
        return vertices

    def get_geometria_rampas(self):
        """Devuelve la geometría completa de cada rampa"""
        return self.rampas

    def get_info_tapas(self):
        """Devuelve información necesaria para generar tapas sin huecos"""
        return {
            "ancho_base": 0.7,
            "altura_tapa_trasera": self.punto_A[1],  # Altura del punto A
            "altura_tapa_delantera": 0.4,
            "grosor_pared": 0.3,
            "separacion": self.separacion,
            "punto_A": self.punto_A,
            "punto_B": self.punto_B
        }

    def get_curvas_para_esferas(self):
        """Devuelve la información necesaria para crear las esferas"""
        return [
            {
                "curve_func": self.rampas["Recta"]["funcion"],
                "color": self.rampas["Recta"]["color"],
                "name": "Línea Recta",
                "z_offset": self.rampas["Recta"]["z_offset"],
                "radius": 0.15
            },
            {
                "curve_func": self.rampas["Parábola"]["funcion"],
                "color": self.rampas["Parábola"]["color"],
                "name": "Parábola",
                "z_offset": self.rampas["Parábola"]["z_offset"],
                "radius": 0.15
            },
            {
                "curve_func": self.rampas["Cicloide"]["funcion"],
                "color": self.rampas["Cicloide"]["color"],
                "name": "Cicloide",
                "z_offset": self.rampas["Cicloide"]["z_offset"],
                "radius": 0.15
            }
        ]