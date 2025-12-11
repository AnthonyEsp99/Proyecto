import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from Rampas import A_METERS, B_METERS, RAMP_SEPARATION, line_curve_3d, parabolic_curve_3d, cycloid_curve_3d
from Textura import load_ppm_texture, create_improved_wood_texture, create_improved_iron_texture

class RealTimeReflectionSystem:
    def __init__(self, cube_size=128):
        # Inicializar el sistema de reflejos en tiempo real
        self.cube_size = cube_size  # Tamaño del cubemap para reflejos
        self.fbo = None  # Framebuffer object
        self.cube_map = None  # Textura cubemap
        self.setup_cube_map()  # Configurar el cubemap
        
    def setup_cube_map(self):
        """Configurar cubemap dinámico para reflejos en tiempo real"""
        # Generar framebuffer y textura cubemap
        self.fbo = glGenFramebuffers(1)
        self.cube_map = glGenTextures(1)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.cube_map)
        
        # Crear las 6 caras del cubemap vacías
        for i in range(6):
            glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB, 
                         self.cube_size, self.cube_size, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
        
        # Configurar parámetros de textura
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
        
        print(f"Cubemap dinámico creado: {self.cube_size}x{self.cube_size}")

    def render_to_cube_map(self, ball_position, render_scene_function):
        """Renderizar la escena a las 6 caras del cubemap"""
        if self.fbo is None or self.cube_map is None:
            return
            
        # Guardar viewport actual
        old_viewport = glGetIntegerv(GL_VIEWPORT)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        
        # Configurar proyección para vistas de 90 grados
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(90, 1.0, 0.1, 50.0)
        
        # Definir las 6 direcciones de vista del cubemap
        cube_faces = [
            (GL_TEXTURE_CUBE_MAP_POSITIVE_X, [1.0, 0.0, 0.0, 0.0, -1.0, 0.0]),
            (GL_TEXTURE_CUBE_MAP_NEGATIVE_X, [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0]),
            (GL_TEXTURE_CUBE_MAP_POSITIVE_Y, [0.0, 1.0, 0.0, 0.0, 0.0, 1.0]),
            (GL_TEXTURE_CUBE_MAP_NEGATIVE_Y, [0.0, -1.0, 0.0, 0.0, 0.0, -1.0]),
            (GL_TEXTURE_CUBE_MAP_POSITIVE_Z, [0.0, 0.0, 1.0, 0.0, -1.0, 0.0]),
            (GL_TEXTURE_CUBE_MAP_NEGATIVE_Z, [0.0, 0.0, -1.0, 0.0, -1.0, 0.0])
        ]
        
        # Renderizar cada cara del cubemap
        for i, (face, (dx, dy, dz, ux, uy, uz)) in enumerate(cube_faces):
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, face, self.cube_map, 0)
            
            if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
                continue
            
            glViewport(0, 0, self.cube_size, self.cube_size)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Configurar vista desde la posición de la bola
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            gluLookAt(ball_position[0], ball_position[1], ball_position[2],
                     ball_position[0] + dx, ball_position[1] + dy, ball_position[2] + dz,
                     ux, uy, uz)
            
            # Renderizar escena excluyendo la bola actual
            render_scene_function(ball_position)
            glPopMatrix()
        
        # Restaurar configuración anterior
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(old_viewport[0], old_viewport[1], old_viewport[2], old_viewport[3])

class Escena:
    def __init__(self, config_textura):
        # Inicializar la escena con configuración de texturas
        self.config_textura = config_textura
        self.wood_texture = None  # Textura de madera para estructura
        self.ramp_surface_texture = None  # Textura específica para las superficies de las curvas
        self.reflection_system = RealTimeReflectionSystem(cube_size=128)
        self.cargar_texturas()

    def cargar_texturas(self):
        """Carga las texturas según la configuración - solo superficies de curvas cambian"""
        # Cargar textura de madera para estructura (SIEMPRE madera.ppm)
        self.wood_texture = load_ppm_texture("madera.ppm")
        if self.wood_texture is None:
            print("ADVERTENCIA: No se encontró madera.ppm. Usando textura procedural de madera.")
            self.wood_texture = create_improved_wood_texture()
        else:
            print("Textura de madera (estructura) cargada (madera.ppm)")
        
        # Cargar textura específica para las superficies de las curvas según selección
        texture_file = self.config_textura["archivo"]
        self.ramp_surface_texture = load_ppm_texture(texture_file)
        
        if self.ramp_surface_texture is None:
            # Si no se encuentra el archivo, crear textura procedural según el tipo
            if self.config_textura["tipo"] == "Hierro":
                self.ramp_surface_texture = load_ppm_texture("hierro.ppm")
                if self.ramp_surface_texture is None:
                    print("ADVERTENCIA: No se encontró hierro.ppm. Usando textura procedural de hierro.")
                    self.ramp_surface_texture = create_improved_iron_texture()
                else:
                    print("Textura de hierro para curvas cargada (hierro.ppm)")
            elif self.config_textura["tipo"] == "Madera":
                # Para madera, usar madera2.ppm para las superficies de las rampas
                self.ramp_surface_texture = load_ppm_texture("madera2.ppm")
                if self.ramp_surface_texture is None:
                    print("ADVERTENCIA: No se encontró madera2.ppm. Usando textura procedural de madera.")
                    self.ramp_surface_texture = create_improved_wood_texture()
                else:
                    print("Textura de madera para curvas cargada (madera2.ppm)")
            elif self.config_textura["tipo"] == "Plástico":
                self.ramp_surface_texture = load_ppm_texture("plastico.ppm")
                if self.ramp_surface_texture is None:
                    print("ADVERTENCIA: No se encontró plastico.ppm. Usando textura procedural de plástico.")
                    self.ramp_surface_texture = self.create_plastic_texture()
                else:
                    print("Textura de plástico para curvas cargada (plastico.ppm)")
        else:
            print(f"Textura de {self.config_textura['tipo']} para curvas cargada ({texture_file})")

    def create_plastic_texture(self):
        """Crear textura procedural de plástico para superficies de curvas"""
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        # Configurar parámetros de textura
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        
        # Crear datos de textura procedural
        width, height = 256, 256
        texture_data = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Color base para plástico (azul grisáceo claro)
        base_color = [180, 190, 210]
        
        for y in range(height):
            for x in range(width):
                # Patrón sutil para plástico con ruido y grano
                noise = np.random.normal(0, 6)
                grain = np.sin(x * 0.05) * np.cos(y * 0.05) * 8
                
                # Calcular componentes de color con variaciones
                r = max(150, min(220, base_color[0] + grain + noise))
                g = max(160, min(230, base_color[1] + grain * 0.8 + noise * 0.9))
                b = max(170, min(240, base_color[2] + grain * 0.6 + noise * 0.8))
                
                # Añadir brillo plástico sutil en patrones
                if (x + y) % 80 < 3:
                    r = min(255, r + 40)
                    g = min(255, g + 40)
                    b = min(255, b + 40)
                
                texture_data[y, x] = [int(r), int(g), int(b)]
        
        # Cargar textura en OpenGL
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, 
                    GL_RGB, GL_UNSIGNED_BYTE, texture_data)
        
        return texture_id

    def draw_floor(self):
        """Dibujar plano de referencia con patrón de ajedrez"""
        glEnable(GL_LIGHTING)
        glColor4f(0.45, 0.45, 0.5, 1.0)  # Color base del piso
        
        glBegin(GL_QUADS)
        size = 20  # Tamaño del piso
        for x in range(-size, size):
            for z in range(-size, size):
                # Alternar colores para patrón de ajedrez
                if (x + z) % 2 == 0:
                    glColor4f(0.5, 0.5, 0.55, 1.0)  # Color claro
                else:
                    glColor4f(0.4, 0.4, 0.45, 1.0)  # Color oscuro
                # Dibujar cuadrado del piso
                glVertex3f(x, 0, z)
                glVertex3f(x+1, 0, z)
                glVertex3f(x+1, 0, z+1)
                glVertex3f(x, 0, z+1)
        glEnd()

    def draw_platform(self, platform_position_x, platform_height):
        """Dibujar plataforma con textura de madera"""
        # No dibujar si la plataforma se movió demasiado
        if platform_position_x < A_METERS[0] - 3.0:
            return
            
        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.wood_texture)  # SIEMPRE madera.ppm
        glColor3f(0.9, 0.7, 0.5)  # Color de madera
        
        # Dimensiones de la plataforma
        platform_width = 3.0
        platform_length = 2.0
        platform_thickness = 0.1
        
        x_position = platform_position_x
        y_position = platform_height
        z_center = 0.0
        
        # Transformar y escalar la plataforma
        glPushMatrix()
        glTranslatef(x_position, y_position, z_center)
        glScalef(platform_length, platform_thickness, platform_width)
        
        # Definir vértices del cubo
        size = 0.5
        vertices = [
            [-size, -size, size], [size, -size, size], [size, size, size], [-size, size, size],
            [-size, -size, -size], [-size, size, -size], [size, size, -size], [size, -size, -size],
            [-size, size, -size], [-size, size, size], [size, size, size], [size, size, -size],
            [-size, -size, -size], [size, -size, -size], [size, -size, size], [-size, -size, size],
            [size, -size, -size], [size, size, -size], [size, size, size], [size, -size, size],
            [-size, -size, -size], [-size, -size, size], [-size, size, size], [-size, size, -size]
        ]
        
        # Coordenadas de textura para cada vértice
        tex_coords = [
            [0, 0], [1, 0], [1, 1], [0, 1],
            [0, 0], [0, 1], [1, 1], [1, 0],
            [0, 1], [0, 0], [1, 0], [1, 1],
            [0, 0], [1, 0], [1, 1], [0, 1],
            [0, 0], [0, 1], [1, 1], [1, 0],
            [0, 0], [1, 0], [1, 1], [0, 1]
        ]
        
        # Índices de las caras del cubo
        indices = [
            [0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11],
            [12, 13, 14, 15], [16, 17, 18, 19], [20, 21, 22, 23]
        ]
        
        # Dibujar todas las caras del cubo
        glBegin(GL_QUADS)
        for face in indices:
            for i, vertex_idx in enumerate(face):
                glTexCoord2fv(tex_coords[vertex_idx])
                glVertex3fv(vertices[vertex_idx])
        glEnd()
        
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

    def draw_wall(self):
        """Dibujar muro con textura de madera"""
        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.wood_texture)  # SIEMPRE madera.ppm
        glColor3f(0.8, 0.6, 0.4)  # Color de madera
        
        # Dimensiones del muro
        wall_x = B_METERS[0] + 0.2  # Posición X del muro
        wall_height = 2.0
        wall_width = 3.0
        wall_thickness = 0.1
        
        # Transformar y escalar el muro
        glPushMatrix()
        glTranslatef(wall_x, wall_height/2, 0.0)
        glScalef(wall_thickness, wall_height, wall_width)
        
        # Vértices del cubo (mismo que plataforma pero con diferentes coordenadas de textura)
        size = 0.5
        vertices = [
            [-size, -size, size], [size, -size, size], [size, size, size], [-size, size, size],
            [-size, -size, -size], [-size, size, -size], [size, size, -size], [size, -size, -size],
            [-size, size, -size], [-size, size, size], [size, size, size], [size, size, -size],
            [-size, -size, -size], [size, -size, -size], [size, -size, size], [-size, -size, size],
            [size, -size, -size], [size, size, -size], [size, size, size], [size, -size, size],
            [-size, -size, -size], [-size, -size, size], [-size, size, size], [-size, size, -size]
        ]
        
        # Coordenadas de textura escaladas para el muro
        tex_coords = [
            [0, 0], [2, 0], [2, 2], [0, 2],
            [0, 0], [0, 2], [2, 2], [2, 0],
            [0, 2], [0, 0], [2, 0], [2, 2],
            [0, 0], [2, 0], [2, 2], [0, 2],
            [0, 0], [0, 2], [2, 2], [2, 0],
            [0, 0], [2, 0], [2, 2], [0, 2]
        ]
        
        indices = [
            [0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11],
            [12, 13, 14, 15], [16, 17, 18, 19], [20, 21, 22, 23]
        ]
        
        # Dibujar el muro
        glBegin(GL_QUADS)
        for face in indices:
            for i, vertex_idx in enumerate(face):
                glTexCoord2fv(tex_coords[vertex_idx])
                glVertex3fv(vertices[vertex_idx])
        glEnd()
        
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

    def draw_ramp_base(self, curve_func, color, z_offset=0.0, platform_height=None):
        """Dibujar base de rampa - SOLO la superficie de la curva cambia de textura"""
        base_width = 0.7  # Ancho de la base de la rampa
        segments = 100    # Número de segmentos para suavizar la curva
        
        # SUPERFICIE DE RODAMIENTO - usa textura seleccionada
        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.ramp_surface_texture)  # Textura seleccionada
        glColor3f(1.0, 1.0, 1.0)  # Color blanco para no afectar textura
        
        # Calcular longitud total de la curva para mapeo de textura
        total_length = 0
        prev_point = None
        for i in range(segments + 1):
            t = i / segments
            left, right = curve_func(t, z_offset=z_offset)
            center = (left + right) / 2.0
            if prev_point is not None:
                total_length += np.linalg.norm(center - prev_point)
            prev_point = center
        
        # Dibujar superficie de rodamiento con textura seleccionada
        glBegin(GL_QUADS)
        current_length = 0
        prev_point = None
        
        for i in range(segments):
            t1 = i / segments
            t2 = (i + 1) / segments
            
            # Obtener puntos de la curva
            left1, right1 = curve_func(t1, z_offset=z_offset)
            left2, right2 = curve_func(t2, z_offset=z_offset)
            
            # Calcular centros para longitud
            center1 = (left1 + right1) / 2.0
            center2 = (left2 + right2) / 2.0
            if prev_point is not None:
                segment_length = np.linalg.norm(center1 - prev_point)
                current_length += segment_length
            prev_point = center1
            
            # Calcular coordenadas de textura basadas en longitud
            tex_x1 = current_length / total_length * 4.0
            tex_x2 = (current_length + np.linalg.norm(center2 - center1)) / total_length * 4.0
            
            # Dibujar cuadrilátero de la superficie
            glTexCoord2f(tex_x1, 0.0); glVertex3f(left1[0], left1[1], left1[2])
            glTexCoord2f(tex_x2, 0.0); glVertex3f(left2[0], left2[1], left2[2])
            glTexCoord2f(tex_x2, 1.0); glVertex3f(right2[0], right2[1], right2[2])
            glTexCoord2f(tex_x1, 1.0); glVertex3f(right1[0], right1[1], right1[2])
        glEnd()
        
        glDisable(GL_TEXTURE_2D)
        
        # ESTRUCTURA BASE - SIEMPRE usa textura de madera (madera.ppm)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.wood_texture)  # SIEMPRE madera.ppm
        glColor3f(0.7, 0.5, 0.3)  # Color madera
        
        for i in range(segments):
            t1 = i / segments
            t2 = (i + 1) / segments
            
            left1, right1 = curve_func(t1, z_offset=z_offset)
            left2, right2 = curve_func(t2, z_offset=z_offset)
            
            # Calcular puntos base y en el suelo
            base_left1 = np.array([left1[0], left1[1], -base_width/2 + z_offset])
            base_right1 = np.array([right1[0], right1[1], base_width/2 + z_offset])
            base_left2 = np.array([left2[0], left2[1], -base_width/2 + z_offset])
            base_right2 = np.array([right2[0], right2[1], base_width/2 + z_offset])
            
            ground_left1 = np.array([left1[0], 0, -base_width/2 + z_offset])
            ground_right1 = np.array([right1[0], 0, base_width/2 + z_offset])
            ground_left2 = np.array([left2[0], 0, -base_width/2 + z_offset])
            ground_right2 = np.array([right2[0], 0, base_width/2 + z_offset])
            
            # Caras laterales - SIEMPRE madera.ppm
            glBegin(GL_QUADS)
            # Cara lateral izquierda
            glTexCoord2f(0.0, 0.0); glVertex3f(base_left1[0], base_left1[1], base_left1[2] - 0.01)
            glTexCoord2f(1.0, 0.0); glVertex3f(base_left2[0], base_left2[1], base_left2[2] - 0.01)
            glTexCoord2f(1.0, 1.0); glVertex3f(ground_left2[0], ground_left2[1], ground_left2[2] - 0.01)
            glTexCoord2f(0.0, 1.0); glVertex3f(ground_left1[0], ground_left1[1], ground_left1[2] - 0.01)
            
            # Cara lateral derecha
            glTexCoord2f(0.0, 0.0); glVertex3f(base_right1[0], base_right1[1], base_right1[2] + 0.01)
            glTexCoord2f(1.0, 0.0); glVertex3f(base_right2[0], base_right2[1], base_right2[2] + 0.01)
            glTexCoord2f(1.0, 1.0); glVertex3f(ground_right2[0], ground_right2[1], ground_right2[2] + 0.01)
            glTexCoord2f(0.0, 1.0); glVertex3f(ground_right1[0], ground_right1[1], ground_right1[2] + 0.01)
            glEnd()
        
        glDisable(GL_TEXTURE_2D)
        
        # Dibujar tapas - SIEMPRE madera.ppm
        self.draw_back_cap(curve_func, z_offset, platform_height)
        self.draw_front_cap(curve_func, z_offset)

    def draw_back_cap(self, curve_func, z_offset=0.0, platform_height=None):
        """Dibujar tapa trasera ALTA con textura de madera"""
        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.wood_texture)  # SIEMPRE madera.ppm
        glColor3f(0.8, 0.6, 0.4)  # Color madera
        
        base_width = 0.7
        
        # Calcular altura de la tapa
        if platform_height is None:
            wall_height = A_METERS[1] + 0.3
        else:
            wall_height = platform_height - 0.3  # Ajustar altura
        
        # Obtener punto inicial de la curva
        left_start, right_start = curve_func(0.0, z_offset=z_offset)
        
        # Calcular vértices de la tapa
        bottom_left = np.array([left_start[0], 0, -base_width/2 - 0.01 + z_offset])
        bottom_right = np.array([right_start[0], 0, base_width/2 + 0.01 + z_offset])
        top_left = np.array([left_start[0], wall_height, -base_width/2 - 0.01 + z_offset])
        top_right = np.array([right_start[0], wall_height, base_width/2 + 0.01 + z_offset])
        
        # Dibujar tapa
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex3f(bottom_left[0], bottom_left[1], bottom_left[2])
        glTexCoord2f(1.0, 0.0); glVertex3f(bottom_right[0], bottom_right[1], bottom_right[2])
        glTexCoord2f(1.0, 1.0); glVertex3f(top_right[0], top_right[1], top_right[2])
        glTexCoord2f(0.0, 1.0); glVertex3f(top_left[0], top_left[1], top_left[2])
        glEnd()
        
        glDisable(GL_TEXTURE_2D)

    def draw_front_cap(self, curve_func, z_offset=0.0):
        """Dibujar tapa delantera con textura de madera"""
        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.wood_texture)  # SIEMPRE madera.ppm
        glColor3f(0.8, 0.6, 0.4)  # Color madera
        
        base_width = 0.7
        wall_height = 0.4  # Altura fija para tapa delantera
        
        # Obtener punto final de la curva
        left_end, right_end = curve_func(1.0, z_offset=z_offset)
        
        # Calcular vértices de la tapa
        bottom_left = np.array([left_end[0], 0, -base_width/2 - 0.01 + z_offset])
        bottom_right = np.array([right_end[0], 0, base_width/2 + 0.01 + z_offset])
        top_left = np.array([left_end[0], wall_height, -base_width/2 - 0.01 + z_offset])
        top_right = np.array([right_end[0], wall_height, base_width/2 + 0.01 + z_offset])
        
        # Dibujar tapa
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex3f(bottom_left[0], bottom_left[1], bottom_left[2])
        glTexCoord2f(1.0, 0.0); glVertex3f(bottom_right[0], bottom_right[1], bottom_right[2])
        glTexCoord2f(1.0, 1.0); glVertex3f(top_right[0], top_right[1], top_right[2])
        glTexCoord2f(0.0, 1.0); glVertex3f(top_left[0], top_left[1], top_left[2])
        glEnd()
        
        glDisable(GL_TEXTURE_2D)

    def render_scene_for_reflection(self, exclude_ball_position=None, balls=None):
        """Renderizar la escena para reflejos (excluyendo bola actual)"""
        self.draw_floor()
        self.draw_platform(A_METERS[0], A_METERS[1] + 0.3)
        self.draw_wall()
        
        # Dibujar bases de las rampas
        platform_height_reflection = A_METERS[1] + 0.3
        self.draw_ramp_base(line_curve_3d, (1.0, 1.0, 0.0), z_offset=-RAMP_SEPARATION, platform_height=platform_height_reflection)
        self.draw_ramp_base(parabolic_curve_3d, (0.0, 0.0, 1.0), z_offset=0.0, platform_height=platform_height_reflection)
        self.draw_ramp_base(cycloid_curve_3d, (1.0, 0.0, 0.0), z_offset=RAMP_SEPARATION, platform_height=platform_height_reflection)
        
        # Dibujar otras bolas (excluyendo la actual si se especifica)
        if balls is not None:
            for ball in balls:
                ball_pos = ball.get_render_position()
                if exclude_ball_position is None or np.linalg.norm(ball_pos - exclude_ball_position) > 0.5:
                    self.draw_ball_for_reflection(ball)

    def draw_ball_for_reflection(self, ball):
        """Dibujar bola para el mapa de reflejos"""
        glPushMatrix()
        render_pos = ball.get_render_position()
        glTranslatef(render_pos[0], render_pos[1], render_pos[2])
        
        # Configurar material para la bola
        mat_ambient = [ball.color[0] * 0.3, ball.color[1] * 0.3, ball.color[2] * 0.3, 1.0]
        mat_diffuse = [ball.color[0] * 0.8, ball.color[1] * 0.8, ball.color[2] * 0.8, 1.0]
        
        glMaterialfv(GL_FRONT, GL_AMBIENT, mat_ambient)
        glMaterialfv(GL_FRONT, GL_DIFFUSE, mat_diffuse)
        
        # Dibujar esfera
        radius = ball.radius
        gluSphere(gluNewQuadric(), radius, 16, 16)
        
        glPopMatrix()

    def draw_ball_3d(self, ball, balls):
        """Versión simple - color con reflejos sutiles"""
        # Actualizar cubemap
        if pygame.time.get_ticks() % 60 == 0:
            ball_position = ball.get_render_position()
            self.reflection_system.render_to_cube_map(
                ball_position, 
                lambda exclude_pos: self.render_scene_for_reflection(exclude_pos, balls)
            )
        
        glPushMatrix()
        ball_position = ball.get_render_position()
        glTranslatef(ball_position[0], ball_position[1], ball_position[2])
        
        # Configurar material CON COLOR
        mat_ambient = [ball.color[0] * 0.5, ball.color[1] * 0.5, ball.color[2] * 0.5, 1.0]
        mat_diffuse = [ball.color[0] * 0.9, ball.color[1] * 0.9, ball.color[2] * 0.9, 1.0]
        mat_specular = [0.3, 0.3, 0.3, 1.0]  # Reflejo moderado
        mat_shininess = [50.0]
        
        glMaterialfv(GL_FRONT, GL_AMBIENT, mat_ambient)
        glMaterialfv(GL_FRONT, GL_DIFFUSE, mat_diffuse)
        glMaterialfv(GL_FRONT, GL_SPECULAR, mat_specular)
        glMaterialfv(GL_FRONT, GL_SHININESS, mat_shininess)
        
        # Establecer color
        glColor3f(ball.color[0], ball.color[1], ball.color[2])
        
        # Habilitar reflejos
        glEnable(GL_TEXTURE_CUBE_MAP)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.reflection_system.cube_map)
        glEnable(GL_TEXTURE_GEN_S)
        glEnable(GL_TEXTURE_GEN_T)
        glEnable(GL_TEXTURE_GEN_R)
        glTexGeni(GL_S, GL_TEXTURE_GEN_MODE, GL_REFLECTION_MAP)
        glTexGeni(GL_T, GL_TEXTURE_GEN_MODE, GL_REFLECTION_MAP)
        glTexGeni(GL_R, GL_TEXTURE_GEN_MODE, GL_REFLECTION_MAP)
        
        # Dibujar esfera
        gluSphere(gluNewQuadric(), ball.radius, 32, 32)
        
        # Limpiar
        glDisable(GL_TEXTURE_GEN_S)
        glDisable(GL_TEXTURE_GEN_T)
        glDisable(GL_TEXTURE_GEN_R)
        glDisable(GL_TEXTURE_CUBE_MAP)
        glPopMatrix()

    def render(self, setup_camera_func, platform_position_x, platform_height, balls, simulation_started, start_time, 
               all_balls_stopped, last_ball_stop_time, font, small_font):
        """Renderizar toda la escena"""
        # Limpiar buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Configurar cámara
        setup_camera_func()
        
        # Renderizar escena 3D
        self.draw_floor()
        self.draw_platform(platform_position_x, platform_height)
        self.draw_wall()
        
        # Dibujar bases de las rampas
        self.draw_ramp_base(line_curve_3d, (1.0, 1.0, 0.0), z_offset=-RAMP_SEPARATION, platform_height=platform_height)
        self.draw_ramp_base(parabolic_curve_3d, (0.0, 0.0, 1.0), z_offset=0.0, platform_height=platform_height)
        self.draw_ramp_base(cycloid_curve_3d, (1.0, 0.0, 0.0), z_offset=RAMP_SEPARATION, platform_height=platform_height)
        
        # Dibujar bolas con reflejos en tiempo real
        for ball in balls:
            self.draw_ball_3d(ball, balls)
        
        # Dibujar panel de información
        self.draw_text_panel(simulation_started, start_time, all_balls_stopped, last_ball_stop_time, balls, font, small_font)

    def draw_text_panel(self, simulation_started, start_time, all_balls_stopped, last_ball_stop_time, balls, font, small_font):
        """Dibujar panel de información superpuesto"""
        # Cambiar a proyección 2D para el panel
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1200, 800, 0)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Configurar para dibujo 2D
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Crear superficie para el panel
        panel_width, panel_height = 400, 200
        info_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        info_surface.fill((50, 50, 70, 230))  # Fondo semitransparente
        
        # Renderizar textos en la superficie
        title_text = font.render("BRAQUISTÓCRONA 3D", True, (255, 255, 100))
        info_surface.blit(title_text, (20, 15))
        
        if simulation_started:
            current_time = (pygame.time.get_ticks() - start_time) / 1000.0
            
            if all_balls_stopped:
                time_text = font.render(f"Tiempo final: {last_ball_stop_time:.2f} s", True, (100, 255, 100))
                info_surface.blit(time_text, (20, 50))
            else:
                time_text = font.render(f"Tiempo: {current_time:.2f} s", True, (255, 255, 255))
                info_surface.blit(time_text, (20, 50))
            
            # Mostrar tiempos de impacto
            impact_y = 85
            impact_title = small_font.render("Primeros impactos:", True, (255, 255, 255))
            info_surface.blit(impact_title, (20, impact_y))
            
            impact_y += 25
            
            for ball in balls:
                if ball.first_impact_time is not None:
                    color_tuple = tuple(min(255, int(c * 300)) for c in ball.color)
                    impact_text = small_font.render(
                        f"{ball.name}: {ball.first_impact_time:.2f} s", 
                        True, color_tuple
                    )
                    info_surface.blit(impact_text, (30, impact_y))
                    impact_y += 22
        else:
            waiting_text = font.render("Presiona ESPACIO (start)", True, (255, 200, 100))
            info_surface.blit(waiting_text, (20, 50))
        
        # Añadir borde al panel
        pygame.draw.rect(info_surface, (120, 120, 170, 255), info_surface.get_rect(), 2)
        
        # Convertir superficie a textura OpenGL
        texture_data = pygame.image.tostring(info_surface, "RGBA", False)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        # Configurar textura
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, panel_width, panel_height, 0, 
                    GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        # Dibujar panel como textura 2D
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(10, 10)
        glTexCoord2f(1, 0); glVertex2f(10 + panel_width, 10)
        glTexCoord2f(1, 1); glVertex2f(10 + panel_width, 10 + panel_height)
        glTexCoord2f(0, 1); glVertex2f(10, 10 + panel_height)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glDeleteTextures([texture_id])
        
        # Restaurar configuración 3D
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()