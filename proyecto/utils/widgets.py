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
                if (!/[a-zA-Z\\sáéíóúÁÉÍÓÚñÑ\\,\\.]/.test(key)) return false;
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
    def email(placeholder="Ej: usuario@correo.com"):
        """
        Widget para campos de email con validación en tiempo real.
        - No permite espacios
        - Valida formato básico de email
        - Elimina espacios automáticamente
        """
        return forms.TextInput(attrs={
            'maxlength': 50,  # Longitud máxima estándar para emails
            'onkeypress': """
                // Prevenir espacios en tiempo real
                if (event.key === ' ') {
                    event.preventDefault();
                    return false;
                }
                return true;
            """,
            'oninput': """
                // Eliminar todos los espacios y validar formato básico
                let input = event.target;
                let value = input.value;
                
                // Eliminar espacios
                value = value.replace(/\\s/g, '');
                input.value = value;
                
                // Validación visual del formato email
                const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
                if (value && !emailRegex.test(value)) {
                    input.style.borderColor = '#dc3545';
                    input.style.boxShadow = '0 0 0 0.2rem rgba(220, 53, 69, 0.25)';
                } else {
                    input.style.borderColor = '';
                    input.style.boxShadow = '';
                }
            """,
            'onblur': """
                // Validación más estricta al perder el foco
                const input = event.target;
                const value = input.value.trim();
                
                // Patrón más específico para emails
                const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\\.[a-zA-Z0-9-]+)*$/;
                
                if (value && !emailRegex.test(value)) {
                    input.style.borderColor = '#dc3545';
                    input.style.boxShadow = '0 0 0 0.2rem rgba(220, 53, 69, 0.25)';
                    
                    // Mostrar mensaje de error temporal
                    let errorMsg = input.nextElementSibling;
                    if (!errorMsg || !errorMsg.classList.contains('email-error-msg')) {
                        errorMsg = document.createElement('div');
                        errorMsg.className = 'email-error-msg text-danger small mt-1';
                        input.parentNode.appendChild(errorMsg);
                    }
                    errorMsg.textContent = 'Por favor ingrese un correo electrónico válido';
                } else {
                    input.style.borderColor = '#28a745';
                    input.style.boxShadow = '0 0 0 0.2rem rgba(40, 167, 69, 0.25)';
                    
                    // Eliminar mensaje de error si existe
                    const errorMsg = input.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('email-error-msg')) {
                        errorMsg.remove();
                    }
                }
            """,
            'onfocus': """
                // Limpiar estilos al enfocar
                const input = event.target;
                input.style.borderColor = '';
                input.style.boxShadow = '';
                
                // Eliminar mensaje de error si existe
                const errorMsg = input.nextElementSibling;
                if (errorMsg && errorMsg.classList.contains('email-error-msg')) {
                    errorMsg.remove();
                }
            """,
            'placeholder': placeholder,
            'autocomplete': 'email',
            'class': 'email-widget'
        })
    


    @staticmethod
    def numero(maxim, allow_zero=False, placeholder="Ej: 1"):
        if allow_zero:
            min_val = 0
        else:
            min_val = 1
        max_val = 10**maxim - 1

        return forms.TextInput(attrs={
            #size': maxim'''
            'style':'width: 200px;',
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
    @staticmethod
    def precio(maxim, allow_zero=False, placeholder="Ej: 199.99"):
        min_val = 0 if allow_zero else 1
        max_val = 10**maxim - 1

        return forms.TextInput(attrs={
            'style':'width: 200px;',
            'inputmode': 'decimal',
            'placeholder': placeholder,
            'oninput': """
                let raw = this.value.replace(/[^0-9]/g, '');
                
                // No permitir empezar con cero si tiene más de 1 dígito
                if (raw.length > 1 && raw.startsWith('0')) {
                    raw = raw.substring(1);
                }
                
                // Limitar longitud máxima
                if (raw.length > %d) {
                    raw = raw.substring(0, %d);
                }
                
                // Formatear con comas (solo visual)
                let formatted = '';
                for (let i = raw.length - 1, count = 0; i >= 0; i--) {
                    if (count > 0 && count %% 3 === 0) {
                        formatted = ',' + formatted;
                    }
                    formatted = raw[i] + formatted;
                    count++;
                }
                
                // Guardar el valor sin formato en un campo oculto o data attribute
                this.setAttribute('data-raw-value', raw);
                this.value = formatted;
            """ % (maxim, maxim),
            'onblur': """
                // Al salir del campo, restaurar el valor sin formato para el envío
                const raw = this.getAttribute('data-raw-value');
                if (raw) {
                    this.value = raw;
                }
            """,
            'onfocus': """
                // Al entrar al campo, formatear visualmente otra vez
                const raw = this.value.replace(/[^0-9]/g, '');
                if (raw) {
                    let formatted = '';
                    for (let i = raw.length - 1, count = 0; i >= 0; i--) {
                        if (count > 0 && count %% 3 === 0) {
                            formatted = ',' + formatted;
                        }
                        formatted = raw[i] + formatted;
                        count++;
                    }
                    this.setAttribute('data-raw-value', raw);
                    this.value = formatted;
                }
            """
        })
    
class WidgetsEspeciales:
    @staticmethod
    def nombreSucursal(placeholder="Ej: Mueblería San José - Germania"):
        return forms.TextInput(attrs={
            'maxlength': 50,
            'onkeypress': """
                const val = event.target.value;
                const key = event.key;
                if (!/[a-zA-Z\\sáéíóúÁÉÍÓÚñÑ\\-]/.test(key)) return false;
                if (val.length >= 2 && val.slice(-2) === key.repeat(2)) return false;
                return true;
            """,
            'oninput': "this.value = this.value.replace(/\\s{2,}/g, ' ');",
            'placeholder': placeholder,
        })