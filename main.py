import pygame
import sys
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from Esferas import get_esferas
from Rampas import RampaManager
from Textura import seleccionar_textura
from Escena import Escena

# Constantes de la ventana
WIDTH, HEIGHT = 1200, 800
FPS = 60

class Brachistochrone3DSimulation:
    def __init__(self):
        # Inicializar pygame y OpenGL
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.OPENGL)
        pygame.display.set_caption("BRAQUISTÓCRONA 3D - SISTEMA GENERAL")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 1. FLUJO OBLIGATORIO: Pedir textura usando Textura.py
        print("=" * 60)
        print("INICIALIZANDO SISTEMA BRAQUISTÓCRONA 3D GENERAL")
        print("=" * 60)
        self.config_textura = seleccionar_textura()
        
        # 2. FLUJO OBLIGATORIO: Pedir punto A
        self.punto_A = self._solicitar_punto_A()
        
        # 3. FLUJO OBLIGATORIO: Generar rampas usando Rampas.py
        self.rampa_manager = RampaManager()
        self.rampa_manager.set_puntos(self.punto_A)
        
        # Obtener información de las rampas para las esferas
        config_esferas = self.rampa_manager.get_curvas_para_esferas()
        
        # 4. FLUJO OBLIGATORIO: Crear escena usando Escena.py
        self.escena = Escena(self.config_textura)
        
        # 5. IMPORTANTE: Crear esferas DESPUÉS de actualizar las rampas
        self.balls = get_esferas(config_esferas)
        
        # FORZAR INICIALIZACIÓN INMEDIATA DE POSICIONES CON LA ALTURA CORRECTA
        self._forzar_inicializacion_esferas()
        
        # Inicializar variables de simulación
        self.start_time = None  # Tiempo de inicio de simulación
        self.simulation_started = False  # Estado de simulación
        self.finished_balls = 0  # Contador de bolas terminadas
        self.last_ball_stop_time = None  # Tiempo de última bola detenida
        self.all_balls_stopped = False  # Si todas las bolas se detuvieron
        
        # Variables de la plataforma
        self.platform_position_x = self.punto_A[0]  # Posición X inicial
        self.platform_height = self.punto_A[1] + 0.3  # Altura de plataforma
        self.platform_moving = False  # Estado de movimiento
        self.platform_speed = 2.0  # Velocidad de retroceso
        
        # Variables de cámara
        self.camera_distance = 18.0  # Distancia de la cámara
        self.camera_angle_x = 35.0  # Ángulo vertical
        self.camera_angle_y = -30.0  # Ángulo horizontal
        self.camera_position = [0.0, 2.0, 0.0]  # Posición de cámara
        self.dragging = False  # Estado de arrastre de ratón
        self.last_mouse_pos = None  # Última posición del ratón
        
        # Velocidades de control de cámara
        self.camera_move_speed = 5.0
        self.camera_rotate_speed = 50.0
        self.camera_zoom_speed = 10.0
        
        # Fuentes para texto
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.setup_opengl()  # Configurar OpenGL
        
        # VERIFICACIÓN FINAL
        self._verificar_posiciones()

    def _solicitar_punto_A(self):
        """Solicita al usuario las coordenadas del punto A de forma más flexible"""
        print("\n" + "="*50)
        print("CONFIGURACIÓN PUNTO INICIAL A")
        print("="*50)
        print("Punto A es el punto ALTO de inicio de las rampas")
        print("Punto B se fijará automáticamente a 1 metro de altura")
        print("="*50)
        
        try:
            # Solicitar coordenadas con valores por defecto
            x = float(input("Coordenada X del punto A (recomendado: 1.0-3.0): ") or "1.0")
            y = float(input("Coordenada Y del punto A (altura, recomendado: 3.0-10.0): ") or "5.0")
            z = 0.0
            
            # Validar valores razonables
            if y <= 1.0:
                print("Altura debe ser mayor a 1.0 metro. Usando 5.0 metros.")
                y = 5.0
            if x < 0:
                print("Coordenada X negativa. Usando 1.0 metro.")
                x = 1.0
                
            print(f"Punto A configurado en ({x}, {y}, {z})")
            return (x, y, z)
        except ValueError:
            print("Entrada inválida. Usando valores por defecto (1.0, 5.0, 0.0)")
            return (1.0, 5.0, 0.0)

    def _forzar_inicializacion_esferas(self):
        """FORZAR inicialización de las esferas con la altura ACTUALIZADA"""
        print("FORZANDO inicialización de esferas con altura actual...")
        
        # Asegurarse de que tenemos la altura más reciente
        from Rampas import A_METERS
        print(f"Altura actual de A_METERS: {A_METERS[1]:.2f} metros")
        
        for i, ball in enumerate(self.balls):
            # Forzar reinicialización completa con la altura actual
            ball.initialize_position()
            
            # Verificación adicional
            ball_pos = ball.get_render_position()
            expected_height = A_METERS[1] + 0.3 + ball.radius
            print(f"   {ball.name}:")
            print(f"      - Posición actual: ({ball_pos[0]:.2f}, {ball_pos[1]:.2f}, {ball_pos[2]:.2f})")
            print(f"      - Altura esperada: {expected_height:.2f}")
            print(f"      - ¿Coincide?: {'SÍ' if abs(ball_pos[1] - expected_height) < 0.01 else 'NO'}")
        
        print("TODAS las esferas forzadas a posición correcta con altura actualizada")

    def _verificar_posiciones(self):
        """Verificación final de que todas las posiciones son correctas"""
        from Rampas import A_METERS
        
        print("\n" + "="*60)
        print("VERIFICACIÓN FINAL DE POSICIONES")
        print("="*60)
        print(f"Altura configurada A_METERS[1]: {A_METERS[1]:.2f} metros")
        print(f"Posición plataforma X: {self.platform_position_x:.2f}")
        print(f"Altura plataforma: {self.platform_height:.2f} metros")
        
        for ball in self.balls:
            pos = ball.get_render_position()
            expected_y = A_METERS[1] + 0.3 + ball.radius
            print(f"{ball.name}:")
            print(f"  - Posición: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
            print(f"  - Esperado Y: {expected_y:.2f}")
            print(f"  - CORRECTO" if abs(pos[1] - expected_y) < 0.01 else "  - ERROR")
        
        print("="*60)

    def setup_opengl(self):
        """Configuración de OpenGL - MEJORADA: iluminación más brillante"""
        # Habilitar características
        glEnable(GL_DEPTH_TEST)  # Prueba de profundidad
        glEnable(GL_LIGHTING)  # Iluminación
        glEnable(GL_LIGHT0)  # Luz 0
        glEnable(GL_LIGHT1)  # Luz 1
        glEnable(GL_COLOR_MATERIAL)  # Material de color
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # MEJORA: Iluminación más brillante
        # Luz principal
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 15.0, 5.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.6, 0.6, 0.6, 1.0])  # Más brillante
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.2, 1.2, 1.2, 1.0])  # Más brillante
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        
        # Luz secundaria
        glLightfv(GL_LIGHT1, GL_POSITION, [-5.0, 10.0, -5.0, 1.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])  # Más brillante
        glLightfv(GL_LIGHT1, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])  # Más brillante
        
        # Material especular
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 128.0)
        
        # MEJORA: Fondo más claro
        glClearColor(0.5, 0.5, 0.6, 1.0)  # Más claro
        glEnable(GL_NORMALIZE)  # Normalizar normales
        glShadeModel(GL_SMOOTH)  # Sombreado suave

    def handle_events(self):
        """Manejar eventos de entrada"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.simulation_started:
                    # Iniciar simulación
                    self.simulation_started = True
                    self.start_time = pygame.time.get_ticks()
                    print("¡Simulación iniciada! Las bolas bajarán por las rampas...")
                elif event.key == pygame.K_r:
                    self.restart_simulation()  # Reiniciar
                elif event.key == pygame.K_ESCAPE:
                    self.running = False  # Salir
                elif event.key == pygame.K_c:
                    self.mostrar_controles()  # Mostrar controles
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.dragging = True  # Iniciar arrastre
                    self.last_mouse_pos = pygame.mouse.get_pos()
                elif event.button == 4:
                    self.camera_distance = max(8.0, self.camera_distance - 1.0)  # Zoom in
                elif event.button == 5:
                    self.camera_distance += 1.0  # Zoom out
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False  # Terminar arrastre
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                # Rotar cámara con arrastre
                current_pos = pygame.mouse.get_pos()
                dx = current_pos[0] - self.last_mouse_pos[0]
                dy = current_pos[1] - self.last_mouse_pos[1]
                
                self.camera_angle_y += dx * 0.5
                self.camera_angle_x += dy * 0.5
                self.camera_angle_x = max(-90, min(90, self.camera_angle_x))  # Limitar
                self.last_mouse_pos = current_pos
        
        # Control de cámara con teclado
        keys = pygame.key.get_pressed()
        dt = self.clock.get_time() / 1000.0  # Delta time
        
        # Movimiento WASD
        if keys[pygame.K_w]:
            angle_rad = np.radians(self.camera_angle_y)
            self.camera_position[0] -= np.sin(angle_rad) * self.camera_move_speed * dt
            self.camera_position[2] -= np.cos(angle_rad) * self.camera_move_speed * dt
        if keys[pygame.K_s]:
            angle_rad = np.radians(self.camera_angle_y)
            self.camera_position[0] += np.sin(angle_rad) * self.camera_move_speed * dt
            self.camera_position[2] += np.cos(angle_rad) * self.camera_move_speed * dt
        if keys[pygame.K_a]:
            angle_rad = np.radians(self.camera_angle_y)
            self.camera_position[0] -= np.cos(angle_rad) * self.camera_move_speed * dt
            self.camera_position[2] += np.sin(angle_rad) * self.camera_move_speed * dt
        if keys[pygame.K_d]:
            angle_rad = np.radians(self.camera_angle_y)
            self.camera_position[0] += np.cos(angle_rad) * self.camera_move_speed * dt
            self.camera_position[2] -= np.sin(angle_rad) * self.camera_move_speed * dt
        
        # Rotación con flechas
        if keys[pygame.K_LEFT]:
            self.camera_angle_y -= self.camera_rotate_speed * dt
        if keys[pygame.K_RIGHT]:
            self.camera_angle_y += self.camera_rotate_speed * dt
        if keys[pygame.K_UP]:
            self.camera_angle_x -= self.camera_rotate_speed * dt
        if keys[pygame.K_DOWN]:
            self.camera_angle_x += self.camera_rotate_speed * dt
        
        # Movimiento vertical
        if keys[pygame.K_q]:
            self.camera_position[1] += self.camera_move_speed * dt
        if keys[pygame.K_e]:
            self.camera_position[1] -= self.camera_move_speed * dt
        
        # Zoom con teclado
        if keys[pygame.K_PLUS] or keys[pygame.K_KP_PLUS]:
            self.camera_distance = max(8.0, self.camera_distance - self.camera_zoom_speed * dt)
        if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
            self.camera_distance += self.camera_zoom_speed * dt
        
        # Limitar ángulo vertical
        self.camera_angle_x = max(-90, min(90, self.camera_angle_x))

    def mostrar_controles(self):
        """Mostrar controles disponibles"""
        print("\n" + "="*50)
        print("CONTROLES DE CÁMARA")
        print("="*50)
        print("W/A/S/D - Mover cámara")
        print("Q/E - Subir/Bajar cámara")
        print("Flechas - Rotar cámara")
        print("+/- - Zoom")
        print("Click + arrastrar - Rotar vista")
        print("Rueda del ratón - Zoom")
        print("ESPACIO - Iniciar simulación")
        print("R - Reiniciar simulación")
        print("C - Mostrar controles")
        print("ESC - Salir")
        print("="*50)

    def restart_simulation(self):
        """Reiniciar simulación"""
        config_esferas = self.rampa_manager.get_curvas_para_esferas()
        self.balls = get_esferas(config_esferas)
        self._forzar_inicializacion_esferas()  # FORZAR REINICIALIZACIÓN
        self.simulation_started = False
        self.start_time = None
        self.finished_balls = 0
        self.last_ball_stop_time = None
        self.all_balls_stopped = False
        self.platform_position_x = self.punto_A[0]
        self.platform_height = self.punto_A[1] + 0.3
        self.platform_moving = False
        print("Simulación reiniciada")

    def setup_camera(self):
        """Configurar vista de cámara"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, WIDTH/HEIGHT, 0.1, 100.0)  # Proyección perspectiva
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Aplicar transformaciones de cámara
        glTranslatef(0.0, -2.0, -self.camera_distance)  # Alejar
        glRotatef(self.camera_angle_x, 1.0, 0.0, 0.0)  # Rotar X
        glRotatef(self.camera_angle_y, 0.0, 1.0, 0.0)  # Rotar Y
        glTranslatef(-self.camera_position[0], -self.camera_position[1], -self.camera_position[2])  # Mover

    def run(self):
        """Bucle principal"""
        self.mostrar_controles()
        
        # Mostrar información de configuración
        print(f"\nCONFIGURACIÓN ACTUAL:")
        print(f"   Punto A: {self.punto_A}")
        print(f"   Punto B: {self.rampa_manager.punto_B}")
        print(f"   Altura de plataforma: {self.platform_height:.2f} metros")
        print(f"   Textura: {self.config_textura['tipo']}")
        print(f"   Presiona ESPACIO para iniciar la simulación\n")
        
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time
            self.handle_events()  # Procesar eventos
            
            if self.simulation_started:
                # CORRECCIÓN: Cambiar start_time por self.start_time
                current_time = (pygame.time.get_ticks() - self.start_time) / 1000.0
                
                # Plataforma se mueve y libera bolas
                if current_time >= 2.0 and not self.platform_moving:
                    self.platform_moving = True
                    print("¡La plataforma se está moviendo hacia atrás!")
                
                if self.platform_moving and self.platform_position_x > self.punto_A[0] - 3.0:
                    self.platform_position_x -= self.platform_speed * dt
                
                # Liberar bolas cuando la plataforma se ha movido lo suficiente
                if self.platform_position_x <= self.punto_A[0] - 1.5 and not all(ball.platform_released for ball in self.balls):
                    for ball in self.balls:
                        if not ball.platform_released:
                            ball.release_from_platform()
                            print(f"{ball.name} liberada!")
                
                # Actualizar física de las bolas
                stopped_balls = 0
                for ball in self.balls:
                    if not ball.on_platform:
                        ball.update(dt, current_time)
                    
                    if ball.wall_stopped:
                        stopped_balls += 1
                
                # Verificar si todas las bolas se han detenido
                if not self.all_balls_stopped and stopped_balls == len(self.balls):
                    self.all_balls_stopped = True
                    self.last_ball_stop_time = current_time
                    print(f"¡TODAS LAS BOLAS DETENIDAS! Tiempo final: {self.last_ball_stop_time:.2f}s")
            
            # Renderizar la escena completa
            self.escena.render(
                setup_camera_func=self.setup_camera,
                platform_position_x=self.platform_position_x,
                platform_height=self.platform_height,
                balls=self.balls,
                simulation_started=self.simulation_started,
                start_time=self.start_time,
                all_balls_stopped=self.all_balls_stopped,
                last_ball_stop_time=self.last_ball_stop_time,
                font=self.font,
                small_font=self.small_font
            )
            
            pygame.display.flip()  # Actualizar pantalla
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("=" * 60)
    print("BRAQUISTÓCRONA 3D - SISTEMA GENERAL MODULAR")
    print("=" * 60)
    sim = Brachistochrone3DSimulation()
    sim.run()