import cv2
import numpy as np
import dlib
import traceback
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.properties import ObjectProperty
from kivy.graphics.texture import Texture
from database import (autenticar_usuario, obtener_descriptor_rostro, obtener_productos, obtener_rol, obtener_usuarios,
                       verificar_rostro, actualizar_datos_db, obtener_conexion_db, crear_cliente)

detector = dlib.get_frontal_face_detector()
try:
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    face_rec_model = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")
    print("Modelos cargados correctamente")
except Exception as e:
    print(f"Error al cargar los modelos: {e}")

def get_face_descriptor(image):
    if len(image.shape) != 3 or image.shape[2] != 3:
        return None

    faces = detector(image)
    if len(faces) == 0:
        return None
    shape = predictor(image, faces[0])
    face_descriptor = face_rec_model.compute_face_descriptor(image, shape)
    return np.array(face_descriptor, dtype=np.float64)

class PantallaLogin(Screen):
    pass


class MenuAdmin(Screen):
    def regresar(self):
        self.manager.current = 'login'

class MenuCliente(Screen):
    def regresar(self):
        self.manager.current = 'login'

    def mostrar_productos(self):
        self.manager.current = 'productos'

    def actualizar_datos_usuario(self):
        pantalla_actualizar = self.manager.get_screen('actualizar_datos')
        
        if pantalla_actualizar:
            pantalla_actualizar.actualizar()
        else:
            self.show_error_popup("Pantalla de actualización de datos no disponible.")

    def show_error_popup(self, message):
        popup = Popup(title='Mensaje',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()


class PantallaProductos(Screen):
    productos_list = ObjectProperty(None)

    def on_enter(self):
        """Llamado cuando la pantalla es activada. Muestra los productos."""
        self.mostrar_productos()

class PantallaProductos(Screen):
    productos_list = ObjectProperty(None)

    def on_enter(self):
        """Llamado cuando la pantalla es activada. Muestra los productos."""
        self.mostrar_productos()

class PantallaProductos(Screen):
    productos_list = ObjectProperty(None)

    def on_enter(self):
        """Llamado cuando la pantalla es activada. Muestra los productos."""
        self.mostrar_productos()

    def mostrar_productos(self):
        try:
            productos = obtener_productos()
            if productos:
                self.productos_list.clear_widgets()
                self.productos_list.add_widget(Label(text='No.', size_hint_y=None, height=40, bold=True))
                self.productos_list.add_widget(Label(text='Nombre', size_hint_y=None, height=40, bold=True))
                self.productos_list.add_widget(Label(text='Precio', size_hint_y=None, height=40, bold=True))
                self.productos_list.add_widget(Label(text='Proveedor', size_hint_y=None, height=40, bold=True))
                
                for idx, producto in enumerate(productos, start=1):
                    self.productos_list.add_widget(Label(text=str(idx), size_hint_y=None, height=40))
                    self.productos_list.add_widget(Label(text=producto['producto_nombre'], size_hint_y=None, height=40))
                    self.productos_list.add_widget(Label(text=str(producto['precio']), size_hint_y=None, height=40))
                    self.productos_list.add_widget(Label(text=producto['proveedor_nombre'], size_hint_y=None, height=40))
            else:
                self.show_error_popup("No hay productos disponibles.")
        except Exception as e:
            self.show_error_popup(f"Error al obtener los productos: {str(e)}")

    def show_error_popup(self, message):
        popup = Popup(title='Mensaje',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()
    
    def regresar(self):
        self.manager.current = 'cliente'

class PantallaActualizarDatos(Screen):
    def on_pre_enter(self, *args):
        self.cargar_datos_usuario()
    
    def cargar_datos_usuario(self):
        app = App.get_running_app()
        if hasattr(app, 'usuario_actual'):
            usuario_actual = app.usuario_actual
            
            if isinstance(usuario_actual, dict):
                email_usuario = usuario_actual.get('email', '')
            else:
                email_usuario = usuario_actual.email

            datos_usuario = obtener_usuarios(email_usuario)
            
            if datos_usuario:
                self.ids.nombre.text = datos_usuario.get('nombre', '')
                self.ids.apellido.text = datos_usuario.get('apellido', '')
                self.ids.email.text = datos_usuario.get('email', '')
                self.ids.telefono.text = datos_usuario.get('telefono', '')
                self.ids.rol.text = datos_usuario.get('rol', '')
                self.ids.password.text = datos_usuario.get('password', '')
            else:
                self.show_error_popup("No se encontraron los datos del usuario.")
        else:
            self.show_error_popup("No se encontró la instancia del usuario actual.")
    
    def actualizar(self):
        nombre = self.ids.nombre.text
        apellido = self.ids.apellido.text
        email = self.ids.email.text
        telefono = self.ids.telefono.text
        rol = self.ids.rol.text
        password = self.ids.password.text
        
        app = App.get_running_app()
        if hasattr(app, 'usuario_actual'):
            usuario_actual = app.usuario_actual
            
            if isinstance(usuario_actual, dict):
                email_usuario = usuario_actual.get('email', '')
            else:
                email_usuario = usuario_actual.email

            if hasattr(self, 'descriptor') and self.descriptor is not None:
                rostro_descriptor = self.descriptor
            else:
                rostro_descriptor = obtener_descriptor_rostro(email_usuario)  

            if email == email_usuario and rostro_descriptor is not None:
                try:
                    actualizar_datos_db(email, nombre, apellido, telefono, rol, password, rostro_descriptor)
                    self.show_success_popup("Datos actualizados correctamente.")

                    if rol == 'administrador':
                        self.manager.current = 'admin'
                    elif rol == 'cliente':
                        self.manager.current = 'cliente'
                    else:
                        self.show_error_popup("Rol de usuario no reconocido.")
                except Exception as e:
                    self.show_error_popup(f"Error al actualizar datos: {str(e)}")
            else:
                self.show_error_popup("No se puede actualizar sin registrar una foto del rostro o el email es incorrecto.")
        else:
            self.show_error_popup("Error: no se encontró la instancia del usuario actual.")

    def show_success_popup(self, message):
        popup = Popup(title='Éxito',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    def show_error_popup(self, message):
        popup = Popup(title='Mensaje',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

class PantallaRegistrarCliente(Screen):
    def registrar_usuario(self, nombre, apellido, email, telefono, password):
        if not nombre or not apellido or not email or not telefono or not password:
            self.show_error_popup("Todos los campos son obligatorios.")
            return

        if hasattr(self, 'descriptor'):
            try:
                crear_cliente(nombre, apellido, email, telefono, 'cliente', password, self.descriptor)
                self.show_success_popup("Registro exitoso.")
                self.redirect_to_login()
            except Exception as e:
                self.show_error_popup(f"Error al registrar usuario: {str(e)}")
        else:
            self.show_error_popup("No se ha capturado ninguna foto del rostro.")

    def tomar_foto(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise ValueError("No se puede acceder a la cámara.")

            while True:
                ret, frame = cap.read()
                if not ret:
                    raise ValueError("Error al capturar la imagen.")

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                cv2.imshow('Captura de Foto', frame)

                if gray_frame is not None and len(gray_frame.shape) == 2 and gray_frame.dtype == np.uint8:
                    faces = detector(gray_frame)
                    for face in faces:
                        x, y, w, h = face.left(), face.top(), face.width(), face.height()
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

                    if len(faces) > 0:
                        descriptor = get_face_descriptor(rgb_frame)
                        if descriptor is not None:
                            verification_result = verificar_rostro(descriptor.tobytes())
                            if verification_result:
                                self.show_error_popup("Rostro ya registrado. Por favor, inicie sesión.")
                                self.redirect_to_login()
                                break
                            else:
                                self.display_photo(frame, descriptor)
                                break

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            print(f"Ocurrió un error: {e}")
            traceback.print_exc()
            self.show_error_popup("No se pudo capturar la foto.")

        finally:
            cap.release()
            cv2.destroyAllWindows()

    def display_photo(self, frame, descriptor):
        frame_rotated = cv2.rotate(frame, cv2.ROTATE_180)
        frame_rgb = cv2.cvtColor(frame_rotated, cv2.COLOR_BGR2RGB)
        height, width, _ = frame_rgb.shape
        texture = Texture.create(size=(width, height), colorfmt='rgb')
        texture.blit_buffer(frame_rgb.tobytes(), bufferfmt='ubyte', colorfmt='rgb')

        image_widget = Image(texture=texture, size_hint=(None, None), size=(400, 400))
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50, pos_hint={'center_x': 0.5})
        accept_button = Button(text="Aceptar", size_hint=(None, None), size=(100, 44), pos_hint={'center_x': 0.5})
        accept_button.bind(on_press=lambda instance: self.accept_photo(descriptor, self.popup))
        retry_button = Button(text="Tomar otra", size_hint=(None, None), size=(100, 44), pos_hint={'center_x': 0.5})
        retry_button.bind(on_press=lambda instance: self.retry_photo(self.popup))
        button_layout.add_widget(accept_button)
        button_layout.add_widget(retry_button)

        popup_content = BoxLayout(orientation='vertical')
        popup_content.add_widget(image_widget)
        popup_content.add_widget(button_layout)

        self.popup = Popup(title='Foto Capturada',
                           content=popup_content,
                           size_hint=(None, None), size=(400, 500),
                           auto_dismiss=False)
        self.popup.open()

    def retry_photo(self, popup):
        popup.dismiss()
        self.tomar_foto()

    def accept_photo(self, descriptor, popup):
        self.descriptor = descriptor
        popup.dismiss()  
        self.show_success_popup("Foto aceptada exitosamente.")

    def show_success_popup(self, message):
        popup = Popup(title='Éxito',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    def show_error_popup(self, message):
        popup = Popup(title='Mensaje',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    def redirect_to_login(self):
        self.manager.current = 'login'  


class AplicacionReconocimientoFacial(App):
    def build(self):
        Builder.load_file('aplicacionreconocimientofacial.kv')
        self.manager_pantallas = ScreenManager()

        self.pantalla_login = PantallaLogin(name='login')
        self.menu_admin = MenuAdmin(name='admin')
        self.menu_cliente = MenuCliente(name='cliente')
        self.pantalla_actualizar_datos = PantallaActualizarDatos(name='actualizar_datos')
        self.pantalla_registrar_cliente = PantallaRegistrarCliente(name='registrar_cliente')

        self.pantalla_productos = PantallaProductos(name='productos')

        self.manager_pantallas.add_widget(self.pantalla_login)
        self.manager_pantallas.add_widget(self.menu_admin)
        self.manager_pantallas.add_widget(self.menu_cliente)
        self.manager_pantallas.add_widget(self.pantalla_actualizar_datos)
        self.manager_pantallas.add_widget(self.pantalla_registrar_cliente)
        self.manager_pantallas.add_widget(self.pantalla_productos)

        return self.manager_pantallas

    def login(self, email, contrasena):
        usuario = autenticar_usuario(email, contrasena)
        if usuario:
            rol = obtener_rol(email)
            self.usuario_actual = usuario

            datos_usuario = obtener_usuarios(email)
            if datos_usuario:
                if rol == 'administrador':
                    self.manager_pantallas.current = 'admin'
                elif rol == 'cliente':
                    if datos_usuario.get('nombre') and datos_usuario.get('apellido') and datos_usuario.get('telefono'):
                        self.manager_pantallas.current = 'cliente'
                    else:
                        self.show_error_popup("Datos erroneos. Ingrese Nuevamente")
                else:
                    self.show_error_popup("Rol de usuario no reconocido")
            else:
                self.show_error_popup("No se encontraron los datos del usuario.")
        else:
            self.show_error_popup("Usuario o contraseña incorrectos")

    def show_error_popup(self, message):
        popup = Popup(title='Mensaje',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    def ingreso_faceid_login(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise ValueError("No se puede acceder a la cámara.")

            while True:
                ret, frame = cap.read()
                if not ret:
                    raise ValueError("Error al capturar la imagen.")

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                cv2.imshow('Ingreso con Face ID', frame)

                if gray_frame is not None and len(gray_frame.shape) == 2 and gray_frame.dtype == np.uint8:
                    faces = detector(gray_frame)
                    for face in faces:
                        x, y, w, h = face.left(), face.top(), face.width(), face.height()
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

                    if len(faces) > 0:
                        descriptor = get_face_descriptor(rgb_frame)
                        if descriptor is not None:
                            user_data = verificar_rostro(descriptor.tobytes())
                            if user_data:
                                self.usuario_actual = user_data
                                if user_data['rol'] == 'administrador':
                                    self.manager_pantallas.current = 'admin'
                                elif user_data['rol'] == 'cliente':
                                    self.manager_pantallas.current = 'cliente'
                                break
                            else:
                                self.show_error_popup("Usuario no reconocido.")
                                break

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            print(f"Ocurrió un error: {e}")
            traceback.print_exc()
            self.show_error_popup("No se pudo iniciar sesión con Face ID.")

        finally:
            cap.release()
            cv2.destroyAllWindows()

if __name__ == '__main__':
    AplicacionReconocimientoFacial().run()