from django import forms

class WidgetsRegulares:

    @staticmethod
    def nombre(placeholder="Ej: Lusiana Pérez"):
        return forms.TextInput(attrs={
            'maxlength': 50,
            'onkeypress': """
                const val = event.target.value;
                const key = event.key;
                if (!/[a-zA-Z\\sáéíóúÁÉÍÓÚñÑ]/.test(key)) return false;
                if (val.length >= 2 && val.slice(-2) === key.repeat(2)) return false;
                return true;
            """,
            'oninput': "this.value = this.value.replace(/\\s{2,}/g, ' ');",
            'placeholder': placeholder,
        })

    @staticmethod
    def direccion(placeholder="Ej: Col. Miraflores, Tegucigalpa, Bloque A, 2032"):
        return forms.TextInput(attrs={
            'maxlength': 150,
            'onkeypress': """
                const val = event.target.value;
                const key = event.key;
                if (!/[a-zA-Z\\sáéíóúÁÉÍÓÚñÑ]/.test(key)) return false;
                if (val.length >= 2 && val.slice(-2) === key.repeat(2)) return false;
                return true;
            """,
            'oninput': "this.value = this.value.replace(/\\s{2,}/g, ' ');",
            'placeholder': placeholder,
        })

    @staticmethod
    def telefono(placeholder="Ej: 9876-5432"):
        return forms.TextInput(attrs={
            'onkeypress': """
                const val = event.target.value;
                const key = event.key;
                if (!/[0-9]/.test(key)) return false;
                if (val.length === 0 && !/[23789]/.test(key)) return false;
                return true;
            """,
            'oninput': """
                this.value = this.value.replace(/[^0-9]/g, '');
                if (this.value.length > 4)
                    this.value = this.value.substring(0,4) + '-' + this.value.substring(4,8);
            """,
            'placeholder': placeholder,
        })
