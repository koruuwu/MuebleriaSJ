# proyecto/validators.py
import re
from django import forms
from django.core.exceptions import ValidationError

class ValidacionesBaseForm(forms.ModelForm):
    """
    Clase base unificada para validaciones comunes en formularios Django.
    Incluye:
    - Validaciones de letras, dobles espacios y letras repetidas.
    - Validaciones de longitud de campos.
    - Validaciones de números de teléfono (inicio permitido y longitud mínima).
    - Otros métodos de validación que quieras reutilizar.
    """

    # ------------------- MÉTODOS DE VALIDACIÓN -------------------
    def full_clean(self):
        """
        Sobrescribe full_clean para manejar el mensaje genérico en español
        """
        try:
            return super().full_clean()
        except ValidationError as e:
            # Si es un error de formulario completo, personalizar el mensaje
            if not hasattr(e, 'error_dict') and hasattr(e, 'message'):
                if e.message == "Please correct the errors below.":
                    raise ValidationError("Por favor, corrija los errores a continuación.")
            raise e
        
    def validar_campo_texto(self, valor, nombre_visible, min_len=1, max_len=100):
        """
        Aplica todas las validaciones estándar del sistema:
        - Longitud mínima y máxima
        - No dobles espacios
        - No letras repetidas
        """
        valor = valor.strip()
        valor = self.validar_longitud(valor, nombre_visible, min_len=min_len, max_len=max_len)
        valor = self.validar_dobles_espacios(valor, nombre_visible)
        valor = self.validar_letras_repetidas(valor, nombre_visible)
        return valor
    

    def validar_dobles_espacios(self, valor, nombre_campo):
        if '  ' in valor:
            raise ValidationError(f"No se permiten dobles espacios en {nombre_campo}.")
        return valor

    def validar_letras_repetidas(self, valor, nombre_campo, max_repeticiones=2):
        """Evita más de 'max_repeticiones' letras iguales seguidas."""
        if re.search(rf'(.)\1{{{max_repeticiones},}}', valor):
            raise ValidationError(f"No se permiten más de {max_repeticiones} letras iguales seguidas en {nombre_campo}.")
        return valor

    def validar_longitud(self, valor, nombre_campo, min_len=None, max_len=None):
        if min_len and len(valor) < min_len:
            raise ValidationError(f"{nombre_campo} debe tener al menos {min_len} caracteres.")
        if max_len and len(valor) > max_len:
            raise ValidationError(f"{nombre_campo} no puede superar los {max_len} caracteres.")
        return valor

    def validar_numero_inicio(self, valor, nombre_campo, primeros_permitidos):
        if len(valor) > 0 and valor[0] not in primeros_permitidos:
            raise ValidationError(f"{nombre_campo} debe iniciar con {'/'.join(primeros_permitidos)}.")
        return valor
    
    def validar_precio(self, valor, nombre_campo="El precio", min_val=0.01, max_val=999999):
        """
        Valida precios con:
        - Solo números y un punto opcional
        - Máximo dos decimales
        - Rango configurado
        """
        valor = str(valor).strip()

        # No debe estar vacío
        if not valor:
            raise ValidationError(f"{nombre_campo} no puede estar vacío.")

        # Validar patrón: números + opcional punto + 1 o 2 decimales
        if not re.match(r'^\d+(\.\d{1,2})?$', valor):
            raise ValidationError(f"{nombre_campo} debe ser un número válido.")

        # Convertir a float
        try:
            precio = float(valor)
        except:
            raise ValidationError(f"{nombre_campo} no es un número válido.")

        # Validar rango
        if precio < min_val:
            raise ValidationError(f"{nombre_campo} debe ser mayor o igual a {min_val}.")
        if precio > max_val:
            raise ValidationError(f"{nombre_campo} no puede superar {max_val}.")

        return precio
    # ------------------- CLEAN PREDEFINIDOS -------------------
   
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        return self.validar_campo_texto(nombre, "El nombre", min_len=10, max_len=50)#--importante usa validador para tipo de dato general
    #validar campo reune los metodos para validacion de nombres-sofia castro


    #def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        nombre = self.validar_longitud(nombre, "El nombre", min_len=10, max_len=50)
        nombre = self.validar_dobles_espacios(nombre, "El nombre")
        nombre = self.validar_letras_repetidas(nombre, "El nombre")
        return nombre#

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion', '').strip()
        direccion = self.validar_longitud(direccion, "La dirección", min_len=10, max_len=100)
        direccion = self.validar_dobles_espacios(direccion, "La dirección")
        direccion = self.validar_letras_repetidas(direccion, "La dirección")
        return direccion

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').replace('-', '')
        telefono = self.validar_longitud(telefono, "El teléfono", min_len=8)
        telefono = self.validar_numero_inicio(telefono, "El teléfono", ['2','3','7','8','9'])
        return telefono
    def clean_precio_base(self):
        valor = self.cleaned_data.get("precio_base")
        return self.validar_precio(valor, "El precio")



    
    def clean_stock_minimo(self):
        numero = self.cleaned_data.get('stock_minimo')
        numero = self.validar_longitud(str(numero), "Stock minimo", min_len=1, max_len=4)
        return numero
    
    def clean_stock_maximo(self):
        numero = self.cleaned_data.get('stock_maximo')
        numero = self.validar_longitud(str(numero), "Stock maximo", min_len=1, max_len=5)
        return numero


    # ------------------- MÉTODOS ADICIONALES -------------------
    # otros métodos de validación comunes
    # como validar emails, números de documentos, etc.
