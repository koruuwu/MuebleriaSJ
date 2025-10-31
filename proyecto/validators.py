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


    def validar_dobles_espacios(self, valor, nombre_campo):
        if '  ' in valor:
            raise ValidationError(f"⚠️ No se permiten dobles espacios en {nombre_campo}.")
        return valor

    def validar_letras_repetidas(self, valor, nombre_campo, max_repeticiones=2):
        """Evita más de 'max_repeticiones' letras iguales seguidas."""
        if re.search(rf'(.)\1{{{max_repeticiones},}}', valor):
            raise ValidationError(f"⚠️ No se permiten más de {max_repeticiones} letras iguales seguidas en {nombre_campo}.")
        return valor

    def validar_longitud(self, valor, nombre_campo, min_len=None, max_len=None):
        if min_len and len(valor) < min_len:
            raise ValidationError(f"⚠️ {nombre_campo} debe tener al menos {min_len} caracteres.")
        if max_len and len(valor) > max_len:
            raise ValidationError(f"⚠️ {nombre_campo} no puede superar los {max_len} caracteres.")
        return valor

    def validar_numero_inicio(self, valor, nombre_campo, primeros_permitidos):
        if len(valor) > 0 and valor[0] not in primeros_permitidos:
            raise ValidationError(f"⚠️ {nombre_campo} debe iniciar con {'/'.join(primeros_permitidos)}.")
        return valor

    # ------------------- CLEAN PREDEFINIDOS -------------------

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        nombre = self.validar_longitud(nombre, "El nombre", min_len=10, max_len=50)
        nombre = self.validar_dobles_espacios(nombre, "El nombre")
        nombre = self.validar_letras_repetidas(nombre, "El nombre")
        return nombre

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

    # ------------------- MÉTODOS ADICIONALES -------------------
    # Puedes agregar aquí otros métodos de validación comunes
    # como validar emails, números de documentos, etc.
