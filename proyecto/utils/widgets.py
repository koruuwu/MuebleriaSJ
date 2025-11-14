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
    
    #---AGREGAR CAMBIO NO ESPECIFICAR MAX LENGHT PARA VALORES DE PALABRAS, HACERLO DESDE MODEL-sofia castro
    @staticmethod
    def comentario(placeholder="Ej: Madera de mala calidad, entrega rapida"):
        return forms.Textarea(attrs={
            'rows': 4,  # cantidad de líneas visibles
            'cols': 40, # ancho del área
            'maxlength': 150, 
            'onkeypress': """
                const val = event.target.value;
                const key = event.key;
                if (!/[a-zA-Z\\sáéíóúÁÉÍÓÚñÑ,]/.test(key)) return false;
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


    @staticmethod
    def numero(maxim, allow_zero=False, placeholder="Ej: 1"):
        if allow_zero:
            min_val = 0
        else:
            min_val = 1
        max_val = 10**maxim - 1

        return forms.TextInput(attrs={
            'inputmode': 'numeric',
            'pattern': r'\d*',
            'placeholder': placeholder,
            'oninput': f"""
                this.value = this.value.replace(/[^0-9]/g,'');
                if(this.value !== '') {{
                    // Primero limitar la longitud máxima
                    if(this.value.length > {maxim}) {{
                        this.value = this.value.slice(0,{maxim});
                    }}
                    
                    // Luego validar el valor numérico
                    let val = parseInt(this.value);
                    if(val < {min_val}) {{
                        this.value = '{min_val}';
                    }} else if(val > {max_val}) {{
                        this.value = '{max_val}';
                    }}
                }}
            """,
            'onkeydown': f"""
                // Prevenir que se escriban más dígitos si ya se alcanzó el máximo
                if(this.value.length >= {maxim} && 
                event.key >= '0' && event.key <= '9' && 
                !event.ctrlKey && !event.metaKey && 
                !event.altKey) {{
                    event.preventDefault();
                }}
            """
        })



    @staticmethod
    def abreviatura(max_length=5, placeholder="Ej: ABC"):
        """
        Widget para abreviaturas o descripciones cortas.
        """
        return forms.TextInput(attrs={
            'maxlength': str(max_length),
            'placeholder': placeholder,
            'oninput': f"if(this.value.length > {max_length}) this.value = this.value.slice(0,{max_length});"
        })