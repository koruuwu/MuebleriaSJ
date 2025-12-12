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
    def cai(placeholder="####-####-######-######-######-##"):
        return forms.TextInput(attrs={
            'maxlength': 53,  # incluye guiones, evita crashes por tipeo rápido
            'placeholder': placeholder,
            'style': 'width: 280px;',
            'oninput': """
                // permitir solo números y guiones
                this.value = this.value.replace(/[^0-9-]/g, '');
                
                // remover todos los guiones
                let v = this.value.replace(/-/g, '');
                
                // máximo 44 dígitos del CAI
                if (v.length > 44) v = v.slice(0,44);

                // volver a aplicar formato ####-####-######-######-######-##
                let formatted = '';
                if (v.length > 0) formatted = v.slice(0,4);
                if (v.length > 4) formatted += '-' + v.slice(4,8);
                if (v.length > 8) formatted += '-' + v.slice(8,14);
                if (v.length > 14) formatted += '-' + v.slice(14,20);
                if (v.length > 20) formatted += '-' + v.slice(20,26);
                if (v.length > 26) formatted += '-' + v.slice(26,28);

                this.value = formatted;
            """,

            'onblur': """
                // Validar con expresión regular oficial del CAI
                const regexCAI = /^\\d{4}-\\d{4}-\\d{6}-\\d{6}-\\d{6}-\\d{2}$/;

                if (this.value && !regexCAI.test(this.value)) {
                    this.style.borderColor = '#dc3545';
                    this.style.boxShadow = '0 0 0 0.2rem rgba(220,53,69,.25)';
                } else {
                    this.style.borderColor = '#28a745';
                    this.style.boxShadow = '0 0 0 0.2rem rgba(40,167,69,.25)';
                }
            """,

            'onfocus': """
                this.style.borderColor = '';
                this.style.boxShadow = '';
            """
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
    def cai(placeholder="######-######-######-######-######-##"):
        return forms.TextInput(attrs={
            'maxlength': 39,  # 32 caracteres + 5 guiones + margen por tipeo rápido
            'placeholder': placeholder,
            'style': 'width: 500px; text-transform: uppercase;',  # fuerza visual a mayúsculas

            'oninput': """
                // Convertir a mayúsculas
                this.value = this.value.toUpperCase();

                // Aceptar solo alfanumérico mayúscula y guiones
                this.value = this.value.replace(/[^A-Z0-9-]/g, '');

                // Quitar guiones para formatear
                let v = this.value.replace(/-/g, '');

                // Máximo 32 caracteres reales
                if (v.length > 32) v = v.slice(0, 32);

                // Volver a aplicar formato 6-6-6-6-6-2
                let f = '';
                if (v.length > 0) f = v.slice(0, 6);
                if (v.length > 6) f += '-' + v.slice(6, 12);
                if (v.length > 12) f += '-' + v.slice(12, 18);
                if (v.length > 18) f += '-' + v.slice(18, 24);
                if (v.length > 24) f += '-' + v.slice(24, 30);
                if (v.length > 30) f += '-' + v.slice(30, 32);

                this.value = f;
            """,

            'onblur': """
                // Regex alfanumérico oficial corregido
                const regexCAI = /^[A-Z0-9]{6}-[A-Z0-9]{6}-[A-Z0-9]{6}-[A-Z0-9]{6}-[A-Z0-9]{6}-[A-Z0-9]{2}$/;

                if (this.value && !regexCAI.test(this.value)) {
                    this.style.borderColor = '#dc3545';
                    this.style.boxShadow = '0 0 0 0.2rem rgba(220,53,69,.25)';
                } else {
                    this.style.borderColor = '#28a745';
                    this.style.boxShadow = '0 0 0 0.2rem rgba(40,167,69,.25)';
                }
            """,

            'onfocus': """
                this.style.borderColor = '';
                this.style.boxShadow = '';
            """
        })

    @staticmethod
    def tarjeta(maxim=4, min_len=4, placeholder="Ej: 0001"):
        return forms.TextInput(attrs={
            'style': 'width: 200px;',
            'inputmode': 'numeric',  # Teclado numérico en móviles
            'pattern': r'\d*',      # Solo números
            'placeholder': placeholder,
            'maxlength': maxim,

            # Limitar solo a números y máximo de longitud
            'oninput': f"""
                this.value = this.value.replace(/[^0-9]/g,'');
                if (this.value.length > {maxim}) {{
                    this.value = this.value.slice(0, {maxim});
                }}
            """,

            # Evitar escribir más de la longitud permitida
            'onkeydown': f"""
                if(
                    this.value.length >= {maxim} &&
                    event.key >= '0' && event.key <= '9' &&
                    !event.ctrlKey && !event.metaKey
                ) {{
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
    
    @staticmethod
    def precio_decimal(maxim, allow_zero=False, placeholder="Ej: 199.99"):
        """
        Widget de precio que permite decimales con un solo punto.
        Se formatea visualmente con comas, pero se envía RAW sin formato.
        """
        min_val = 0 if allow_zero else 1

        return forms.TextInput(attrs={
            'style': 'width: 200px;',
            'inputmode': 'decimal',
            'placeholder': placeholder,
            
            'oninput': f"""
                // Guardar posición del cursor
                let cursorPos = this.selectionStart;
                let originalValue = this.value;
                
                // Remover todas las comas para procesar
                let valueWithoutCommas = originalValue.replace(/,/g, '');
                
                // Permitir solo números y un punto
                let cleanValue = valueWithoutCommas.replace(/[^0-9.]/g, '');
                
                // Manejar múltiples puntos - permitir solo uno
                let parts = cleanValue.split('.');
                if (parts.length > 2) {{
                    cleanValue = parts[0] + '.' + parts.slice(1).join('');
                }}
                
                // Limitar parte entera
                let integerPart = parts[0] || '';
                if (integerPart.length > {maxim}) {{
                    integerPart = integerPart.substring(0, {maxim});
                }}
                
                // Manejar parte decimal (máximo 2 dígitos)
                let decimalPart = '';
                if (parts.length > 1) {{
                    decimalPart = parts[1].substring(0, 2); // Máximo 2 decimales
                }}
                
                // Reconstruir cleanValue
                cleanValue = integerPart;
                if (decimalPart) {{
                    cleanValue += '.' + decimalPart;
                }}
                
                // Formatear con comas (solo visual)
                let formattedValue = '';
                if (integerPart) {{
                    // Formatear parte entera con comas
                    let count = 0;
                    for (let i = integerPart.length - 1; i >= 0; i--) {{
                        if (count > 0 && count % 3 === 0) {{
                            formattedValue = ',' + formattedValue;
                        }}
                        formattedValue = integerPart[i] + formattedValue;
                        count++;
                    }}
                    
                    // Agregar parte decimal si existe
                    if (decimalPart) {{
                        formattedValue += '.' + decimalPart;
                    }}
                }}
                
                // Guardar valor sin formato en atributo data
                this.setAttribute('data-raw-value', cleanValue);
                
                // Actualizar el valor visual
                this.value = formattedValue;
                
                // Ajustar posición del cursor después de agregar comas
                if (formattedValue !== originalValue) {{
                    // Contar comas añadidas antes de la posición original del cursor
                    let commasAdded = 0;
                    let valueBeforeCursor = originalValue.substring(0, cursorPos);
                    let cleanBeforeCursor = valueBeforeCursor.replace(/,/g, '');
                    let newFormattedBeforeCursor = formattedValue.substring(0, cursorPos + commasAdded);
                    let newCleanBeforeCursor = newFormattedBeforeCursor.replace(/,/g, '');
                    
                    // Ajustar cursor basado en la diferencia
                    while (newCleanBeforeCursor.length > cleanBeforeCursor.length) {{
                        commasAdded++;
                        newFormattedBeforeCursor = formattedValue.substring(0, cursorPos + commasAdded);
                        newCleanBeforeCursor = newFormattedBeforeCursor.replace(/,/g, '');
                    }}
                    
                    this.setSelectionRange(cursorPos + commasAdded, cursorPos + commasAdded);
                }}
            """,
            
            'onblur': """
                // Al perder foco, mostrar sin formato (pero con punto decimal si existe)
                const raw = this.getAttribute('data-raw-value');
                if (raw !== null && raw !== '') {
                    this.value = raw;
                } else if (this.value) {
                    // Si no hay raw value, limpiar comas
                    this.value = this.value.replace(/,/g, '');
                }
            """,
            
            'onfocus': """
                // Al hacer foco, formatear con comas
                let currentValue = this.value;
                if (currentValue) {
                    // Remover comas existentes
                    let cleanValue = currentValue.replace(/,/g, '');
                    
                    // Guardar valor limpio
                    this.setAttribute('data-raw-value', cleanValue);
                    
                    // Formatear con comas
                    let parts = cleanValue.split('.');
                    let integerPart = parts[0] || '';
                    let decimalPart = parts[1] || '';
                    
                    if (integerPart) {
                        let formattedInt = '';
                        for (let i = integerPart.length - 1, count = 0; i >= 0; i--) {
                            if (count > 0 && count % 3 === 0) {
                                formattedInt = ',' + formattedInt;
                            }
                            formattedInt = integerPart[i] + formattedInt;
                            count++;
                        }
                        
                        // Reconstruir valor formateado
                        let formattedValue = formattedInt;
                        if (decimalPart) {
                            formattedValue += '.' + decimalPart;
                        }
                        
                        this.value = formattedValue;
                    }
                }
            """,
            
            'onkeydown': """
                // Permitir navegación con teclas incluso cuando hay comas
                const allowedKeys = [
                    'Backspace', 'Delete', 'Tab', 'Escape', 'Enter',
                    'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
                    'Home', 'End'
                ];
                
                if (allowedKeys.includes(event.key)) {
                    return true;
                }
                
                // Permitir punto decimal
                if (event.key === '.' && !this.value.includes('.')) {
                    return true;
                }
                
                // Permitir solo números
                if (event.key.length === 1 && /[0-9]/.test(event.key)) {
                    return true;
                }
                
                event.preventDefault();
                return false;
            """
        })
    
    @staticmethod
    def rtn(placeholder="####-####-######"):
        return forms.TextInput(attrs={
            'maxlength': 16,  # 14 dígitos + 2 guiones
            'placeholder': placeholder,
            'style': 'width: 300px;',

            'oninput': """
                // Solo permitir números
                this.value = this.value.replace(/[^0-9]/g, '');

                // Máximo 14 dígitos reales
                if (this.value.length > 14) this.value = this.value.slice(0, 14);

                // Aplicar formato ####-####-######
                let v = this.value;
                let formatted = '';
                if (v.length > 0) formatted = v.slice(0, 4);
                if (v.length > 4) formatted += '-' + v.slice(4, 8);
                if (v.length > 8) formatted += '-' + v.slice(8, 14);
                this.value = formatted;
            """,

            'onblur': """
                // Validación de formato exacto
                const regexRTN = /^\\d{4}-\\d{4}-\\d{6}$/;

                if (this.value && !regexRTN.test(this.value)) {
                    this.style.borderColor = '#dc3545';
                    this.style.boxShadow = '0 0 0 0.2rem rgba(220,53,69,.25)';
                } else if (this.value) {
                    this.style.borderColor = '#28a745';
                    this.style.boxShadow = '0 0 0 0.2rem rgba(40,167,69,.25)';
                }
            """,

            'onfocus': """
                this.style.borderColor = '';
                this.style.boxShadow = '';
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
    
