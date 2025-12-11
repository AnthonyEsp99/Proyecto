import numpy as np
from OpenGL.GL import *

def load_ppm_texture(filename):
    """Cargar textura desde archivo PPM"""
    try:
        with open(filename, 'rb') as f:
            header = f.readline().strip()
            if header != b'P6':
                return None
            
            dimensions = f.readline().strip()
            while dimensions.startswith(b'#'):
                dimensions = f.readline().strip()
            
            width, height = map(int, dimensions.split())
            max_val = f.readline().strip()
            data = f.read(width * height * 3)
            
            expected_size = width * height * 3
            if len(data) != expected_size:
                return None
            
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        
        try:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, 
                        GL_RGB, GL_UNSIGNED_BYTE, data)
        except Exception as e:
            try:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, 
                            GL_BGR, GL_UNSIGNED_BYTE, data)
            except Exception as e2:
                return None
        
        return texture_id
        
    except Exception as e:
        return None

def create_improved_wood_texture():
    """Crear textura procedural de madera MEJORADA"""
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    
    width, height = 256, 256
    texture_data = np.zeros((height, width, 3), dtype=np.uint8)
    
    for y in range(height):
        for x in range(width):
            dx = (x - width / 2) * 0.02
            dy = (y - height / 2) * 0.02
            distance = np.sqrt(dx*dx + dy*dy)
            
            base_r = 150 + int(30 * np.sin(distance * 15 + x * 0.1))
            base_g = 100 + int(20 * np.sin(distance * 12 + y * 0.08))
            base_b = 50 + int(15 * np.sin(distance * 10))
            
            grain = np.sin(x * 0.05) * np.cos(y * 0.03) * 25
            noise = np.random.normal(0, 5)
            
            r = max(80, min(200, base_r + grain + noise))
            g = max(50, min(150, base_g + grain * 0.7 + noise * 0.8))
            b = max(20, min(100, base_b + grain * 0.5 + noise * 0.6))
            
            texture_data[y, x] = [r, g, b]
    
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, 
                GL_RGB, GL_UNSIGNED_BYTE, texture_data)
    
    return texture_id

def create_improved_iron_texture():
    """Crear textura procedural de hierro MEJORADA"""
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    
    width, height = 512, 512
    texture_data = np.zeros((height, width, 3), dtype=np.uint8)
    
    for y in range(height):
        for x in range(width):
            base_value = 100 + np.random.normal(0, 8)
            noise1 = np.random.normal(0, 6)
            noise2 = np.random.normal(0, 4)
            
            grain_x = np.sin(x * 0.02) * np.cos(y * 0.015) * 12
            grain_y = np.sin(y * 0.025) * np.cos(x * 0.01) * 10
            
            rust = 0
            if (x * y) % 200 < 15:
                rust = np.random.normal(8, 3)
            
            r = max(70, min(130, base_value + grain_x + noise1 - rust))
            g = max(80, min(140, base_value + grain_y + noise1 * 0.9 - rust * 0.6))
            b = max(90, min(150, base_value + (grain_x + grain_y) * 0.5 + noise2 - rust * 0.4))
            
            metallic = np.sin(x * 0.1 + y * 0.05) * 5
            r = min(150, r + metallic)
            g = min(150, g + metallic)
            b = min(160, b + metallic)
            
            texture_data[y, x] = [int(r), int(g), int(b)]
    
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, 
                GL_RGB, GL_UNSIGNED_BYTE, texture_data)
    glGenerateMipmap(GL_TEXTURE_2D)
    import numpy as np
from OpenGL.GL import *

def load_ppm_texture(filename):
    """Cargar textura desde archivo PPM"""
    try:
        with open(filename, 'rb') as f:
            header = f.readline().strip()
            if header != b'P6':
                return None
            
            dimensions = f.readline().strip()
            while dimensions.startswith(b'#'):
                dimensions = f.readline().strip()
            
            width, height = map(int, dimensions.split())
            max_val = f.readline().strip()
            data = f.read(width * height * 3)
            
            expected_size = width * height * 3
            if len(data) != expected_size:
                return None
            
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        
        try:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, 
                        GL_RGB, GL_UNSIGNED_BYTE, data)
        except Exception as e:
            try:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, 
                            GL_BGR, GL_UNSIGNED_BYTE, data)
            except Exception as e2:
                return None
        
        return texture_id
        
    except Exception as e:
        return None

def create_improved_wood_texture():
    """Crear textura procedural de madera MEJORADA"""
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    
    width, height = 256, 256
    texture_data = np.zeros((height, width, 3), dtype=np.uint8)
    
    for y in range(height):
        for x in range(width):
            dx = (x - width / 2) * 0.02
            dy = (y - height / 2) * 0.02
            distance = np.sqrt(dx*dx + dy*dy)
            
            base_r = 150 + int(30 * np.sin(distance * 15 + x * 0.1))
            base_g = 100 + int(20 * np.sin(distance * 12 + y * 0.08))
            base_b = 50 + int(15 * np.sin(distance * 10))
            
            grain = np.sin(x * 0.05) * np.cos(y * 0.03) * 25
            noise = np.random.normal(0, 5)
            
            r = max(80, min(200, base_r + grain + noise))
            g = max(50, min(150, base_g + grain * 0.7 + noise * 0.8))
            b = max(20, min(100, base_b + grain * 0.5 + noise * 0.6))
            
            texture_data[y, x] = [r, g, b]
    
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, 
                GL_RGB, GL_UNSIGNED_BYTE, texture_data)
    
    return texture_id

def create_improved_iron_texture():
    """Crear textura procedural de hierro MEJORADA"""
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    
    width, height = 512, 512
    texture_data = np.zeros((height, width, 3), dtype=np.uint8)
    
    for y in range(height):
        for x in range(width):
            base_value = 100 + np.random.normal(0, 8)
            noise1 = np.random.normal(0, 6)
            noise2 = np.random.normal(0, 4)
            
            grain_x = np.sin(x * 0.02) * np.cos(y * 0.015) * 12
            grain_y = np.sin(y * 0.025) * np.cos(x * 0.01) * 10
            
            rust = 0
            if (x * y) % 200 < 15:
                rust = np.random.normal(8, 3)
            
            r = max(70, min(130, base_value + grain_x + noise1 - rust))
            g = max(80, min(140, base_value + grain_y + noise1 * 0.9 - rust * 0.6))
            b = max(90, min(150, base_value + (grain_x + grain_y) * 0.5 + noise2 - rust * 0.4))
            
            metallic = np.sin(x * 0.1 + y * 0.05) * 5
            r = min(150, r + metallic)
            g = min(150, g + metallic)
            b = min(160, b + metallic)
            
            texture_data[y, x] = [int(r), int(g), int(b)]
    
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, 
                GL_RGB, GL_UNSIGNED_BYTE, texture_data)
    glGenerateMipmap(GL_TEXTURE_2D)
    
    return texture_id

def seleccionar_textura():
    """Muestra opciones y devuelve diccionario con textura y parámetros"""
    print("\n" + "="*50)
    print("SELECCIÓN DE TEXTURA PARA LAS RAMPAS")
    print("="*50)
    print("(1) Hierro")
    print("(2) Madera")
    print("(3) Plástico")
    print("="*50)
    
    while True:
        try:
            opcion = int(input("Seleccione textura (1-3): "))
            if opcion == 1:
                return {
                    "archivo": "hierro.ppm",
                    "tipo": "Hierro",
                    "friccion": 0.008,
                    "color_base": (0.7, 0.7, 0.8),
                    "reflectividad": 0.8
                }
            elif opcion == 2:
                return {
                    "archivo": "madera2.ppm",  # Cambiado a madera2.ppm para las superficies de las rampas
                    "tipo": "Madera",
                    "friccion": 0.012,
                    "color_base": (0.6, 0.4, 0.2),
                    "reflectividad": 0.3
                }
            elif opcion == 3:
                return {
                    "archivo": "plastico.ppm",
                    "tipo": "Plástico",
                    "friccion": 0.005,
                    "color_base": (0.8, 0.8, 0.9),
                    "reflectividad": 0.6
                }
            else:
                print("Por favor, seleccione 1, 2 o 3")
        except ValueError:
            print("Entrada inválida. Por favor ingrese un número.")
    return texture_id

def seleccionar_textura():
    """Muestra opciones y devuelve diccionario con textura y parámetros"""
    print("\n" + "="*50)
    print("SELECCIÓN DE TEXTURA PARA LAS RAMPAS")
    print("="*50)
    print("(1) Hierro")
    print("(2) Madera")
    print("(3) Plástico")
    print("="*50)
    
    while True:
        try:
            opcion = int(input("Seleccione textura (1-3): "))
            if opcion == 1:
                return {
                    "archivo": "hierro.ppm",
                    "tipo": "Hierro",
                    "friccion": 0.008,
                    "color_base": (0.7, 0.7, 0.8),
                    "reflectividad": 0.8
                }
            elif opcion == 2:
                return {
                    "archivo": "madera.ppm", 
                    "tipo": "Madera",
                    "friccion": 0.012,
                    "color_base": (0.6, 0.4, 0.2),
                    "reflectividad": 0.3
                }
            elif opcion == 3:
                return {
                    "archivo": "plastico.ppm",
                    "tipo": "Plástico",
                    "friccion": 0.005,
                    "color_base": (0.8, 0.8, 0.9),
                    "reflectividad": 0.6
                }
            else:
                print("Por favor, seleccione 1, 2 o 3")
        except ValueError:
            print("Entrada inválida. Por favor ingrese un número.")