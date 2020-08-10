#Universidad del Valle de Guatemala
#Andrea Elias




import struct
import collections


#Estructura de tamanio caracter
def char(c):
	return struct.pack("=c", c.encode('ascii'))
#Estructura de tamanio word
def word(c):
	return struct.pack("=h", c)
#Estructura de tamanio dword
def dword(c):
	return struct.pack("=l", c)
#Asignar un color RGB
def color(r,g,b):
	return bytes([b,g,r])

#Constantes y funciones sobre vectores
V2 = collections.namedtuple('Vertex2',['x','y'])
V3 = collections.namedtuple('Vertex3',['x','y','z'])

def sum(v0, v1):
        return V3(v0.x + v1.x, v0.y + v1.y, v0.z + v1.z)

def sub(v0, v1):
        return V3(v0.x - v1.x, v0.y - v1.y, v0.z - v1.z)

def mul(v0, k):
        return V3(v0.x * k, v0.y * k, v0.z * k)

def dot(v0, v1):
        return v0.x * v1.x + v0.y * v1.y + v0.z * v1.z

def cross(v0, v1):
        return V3(v0.y * v1.z - v0.z * v1.y, v0.z * v1.x - v0.x * v1.z, v0.x * v1.y - v0.y * v1.x)

def length(v0):
        return (v0.x**2 + v0.y**2 + v0.z**2)**0.5
        
def norm(v0):
        l = length(v0)
        if l == 0:
                return V3(0, 0, 0)
        else:
                return V3(v0.x/l, v0.y/l, v0.z/l)

#Se busca la caja mas pequena que contenga un triangulo dados sus vertices
def bbox(A, B, C):
    xs = sorted([int(A.x), int(B.x), int(C.x)])
    ys = sorted([int(A.y), int(B.y), int(C.y)])
    a = V2(int(xs[0]), int(ys[0]))
    b = V2(int(xs[2]), int(ys[2]))    
    return a, b

#Transforma a coordenadas baricentricas los vertices
def barycentric(A, B, C, P):
    cx, cy, cz = cross(V3(B.x - A.x, C.x - A.x, A.x - P.x), V3(B.y - A.y, C.y - A.y, A.y - P.y))

    if cz == 0: #cz no puede ser menor que 1
        return -1, -1, -1

    #Calculamos las coordenadas baricentricas
    u = cx/cz
    v = cy/cz
    w = 1 - (u + v)

    #Regresamos las coordenadas
    return  w, v, u

#Objeto que nos permite darle lectura a un archivo bmp y utilizarlo como textura de un modelo 3D
#Se crea un objeto de textura para Renderizar la textura BMP
class Textura(object):
    def __init__(self, path):
        self.path = path
        self.read()

    #Leemos el archivo bmp y extraemos todos los valores del encabezado y pixeles
    def read(self):
        img = open(self.path, "rb")
        img.seek(2 + 4 + 4)
        header_size = struct.unpack("=l", img.read(4))[0]
        img.seek(2 + 4 + 4 + 4 + 4)
        self.width = struct.unpack("=l", img.read(4))[0]
        self.height = struct.unpack("=l", img.read(4))[0]
        self.pixels = []
        img.seek(header_size)

        #Se hace un recorrido por el alto y ancho de la imagen y se lee el pixel
        for y in range(self.height):
            self.pixels.append([])
            for x in range(self.width):
                b = ord(img.read(1))
                g = ord(img.read(1))
                r = ord(img.read(1))
                self.pixels[y].append(color(r, g, b))

        img.close()

    #Obtenemos los colores de cada pixel del archivo leido
    def get_color(self, tx, ty, intensity=1):
        x = int(tx)
        y = int(ty)
        
        #Devolvemos el color de los bytes que tiene cada pixel de la imagen
        return bytes(
            map(
                lambda b: round(b*intensity) if b * intensity > 0 else 0,
                self.pixels[y][x]
                )
            )

        
#Objeto ArchivoObj para poder dar lectura a un archivo Obj y guardar sus valores de vertices y caras
#Referencia: Basado en ejemplo Dennis Aldana 
class ArchivoObj(object):
    def __init__(self,filename):
        #Se mantiene abierto el archivo hasta leer todas las lineas
        with open(filename) as f:
            self.lines = f.read().splitlines()

        #Se crean los arreglos para guardar las colecciones de vertices y caras del .obj
        self.vertices = []
        self.faces = []
        self.tvertices = []
        #Se da lectura al archivo .obj
        self.lectura()

    #Funcion para eliminar espacios vacios en los datos de las caras si existen
    def eliminarEspacio(self,cara):
        #Se guardan los datos de la cara separados en una lista
        almacenarDatos = cara.split('/')

        #Si hay datos "vacio" almacenados en la lista se eliminan
        if ("") in almacenarDatos:
                almacenarDatos.remove("")

        #Se devuelven los valores de la lista todos convertidos a enteros
        return map(int,almacenarDatos)

    #Funcion que lee cada una de las lineas del .obj extrayendo los valores de vertices y caras
    def lectura(self):
        #Se lee cada una de las lineas guardadas
        for line in self.lines:
            #En caso exista la linea esta se separa en 2 en el primer lugar donde haya un espacio ' ' guardando la primera mitad en prefix y la segunda en value
            if line:
                prefix, value = line.split(' ', 1)

                #Si el prefix es una v es que estamos leyendo los vertices del cual sus coordenadas son mapeados en el value separados por espacios ' '
                if prefix == 'v':
                    self.vertices.append(list(map(float,value.split(' '))))
                if prefix == 'vt':
                    self.tvertices.append(list(map(float,value.split(' '))))
                #Si el prefix es un f es que estamos leyendo una cara de la cual guardaremos una coleccion de datos que nos brindaran los vertices que se usan para formar la cara separados por una diagonal en bloques separados por espacios
                elif prefix == 'f':    
                    self.faces.append([list(self.eliminarEspacio(face)) for face in value.split(' ')])
                    
#Objeto Bitmap para controlar renderizado
class Bitmap(object):
    def __init__(self,width,height):
        self.width = width
        self.height = height
        self.framebuffer = []
        self.zbuffer = []
        self.clearColor = color(0,0,0)
        self.vertexColor = color(255,255,0)
        self.glClear()
        
    #Inicia el bitmap
    def glInit(self):
            pass
        
    #Crea una ventana guardando sus variables de ancho y altura
    def glCreateWindow(self, width, height):
        self.width = width
        self.height = height
        self.glClear()

    #Llena el framebuffer de pixeles de un solo color haciendo un limpiado de imagen
    def glClear(self):
        self.framebuffer = [
            [
                self.clearColor	for x in range(self.width)
                ]
            for y in range(self.height)
            ]
        self.zbuffer = [
            [
                 -1*float('inf') for x in range(self.width)
                 ]
            for y in range(self.height)
            ]
        
    #Cambia el color con que funcionara glClear en formato RGB
    def glClearColor(self,r,g,b):
        try:
                self.rc = round(255*r)
                self.gc = round(255*g)
                self.bc = round(255*b)
                self.clearColor = color(self.rc,self.gc,self.bc)
        except ValueError:
                print("No puede ingresar un numero mayor a 1 ni menor que 0 en el color")

    #Cambia el color de los pixeles que se renderizaran en formato RGB
    def glColor(self,r,g,b):
        try:
                self.rv = round(255*r)
                self.gv = round(255*g)
                self.bv = round(255*b)
                self.vertexColor = color(self.rv,self.gv,self.bv)
        except ValueError:
                print("No puede ingresar un numero mayor a 1 ni menor que 0 en el color")

    #Coloca un Pixel dentro del framebuffer para colocarlo en el renderizado con valores entre -1 y 1
    def glPoint(self,x,y,color):
        #Convertimos los valores entre -1 y 1 a valores enteros de acuerdo a las dimensiones del window
        x = int(round((x+1) * self.width / 2))
        y = int(round((y+1) * self.height / 2))
        try:
                self.framebuffer[y][x] = color
        except IndexError:
                #print("No fue imposible imprimir el punto dado que esta fuera de los limites de la imagen")
                pass
    #Crea una linea formada por la sucesion de puntos equivalentes a pixeles mandando una coordenada x,y inicia y una x,y final, osea 2 pixeles con valores x,y entre -1 y 1
    def glLine(self,x0, y0, x1, y1):
        #Convertimos los valores entre -1 y 1 a valores enteros de acuerdo a las dimensiones del window
        x0 = int(round((x0+1) * self.width / 2))
        y0 = int(round((y0+1) * self.height / 2))
        x1 = int(round((x1+1) * self.width / 2))
        y1 = int(round((y1+1) * self.height / 2))

        #Calulamos las diferencias entre las x y y        
        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

        #Creamos un boolean que nos permita conocer cual es la mayor diferencia
        steep = dy > dx

        #Si dy es mayor a dx entonces intercambiamos cada una de las coordenadas
        if steep:
                x0,y0 = y0,x0
                x1,y1 = y1,x1

        #Si el punto inicial en x es mayor que el final entonces intercambiamos los puntos
        if x0 > x1:
                x0,x1 = x1,x0
                y0,y1 = y1,y0

        #Calculamos nuevamente las diferencias
        dy = abs(y1 - y0)
        dx = abs(x1 - x0)

        #Realizamos el calculo de los puntos que formaran la linea
        offset = 0 * 2 * dx 
        threshold = 0.5 * 2 * dx
        y = y0
        #Ciclo for para rellenar la linea con puntos sucesivos sin dejar espacio
        for x in range(x0, x1 + 1):
                if steep:
                        self.glPoint((float(y)/(float(self.width)/2))-1,(float(x)/(float(self.height)/2))-1,self.vertexColor)
                else:
                        self.glPoint((float(x)/(float(self.width)/2))-1,(float(y)/(float(self.height)/2))-1,self.vertexColor)
                offset += dy
                if offset >= threshold:
                        y += 1 if y0 < y1 else -1
                        threshold += 1 * dx

    #Transformar un vertice a tuple
    def glTransform(self, vertex, translate=(0,0,0), scale=(1,1,1)):
        try:
                return V3(
                        (int(round((vertex[0]+1) * self.width / 2)) + translate[0]) * scale[0],
                        (int(round((vertex[1]+1) * self.height / 2)) + translate[1]) * scale[1],
                        (int(round((vertex[2]+1) * self.width / 2)) + translate[2]) * scale[2])
        except IndexError:
                return V3(
                        (int(round((vertex[0]+1) * self.width / 2)) + translate[0]) * scale[0],
                        (int(round((vertex[1]+1) * self.height / 2)) + translate[1]) * scale[1],
                        (int(round((0.0+1) * self.width / 2)) + translate[2]) * scale[2])
        
    #Transformar un vertice a tuple
    def glTransformT(self, vertex, anchoT, altoT,translate=(0,0,0), scale=(1,1,1)):
        try:
                return V3(
                        (int(round((vertex[0]+1) * anchoT / 2)) + translate[0]) * scale[0],
                        (int(round((vertex[1]+1) * altoT / 2)) + translate[1]) * scale[1],
                        (int(round((vertex[2]+1) * anchoT / 2)) + translate[2]) * scale[2])
        except IndexError:
                return V3(
                        (int(round((vertex[0]+1) * anchoT / 2)) + translate[0]) * scale[0],
                        (int(round((vertex[1]+1) * anchoT / 2)) + translate[1]) * scale[1],
                        (int(round((0.0+1) * anchoT / 2)) + translate[2]) * scale[2])

    #Algorimo para rellenar triangulos se mandan 3 vertices en forma de tupla para rellenar un triangulo
    def glTriangle(self, a, b, c):
        if a.y > b.y:
                a, b = b, a
        if a.y > c.y:
                a, c = c, a
        if b.y > c.y:
                b, c = c, b

        pendientexAC = c.x - a.x
        pendienteyAC = c.y - a.y

        if pendienteyAC == 0:
                return
        
        pendienteInversaAC = pendientexAC/pendienteyAC

        pendientexAB = b.x - a.x
        pendienteyAB = b.y - a.y
        
        if pendienteyAB != 0:
        
                pendienteInversaAB = pendientexAB/pendienteyAB

                for y in range(a.y, b.y + 1):
                        xinicial = round(a.x - pendienteInversaAC * (a.y - y))
                        xfinal = round(a.x - pendienteInversaAB * (a.y - y))

                        if xinicial > xfinal:
                                xinical, xfinal = xfinal, xinicial

                        for x in range(xinicial, xfinal + 1):
                                self.glPoint((float(x)/(float(self.width)/2))-1,(float(y)/(float(self.height)/2))-1,self.vertexColor)

        pendientexBC = c.x - b.x
        pendienteyBC = c.y - b.y

        if pendienteyBC:
                
                pendienteInversaBC = pendientexBC/pendienteyBC

                for y in range(b.y, c.y + 1):
                        xinicial = round(a.x - pendienteInversaAC * (a.y - y))
                        xfinal = round(b.x - pendienteInversaBC * (b.y - y))

                        if xinicial > xfinal:
                                xinical, xfinal = xfinal, xinicial
                        for x in range(xinicial, xfinal + 1):
                                self.glPoint((float(x)/(float(self.width)/2))-1,(float(y)/(float(self.height)/2))-1,self.vertexColor)        

    #Algoritmo para rellenar triangulos
    def triangle(self, A, B, C, color=None, texture=None, texture_coords=(), intensity = 1):
        #Se calculan los valores maximos y minimos de x y y que contienen al triangulo
        bbox_min, bbox_max = bbox(A,B,C)
        #Recorremos a partir de los valores minimos y maximos la caja que contiene al triangulo 
        for x in range(bbox_min.x, bbox_max.x + 1):
                for y in range(bbox_min.y, bbox_max.y +1):
                        #Hacemos el calculo de las coordenadas baricentricas
                        w, v, u = barycentric(A, B, C, V2(x,y))

                        #Se comprueba que los valores de las coordenadas baricentricas no sean menores a cero
                        if w < 0 or v < 0 or u < 0:
                                continue
                        
                        #En caso de haber textura se toma esta como el color del pixel
                        if texture:
                                tA, tB, tC = texture_coords
                                tx = tA.x * w + tB.x * v + tC.x * u
                                ty = tA.y * w + tB.y * v + tC.y * u

                                colorcito = texture.get_color(tx, ty, intensity)
                                self.vertexColor = colorcito
                                
                        #Se calcula la posicion en z del punto a pintar
                        z = A.z * w + B.z * v + C.z * u

                        #Se verifica si se pinta el punto en caso su coordenada en z sea mayor a la anteriormente pintada en el mismo lugar
                        if z > self.zbuffer[y][x]:
                             self.glPoint((float(x)/(float(self.width)/2))-1, (float(y)/(float(self.height)/2))-1,self.vertexColor)
                             self.zbuffer[y][x] = z

                        #Se pinta el punto     
                        #self.glPoint((float(x)/(float(self.width)/2))-1, (float(y)/(float(self.height)/2))-1, self.vertexColor)
                
    #Funcion para cargar un archivo .obj para renderizarlo
    def glLoad(self, filename, textura=None, translate=(10,10,10), scale=(1,1,1)):
        #Se realiza la lectura del archivo .obj
        modelo3D = ArchivoObj(filename)
        modelo3D.lectura()

        luz = V3(0,0.4,1)

        #Se realiza un recorrido de las caras del modelo para conocer su numero de vertices
        for face in modelo3D.faces:
                contadorVertices = len(face)

                #Revisamos que los vertices que conforman una cara sean 3
                if contadorVertices == 3:
                        #Se extraen los valores de los vertices de la cara
                        f1 = face[0][0] - 1
                        f2 = face[1][0] - 1
                        f3 = face[2][0] - 1

                        #Se extraen las coordenadas de los vertices               
                        a = self.glTransform(modelo3D.vertices[f1],translate,scale)
                        b = self.glTransform(modelo3D.vertices[f2],translate,scale)
                        c = self.glTransform(modelo3D.vertices[f3],translate,scale)

                        #Se calcula el vector normal de la cara
                        normal = norm(cross(sub(b,a),sub(c,a)))
                        #Se normalizan los valores de la luz
                        luz = norm(luz)
                        #Se calcula la intensidad de la luz
                        intensity = dot(normal,luz)
                        #print(intensity)

                        #Se revisa que la intensidad no se menor que cero para que no hayan problemas con el color
                        if intensity < 0:
                               continue

                        #En caso de haber una textura se manda a leer los valores de los vertices de la textura en el bmp
                        if textura:
                                #Se extraen los valores de los vertices de la cara de la tetura
                                tv1 = face[0][1] - 1
                                tv2 = face[1][1] - 1
                                tv3 = face[2][1] - 1
                                
                                #Se extraen las coordenadas de los vertices de la textura
                                tvA = self.glTransform(modelo3D.tvertices[tv1],translate,scale)
                                tvB = self.glTransform(modelo3D.tvertices[tv2],translate,scale)
                                tvC = self.glTransform(modelo3D.tvertices[tv3],translate,scale)
                                
                                self.triangle(a,b,c,texture = textura, texture_coords = (tvA, tvB, tvC), intensity = intensity)

                        #En caso de no haber textura solo se rellenan las caras con tonalidades de grises por la intensidad de luz
                        else:
                                self.triangle(a,b,c,color = glColor(intensity, intensity, intensity))

    #Conversion de numero normal a -1 a 1
    def glConvert(self, number, coordenada):
        if coordenada == "x":
                numeroNuevo = (float(number)/((self.width)/2))-1
        elif coordenada =="y":
                numeroNuevo = (float(number)/((self.height)/2))-1
        return float(numeroNuevo)

    #Rellena una figura delimitada por vertices que se unen en el orden que se mandan
    #Basado en Algoritmo Punto en Poligono y modificado para pintar los puntos dentro del poligono
    def glFill(self, poligono):
        #Se recorre cada punto de la imagen por coordenadas x,y con ciclos for
        for y in range(self.height):
                for x in range(self.width): 
                        i = 0
                        j = len(poligono) - 1
                        resultado = False
                        #Se realiza un ciclo que revisa si el punto siempre se encuentra entre los limites de los vertices planteados
                        for i in range(len(poligono)):
                                #Si el poligono se encuentra dentro de los limites la variable resultado esta dentro de los limites obtiene un valor True 
                                if (poligono[i][1] < y and poligono[j][1] >= y) or (poligono[j][1] < y and poligono[i][1] >= y):
                                        if poligono[i][0] + (y - poligono[i][1]) / (poligono[j][1] - poligono[i][1]) * (poligono[j][0] - poligono[i][0]) < x:
                                                resultado = not resultado
                                j = i
                        #Si el resultado es True entonces se pinta el punto 
                        if resultado == True:
                                self.glPoint((float(x)/(float(self.width)/2))-1,(float(y)/(float(self.height)/2))-1,self.vertexColor)
                        else:
                                pass

    #Genera la imagen renderizada en formato bmp recibiendo el nombre de la imagen como imagen.bmp
    def glFinish(self, filename):
        f = open(filename, 'wb')
        #file header 14
        f.write(char('B'))
        f.write(char('M'))
        f.write(dword(54 + self.width * self.height * 3))
        f.write(dword(0))
        f.write(dword(54))

        #image headear 40
        f.write(dword(40))
        f.write(dword(self.width))
        f.write(dword(self.height))
        f.write(word(1))
        f.write(word(24))
        f.write(dword(0))
        f.write(dword(self.width * self.height * 3))
        f.write(dword(0))
        f.write(dword(0))
        f.write(dword(0))
        f.write(dword(0))
        for x in range(self.height):
            for y in range(self.width):
                    self.framebuffer[x][y]
                    f.write(self.framebuffer[x][y])

        f.close()

#Se crea un objeto para manejo de renderizados
objeto = Bitmap(1364,1020)


#Funciones SR2
def glInit():
        objeto = Bitmap(800,600)
        
def glCreateWindow(width,height):
        objeto.glCreateWindow(width,height)
        
def glClear():
        objeto.glClear()

def glClearColor(r,g,b):
        objeto.glClearColor(r,g,b)

#Funcion de linea que recibe coordenadas de un punto inicial y uno final con valores x,y entre -1 y 1
def glLine(x0,y0,x1,y1):
        objeto.glLine(x0,y0,x1,y1)
#Funcion de punto que recibe una coordenada x,y con valores entre -1 y 1
def glPoint(x,y,color):
        objeto.glPoint(x,y,color)
        
def glColor(r,g,b):
        objeto.glColor(r,g,b)

#Funcion para cargar un archivo .obj para ser renderizado con traslado de sus puntos y a cierta escala
def glLoad(filename,textura=None, translate=(5,5,5),scale=(0.5,0.5,0.5)):
        objeto.glLoad(filename,textura=textura,translate=translate,scale=scale)
        
def glFinish(filename):
        objeto.glFinish(filename)

def glConvert(number,coordenada):
        num = objeto.glConvert(number,coordenada)
        return num

#Funcion para pintar un poligono internamente mandandole las coordenadas de los vertices del poligono en el orden en que se unen
def glFill(poligono):
        objeto.glFill(poligono)

def glTransform(a,b,c=10):
        a = objeto.glTransform([a,b,c])
        return a  

def glTriangle(a,b,c):
        objeto.glTriangle(a,b,c)
        
glInit()
glCreateWindow(1000,1000)
glClear()
glColor(0.1,0.1,0.1)
glLoad("Jasmine1.obj")
glFinish("Jasmine.bmp")
