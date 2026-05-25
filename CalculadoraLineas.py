import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # Necesario para el menú desplegable (Combobox)
import csv
import math
import cmath

# Diccionario global para almacenar los datos de los conductores del CSV
diccionario_conductores = {}

f = 60 # Frecuencia en Hz (puede ajustarse según la región o el sistema específico)
# FUNCIÓN PARA CARGAR EL ARCHIVO CSV AL INICIAR EL PROGRAMA
def cargar_base_datos():
    try:
        with open("conductores.csv", mode="r", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            for fila in lector:
                # Guardamos cada conductor usando su nombre como clave
                diccionario_conductores[fila["Nombre"]] = {
                    "Resistencia": fila["Resistencia"],
                    "GMR": fila["GMR"],
                    "Diametro": fila["Diametro"]
                }
    except FileNotFoundError:
        messagebox.showerror("Error de Archivo", "No se encontró el archivo 'conductores.csv'.\nAsegúrate de crearlo en la misma carpeta.")

def a_polar_str(numero_complejo, unidades=""):
    magnitud = abs(numero_complejo)
    angulo_rad = cmath.phase(numero_complejo)
    angulo_deg = math.degrees(angulo_rad)
    return f"{magnitud:.4f} ∠ {angulo_deg:.2f}° {unidades}"

# FUNCIÓN QUE REACCIONA AL SELECCIONAR UN CONDUCTOR EN EL MENÚ DESPLEGABLE
def al_seleccionar_conductor(event):
    nombre_seleccionado = combo_conductores.get()
    
    # Extraemos los datos del diccionario correspondientes al nombre seleccionado
    datos = diccionario_conductores[nombre_seleccionado]
    
    # Actualizamos los Labels de referencia del lado derecho
    val_resistencia.config(text=f"{datos['Resistencia']} Ω/km")
    val_gmr.config(text=f"{datos['GMR']} m")
    val_diametro.config(text=f"{datos['Diametro']} m")

# FUNCIÓN DE CÁLCULO DE REGULACIÓN
def calcular_regulacion():
    try:
        # Capturamos el texto del Entry y lo convertimos a punto flotante (float)
        voltaje_kv = float(entrada_voltaje.get())
        corriente_a = float(entrada_corriente.get())
        potencia_w = float(entrada_potencia.get())
        longitud_km = float(entrada_longitud.get())

        nombre_cond = combo_conductores.get()
        if not nombre_cond:
            messagebox.showerror("Error de selección", "Por favor, selecciona un conductor primero.")
            return
        if longitud_km > 0 and longitud_km < 80:

            tipo_linea = "Corta: Admitancia en Paralelo Despreciada"
            # Extraemos los datos del conductor seleccionado para el cálculo
            r_unitaria = float(diccionario_conductores[nombre_cond]["Resistencia"])
            gmr_m = float(diccionario_conductores[nombre_cond]["GMR"])
            #Calculamos el voltaje en fase del receptor (V_R) a partir del voltaje de línea (LL)
            v_receptor_fase = (voltaje_kv * 1000) / math.sqrt(3)
            #Voltaje en forma compleja del receptor (V_R) con ángulo de fase 0 (asumiendo carga inductiva)
            V_R = complex(v_receptor_fase, 0)
            voltaje_linea_total = voltaje_kv * 1000
            #Factor de potencia (fp) calculado a partir de la potencia activa (P) y la aparente (S)
            fp = potencia_w / (math.sqrt(3) * voltaje_linea_total * corriente_a)
            #Aseguramos que el factor de potencia no exceda 1.0 para evitar errores en el cálculo del ángulo de fase
            if fp > 1.0: fp = 1.0
            theta = math.acos(fp)
            #Corriente en forma compleja (I_R) con ángulo de fase negativo (asumiendo carga inductiva)
            I_R = corriente_a * complex(math.cos(theta), -math.sin(theta))

            #GMD típico para una torre de 3 conductores por fase (puede ajustarse según el diseño específico de la torre)
            gmd_torre = float(entrada_gmd.get())

            #Cálculo de la resistencia total (R_total) y la reactancia total (X_total) de la línea
            r_total = r_unitaria * longitud_km
            #La inductancia por unidad de longitud (H/km) se calcula usando la fórmula estándar para líneas aéreas, considerando el GMR del conductor y la distancia media geométrica (GMD) entre los conductores en la torre.
            #La fórmula para la inductancia por unidad de longitud es: L' = (2e-7) * ln(GMD/GMR), donde GMD es la distancia media geométrica entre los conductores y GMR es el radio geométrico medio del conductor.
            inductancia_h_km = 2e-7 * math.log(gmd_torre / gmr_m) * 1000 # H/km
            
            #La reactancia total (X_total) se calcula multiplicando la inductancia por unidad de longitud por la frecuencia (60 Hz) y por 2π, y luego por la longitud de la línea en kilómetros.
            x_total = 2 * math.pi * 60 * inductancia_h_km * longitud_km
            
            #La impedancia total de la línea (Z_linea) se representa como un número complejo, donde la parte real es la resistencia total (R_total) y la parte imaginaria es la reactancia total (X_total).
            Z_linea = complex(r_total, x_total)
            
            #Actualizamos la etiqueta de impedancia con el valor calculado en la interfaz gráfica
            val_impedancia.config(text=f"{Z_linea} Ω")

            V_T = V_R + (Z_linea * I_R)

            #La regulación se calcula como el porcentaje de la diferencia entre el voltaje en el generador (V_T) y el voltaje en el receptor (V_R) con respecto al voltaje en el receptor (V_R). Se multiplica por 100 para obtener el resultado en porcentaje.
            regulacion = ((abs(V_T) - abs(V_R)) / abs(V_R)) * 100

            #Actualizamos la etiqueta de resultado con el valor calculado de regulación, formateado a dos decimales y con un color verde para resaltar el resultado positivo.
            etiqueta_resultado.config(text=f"Regulación calculada: {regulacion:.2f} %", fg="green")

            #Imprimimos en la consola el valor de regulación calculada y el voltaje requerido en el generador para referencia adicional.
            print("Regulación calculada: %.2f %%" % regulacion)
            #El voltaje requerido en el generador (V_T) se convierte a kilovoltios de línea (kV de línea) dividiendo su valor absoluto por 1000 y multiplicando por la raíz de 3, ya que estamos trabajando con un sistema trifásico.
            vt_linea_kv = (abs(V_T) * math.sqrt(3)) / 1000
            print(f"Voltaje requerido en el generador: {vt_linea_kv:.2f} kV de línea")

##########################################################################################################################################
        elif longitud_km >= 80 and longitud_km <= 250:
            tipo_linea = "Media: Modelo π nominal"
            
            # Extracción paramétrica
            r_unitaria = float(diccionario_conductores[nombre_cond]["Resistencia"])
            gmr_m = float(diccionario_conductores[nombre_cond]["GMR"])
            diametro_m = float(diccionario_conductores[nombre_cond]["Diametro"])
            radio_m = diametro_m / 2.0
            gmd_torre = float(entrada_gmd.get()) 
            
            omega = 2.0 * math.pi * f
            
            # Impedancia serie total (Z)
            r_total = r_unitaria * longitud_km
            inductancia_h_km = 2e-7 * math.log(gmd_torre / gmr_m) * 1000.0
            x_total = omega * inductancia_h_km * longitud_km
            Z_linea = complex(r_total, x_total)
            
            # Admitancia en derivación total (Y)
            epsilon_0 = 8.8541878128e-12
            capacitancia_f_m = (2.0 * math.pi * epsilon_0) / math.log(gmd_torre / radio_m)
            capacitancia_total = capacitancia_f_m * (longitud_km * 1000.0)
            y_total = omega * capacitancia_total
            Y_linea = complex(0, y_total)
            
            # Constantes Generalizadas de Circuito
            A = 1.0 + (Z_linea * Y_linea) / 2.0
            B = Z_linea
            C = Y_linea * (1.0 + (Z_linea * Y_linea) / 4.0)
            D = A
            
            # Variables nulas para la interfaz (inaplicables en línea media)
            constante_prop = "N/A (Línea Media)"
            Z_c_str = "N/A"
            
            # Fasores de estado en el nodo receptor
            v_receptor_fase = (voltaje_kv * 1000.0) / math.sqrt(3)
            V_R = complex(v_receptor_fase, 0)
            voltaje_linea_total = voltaje_kv * 1000.0
            
            fp = potencia_w / (math.sqrt(3) * voltaje_linea_total * corriente_a)
            if fp > 1.0: fp = 1.0
            theta = math.acos(fp)
            I_R = corriente_a * complex(math.cos(theta), -math.sin(theta))
            
            # Solución de la ecuación de estado lineal
            V_T = (A * V_R) + (B * I_R)
            
            # Regulación de voltaje (Evaluación en vacío)
            V_R_NL = V_T / A
            regulacion = ((abs(V_R_NL) - abs(V_R)) / abs(V_R)) * 100.0
            
            # Actualización de GUI
            val_impedancia.config(text=f"{Z_linea.real:.3f} + {Z_linea.imag:.3f}j Ω")
            etiqueta_resultado.config(text=f"Regulación calculada: {regulacion:.4f} %", fg="green")

        elif longitud_km > 250:
            tipo_linea = "Larga: Modelo de Parámetros Distribuidos"

            # Recuperar los datos del conductor seleccionado desde su CSV
            r_unitaria = float(diccionario_conductores[nombre_cond]["Resistencia"]) # Ω/km
            gmr_m = float(diccionario_conductores[nombre_cond]["GMR"])             # m
            r_externo = float(diccionario_conductores[nombre_cond]["Diametro"]) / 2 # m

            # Parámetros eléctricos unitarios por kilómetro
            gmd_torre = float(entrada_gmd.get())  # Distancia de la torre (metros)
            epsilon_0 = 8.854187e-12
            
            # Impedancia serie unitaria z = r + jx
            inductancia_h_km = 2e-7 * math.log(gmd_torre / gmr_m) * 1000
            x_unitaria = 2 * math.pi * f * inductancia_h_km
            z_unitario = complex(r_unitaria, x_unitaria)

            # Admitancia paralelo unitaria y = 0 + jb
            capacitancia_f_km = (2 * math.pi * epsilon_0) / math.log(gmd_torre / r_externo) * 1000
            b_unitaria = 2 * math.pi * f * capacitancia_f_km
            y_unitario = complex(0, b_unitaria)

            # Constantes distribuidas
            gamma = cmath.sqrt(z_unitario * y_unitario)
            Z_c = cmath.sqrt(z_unitario / y_unitario)

            # Argumento hiperbólico (gamma * l)
            gamma_l = gamma * longitud_km

            constante_prop = f"γl = {gamma_l.real:.4f} + {gamma_l.imag:.4f}j"
            Z_c_str = a_polar_str(Z_c, "Ω")

            # Parámetros ABCD calculados de forma compleja con cmath
            A = cmath.cosh(gamma_l)
            B = Z_c * cmath.sinh(gamma_l)
            C = cmath.sinh(gamma_l) / Z_c
            D = A

            # Procesamiento de fasores de la carga (Plena Carga - Full Load)
            v_receptor_fase = (voltaje_kv * 1000) / math.sqrt(3)
            V_R_FL = complex(v_receptor_fase, 0) # Referencia angular 0°

            voltaje_linea_total = voltaje_kv * 1000
            fp = potencia_w / (math.sqrt(3) * voltaje_linea_total * corriente_a)
            if fp > 1.0: fp = 1.0
            theta = math.acos(fp)
            I_R = corriente_a * complex(math.cos(theta), -math.sin(theta))

            # Cálculo de Voltaje Transmisor (V_S) y Receptor sin carga (V_R_NL)
            V_S = (A * V_R_FL) + (B * I_R)
            V_R_NL = V_S / A

            # Porcentaje de Regulación de Voltaje
            regulacion = ((abs(V_R_NL) - abs(V_R_FL)) / abs(V_R_FL)) * 100

            # Resultados en la interfaz gráfica
            etiqueta_resultado.config(text=f"Regulación calculada: {regulacion:.2f} %", fg="green")

##########################################################################################################################################
        else:
            tipo_linea = "Error: Distancia no válida"
        
        type_linea.config(text=f"Tipo de Línea: {tipo_linea}")
        val_propia.config(text=constante_prop)
        val_zc.config(text=Z_c_str)
        val_param_a.config(text=a_polar_str(A))
        val_param_b.config(text=a_polar_str(B, "Ω"))
        val_param_c.config(text=a_polar_str(C, "S"))

    except ValueError:
        messagebox.showerror("Error de entrada", "Por favor, ingresa solo números válidos.")
    except KeyError:
        messagebox.showerror("Error de selección", "Por favor, selecciona primero un conductor del menú.")

# CONFIGURACIÓN DE LA VENTANA PRINCIPAL
ventana = tk.Tk()
ventana.title("Calculador de Regulación de Líneas - SEP")
ventana.geometry("850x450") 

# Cargar los datos antes de que la interfaz termine de dibujarse
cargar_base_datos()

# ==============================================================================
# COLUMNAS 0 Y 1: PANEL IZQUIERDO (CAPTURA DE DATOS Y ENTRADAS)
# ==============================================================================
tk.Label(ventana, text="Voltaje Receptor (LL) [kV]:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
entrada_voltaje = tk.Entry(ventana)
entrada_voltaje.grid(row=0, column=1, padx=10, pady=10)

tk.Label(ventana, text="Corriente [A]:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
entrada_corriente = tk.Entry(ventana) # Corregida duplicidad
entrada_corriente.grid(row=1, column=1, padx=10, pady=10)

tk.Label(ventana, text="Potencia de carga [W]:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
entrada_potencia = tk.Entry(ventana)
entrada_potencia.grid(row=2, column=1, padx=10, pady=10)

tk.Label(ventana, text="Longitud de Línea [km]:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
entrada_longitud = tk.Entry(ventana)
entrada_longitud.grid(row=3, column=1, padx=10, pady=10)

tk.Label(ventana, text="GMD [m]:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
entrada_gmd = tk.Entry(ventana)
entrada_gmd.grid(row=4, column=1, padx=10, pady=10)


# Botón de Acción y Resultados reacomodados en filas secuenciales (4, 5 y 6)
boton_calcular = tk.Button(ventana, text="Calcular Regulación", command=calcular_regulacion, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
boton_calcular.grid(row=5, column=0, columnspan=2, pady=15)

etiqueta_resultado = tk.Label(ventana, text="Regulación calculada: -- %", font=("Arial", 11, "bold"))
etiqueta_resultado.grid(row=6, column=0, columnspan=2, pady=5)

type_linea = tk.Label(ventana, text="Tipo de Línea: ", font=("Arial", 11, "bold"), fg="blue")
type_linea.grid(row=7, column=0, columnspan=2, pady=5)


# ==============================================================================
# COLUMNAS 3 Y 4: PANEL DERECHO (BASE DE DATOS DE CONDUCTORES)
# ==============================================================================
# Añadimos un espaciado a la izquierda (padx=(50, 10)) en la col 3 para separarlo visualmente
tk.Label(ventana, text=" SELECCIÓN DE CONDUCTOR (ACSR) ", font=("Arial", 11, "bold", "underline")).grid(row=0, column=3, columnspan=2, padx=(50, 10), pady=10)

tk.Label(ventana, text="Conductor:").grid(row=1, column=3, padx=(50, 10), pady=10, sticky="e")

# Creamos el Combobox y lo llenamos con las llaves (nombres) de nuestro diccionario
combo_conductores = ttk.Combobox(ventana, values=list(diccionario_conductores.keys()), state="readonly")
combo_conductores.grid(row=1, column=4, padx=10, pady=10)
# Vinculamos la selección del menú con la función que actualiza las etiquetas de abajo
combo_conductores.bind("<<ComboboxSelected>>", al_seleccionar_conductor)

# Etiquetas fijas de referencia
tk.Label(ventana, text="Resistencia AC (75°C):", font=("Arial", 10, "bold")).grid(row=2, column=3, padx=(50, 10), pady=8, sticky="e")
tk.Label(ventana, text="GMR (Ds):", font=("Arial", 10, "bold")).grid(row=3, column=3, padx=(50, 10), pady=8, sticky="e")
tk.Label(ventana, text="Diámetro Exterior:", font=("Arial", 10, "bold")).grid(row=4, column=3, padx=(50, 10), pady=8, sticky="e")
tk.Label(ventana, text="Impedancia:", font=("Arial", 10, "bold")).grid(row=5, column=3, padx=(50, 10), pady=8, sticky="e")

# Etiquetas dinámicas donde se imprimirán los valores del conductor seleccionado
val_resistencia = tk.Label(ventana, text="-- Ω/km", font=("Arial", 10), fg="purple")
val_resistencia.grid(row=2, column=4, padx=10, pady=8, sticky="w")

val_gmr = tk.Label(ventana, text="-- m", font=("Arial", 10), fg="purple")
val_gmr.grid(row=3, column=4, padx=10, pady=8, sticky="w")

val_diametro = tk.Label(ventana, text="-- m", font=("Arial", 10), fg="purple")
val_diametro.grid(row=4, column=4, padx=10, pady=8, sticky="w")

val_impedancia = tk.Label(ventana, text="-- Ω", font=("Arial", 10), fg="purple")
val_impedancia.grid(row=5, column=4, padx=10, pady=8, sticky="w")

tk.Label(ventana, text=" CONSTANTES GENERALIZADAS DE LA RED ", font=("Arial", 11, "bold", "underline")).grid(row=5, column=3, columnspan=2, padx=(50, 10), pady=(20, 10))

tk.Label(ventana, text="Constante Propia:", font=("Arial", 10, "bold")).grid(row=6, column=3, padx=(50, 10), pady=4, sticky="e")
val_propia = tk.Label(ventana, text="--", font=("Arial", 10), fg="brown")
val_propia.grid(row=6, column=4, padx=10, pady=4, sticky="w")

tk.Label(ventana, text="Impedancia Característica (Zc):", font=("Arial", 10, "bold")).grid(row=7, column=3, padx=(50, 10), pady=4, sticky="e")
val_zc = tk.Label(ventana, text="--", font=("Arial", 10), fg="brown")
val_zc.grid(row=7, column=4, padx=10, pady=4, sticky="w")

tk.Label(ventana, text="Parámetros A y D (Adimensional):", font=("Arial", 10, "bold")).grid(row=8, column=3, padx=(50, 10), pady=4, sticky="e")
val_param_a = tk.Label(ventana, text="--", font=("Arial", 10), fg="brown")
val_param_a.grid(row=8, column=4, padx=10, pady=4, sticky="w")

tk.Label(ventana, text="Parámetro B (Impedancia):", font=("Arial", 10, "bold")).grid(row=9, column=3, padx=(50, 10), pady=4, sticky="e")
val_param_b = tk.Label(ventana, text="--", font=("Arial", 10), fg="brown")
val_param_b.grid(row=9, column=4, padx=10, pady=4, sticky="w")

tk.Label(ventana, text="Parámetro C (Admitancia):", font=("Arial", 10, "bold")).grid(row=10, column=3, padx=(50, 10), pady=4, sticky="e")
val_param_c = tk.Label(ventana, text="--", font=("Arial", 10), fg="brown")
val_param_c.grid(row=10, column=4, padx=10, pady=4, sticky="w")

ventana.mainloop()