import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde, ks_2samp, chi2_contingency
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from scipy.stats import spearmanr
import seaborn as sns
from sklearn.decomposition import PCA
from scipy.linalg import cholesky
from sklearn.linear_model import LinearRegression
from scipy.stats import norm


def generar_datos_monte_carlo(
    csv_path, n_samples=1000, output_path="datos_sinteticos.csv"
):
    """
    Genera datos sintéticos para el entrenamiento de redes neuronales de estimación de tiempos
    en proyectos de software mediante un enfoque de Monte Carlo mejorado.
    
    Esta función implementa un pipeline completo y optimizado para la generación de datos
    sintéticos de alta calidad que preservan las distribuciones estadísticas y correlaciones
    de los datos originales, utilizando técnicas avanzadas de análisis y simulación.
    
    Args:
        csv_path (str): Ruta al archivo CSV con datos reales
        n_samples (int): Número de muestras sintéticas a generar
        output_path (str): Ruta donde guardar el archivo CSV con datos sintéticos
        
    Returns:
        pd.DataFrame: DataFrame con los datos sintéticos generados
    """
    # 1. PREPROCESADO Y CARGA DE DATOS
    df, numeric_cols, categorical_cols = _cargar_y_preprocesar_datos(csv_path)
    
    # 2. ANÁLISIS ESTADÍSTICO DE DATOS ORIGINALES
    analisis_estadistico = _analizar_datos_originales(df, numeric_cols, categorical_cols)
    
    # 3. GENERACIÓN DE DATOS SINTÉTICOS
    synthetic_data = _generar_datos_sinteticos(
        df, 
        n_samples, 
        analisis_estadistico["numeric_cols"],
        analisis_estadistico["categorical_cols"],
        analisis_estadistico["cat_distributions"],
        analisis_estadistico["kdes"],
        analisis_estadistico["conditional_distributions"],
        analisis_estadistico["encoders"],
        analisis_estadistico["corr_matrix"],
        analisis_estadistico["tamanos_reales"],
        analisis_estadistico["dist_real_recursos"],
        analisis_estadistico["correlaciones_criticas"]
    )
    
    # 4. VALIDACIÓN Y ANÁLISIS DE RESULTADOS
    synthetic_df = _validar_y_ajustar_datos(
        df, 
        synthetic_data, 
        analisis_estadistico["numeric_cols"],
        analisis_estadistico["categorical_cols"],
        analisis_estadistico["correlaciones_criticas"],
        analisis_estadistico["tamanos_reales"]
    )
    
    # 5. GUARDAR RESULTADOS
    if output_path:
        synthetic_df.to_csv(output_path, index=False)
        print(f"Datos sintéticos guardados en {output_path}")
    
    return synthetic_df

def _cargar_y_preprocesar_datos(csv_path):
    """
    Carga y preprocesa los datos de entrada, realizando limpieza y normalización básica.
    
    Args:
        csv_path (str): Ruta al archivo CSV con datos reales
        
    Returns:
        tuple: DataFrame con datos preprocesados y listas de columnas numéricas y categóricas
    """
    print("\n=== CARGANDO Y PREPROCESANDO DATOS ===")
    
    # Cargar datos con detección automática de codificación
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='latin-1')
        print("  Nota: Se utilizó codificación latin-1 para cargar el archivo")
    
    print(f"  Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas")
    
    # Corregir nombres de columnas con problemas de codificación
    if "TamaÃ±o_Tarea" in df.columns:
        df.rename(columns={"TamaÃ±o_Tarea": "Tamaño_Tarea"}, inplace=True)
        print("  Corregida codificación de la columna 'Tamaño_Tarea'")
    
    # Identificar variables numéricas y categóricas para preservar correlaciones
    numeric_cols = [
        "Tiempo_Ejecucion",
        "Complejidad",
        "Tamaño_Tarea",
        "Carga_Trabajo_R1",
        "Experiencia_R1",
        "Experiencia_Equipo",
        "Claridad_Requisitos",
    ]

    categorical_cols = ["Tipo_Tarea", "Fase_Tarea", "Cantidad_Recursos"]
    
    # Verificar columnas disponibles
    missing_cols = [col for col in numeric_cols + categorical_cols if col not in df.columns]
    if missing_cols:
        print(f"  Advertencia: No se encontraron las columnas: {', '.join(missing_cols)}")
        # Filtrar solo columnas existentes
        numeric_cols = [col for col in numeric_cols if col in df.columns]
        categorical_cols = [col for col in categorical_cols if col in df.columns]
    
    # Eliminar outliers para mejorar la calidad del KDE
    df_clean = eliminar_outliers(df, numeric_cols, threshold=3)
    print(f"  Outliers eliminados: {len(df) - len(df_clean)} filas")
    
    # Estandarizar tipos de datos categóricos para evitar problemas de mezcla de tipos
    for col in categorical_cols:
        if col != "Cantidad_Recursos":  # Cantidad_Recursos ya es numérica
            df_clean[col] = df_clean[col].astype(str)
    
    # Retornar datos limpios y tipados
    return df_clean, numeric_cols, categorical_cols

def calcular_kde(columna, df):
    # Usar Scott's rule para bandwidth óptimo
    valores = df[columna].dropna().values
    if len(valores) > 0:
        try:
            return columna, gaussian_kde(valores, bw_method='scott')
        except Exception as e:
            print(f"    Error al calcular KDE para {columna}: {e}")
            return columna, None
    return columna, None

def _analizar_datos_originales(df, numeric_cols, categorical_cols):
    """
    Analiza los datos originales para extraer distribuciones estadísticas y parámetros
    necesarios para la generación de datos sintéticos.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos limpios
        numeric_cols (list): Lista de columnas numéricas
        categorical_cols (list): Lista de columnas categóricas
        
    Returns:
        dict: Diccionario con todos los parámetros estadísticos extraídos
    """
    print("\n=== ANALIZANDO DATOS ORIGINALES ===")
    
    # Diccionario para almacenar todos los parámetros
    analisis = {
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols
    }
    
    # 1. Calcular KDEs para variables numéricas (paralelizado)
    print("  Calculando KDEs para variables numéricas...")
    kdes = {}    

    # Procesar secuencialmente (evitar multiprocessing)
    for col in numeric_cols:
        resultado = calcular_kde(col, df)
        if resultado:
            kdes[resultado[0]] = resultado[1]
    
    analisis["kdes"] = kdes

    '''
    from functools import partial
    calcular_kde_parcial = partial(calcular_kde, df=df)
    
    # Usar múltiples núcleos para acelerar el cálculo de KDEs
    from multiprocessing import Pool, cpu_count      

    # Usar hasta 4 núcleos o los disponibles, lo que sea menos
    with Pool(processes=min(4, cpu_count())) as pool:
        resultados = pool.map(calcular_kde_parcial, numeric_cols)
        
    # Convertir resultados a diccionario
    kdes = dict(resultados)
    analisis["kdes"] = kdes
    '
    '''
    # 2. Analizar distribuciones de variables categóricas
    print("  Analizando distribuciones de variables categóricas...")
    cat_distributions = {}
    for col in categorical_cols:
        cat_distributions[col] = df[col].value_counts(normalize=True)
    analisis["cat_distributions"] = cat_distributions
    
    # 3. Análisis de probabilidades condicionales más detallado
    print("  Analizando probabilidades condicionales...")
    conditional_distributions = analizar_probabilidades_condicionales(df, categorical_cols, numeric_cols)
    analisis["conditional_distributions"] = conditional_distributions
    
    # 4. Preparar datos para preservar correlaciones
    print("  Preparando datos para análisis de correlaciones...")
    df_corr = df.copy()
    encoders = {}

    for col in categorical_cols:
        if col != "Cantidad_Recursos":  # Cantidad_Recursos ya es numérica
            encoders[col] = LabelEncoder()
            df_corr[col] = encoders[col].fit_transform(df_corr[col])

    # Calcular matriz de correlación incluyendo todas las variables
    all_cols = numeric_cols + categorical_cols
    corr_matrix = df_corr[all_cols].corr()
    analisis["encoders"] = encoders
    analisis["corr_matrix"] = corr_matrix
    
    # 5. Extraer valores únicos de Tamaño_Tarea de los datos reales para limitar los sintéticos
    tamanos_reales = sorted(df["Tamaño_Tarea"].unique())
    analisis["tamanos_reales"] = tamanos_reales
    print(f"  Valores únicos de Tamaño_Tarea: {len(tamanos_reales)} niveles identificados")
    
    # 6. Extraer la distribución real de Cantidad_Recursos
    dist_real_recursos = df["Cantidad_Recursos"].value_counts(normalize=True).to_dict()
    analisis["dist_real_recursos"] = dist_real_recursos
    print(f"  Distribución de Cantidad_Recursos: {dist_real_recursos}")
    
    # 7. Extraer correlaciones críticas
    correlaciones_criticas = _extraer_correlaciones_criticas(df_corr)
    analisis["correlaciones_criticas"] = correlaciones_criticas
    
    # Informar más detalladamente sobre las correlaciones críticas
    print("\n--- Correlaciones críticas identificadas ---")
    for key, value in correlaciones_criticas.items():
        print(f"  {key}: {value:.4f}")
    
    return analisis

def _extraer_correlaciones_criticas(df_corr):
    """
    Extrae las correlaciones críticas que deben preservarse en los datos sintéticos.
    
    Args:
        df_corr (pd.DataFrame): DataFrame con variables codificadas para correlación
        
    Returns:
        dict: Diccionario con las correlaciones críticas
    """
    # Definir pares de variables con correlaciones importantes a preservar
    pares_criticos = [
        ("Complejidad", "Fase_Tarea"),
        ("Carga_Trabajo_R1", "Cantidad_Recursos"),
        ("Experiencia_R1", "Tipo_Tarea"),
        ("Experiencia_Equipo", "Cantidad_Recursos"),
        ("Tiempo_Ejecucion", "Cantidad_Recursos"),
        ("Tamaño_Tarea", "Carga_Trabajo_R1"),
        ("Carga_Trabajo_R1", "Experiencia_Equipo")
    ]
    
    # Calcular correlaciones
    correlaciones = {}
    for var1, var2 in pares_criticos:
        if var1 in df_corr.columns and var2 in df_corr.columns:
            # Extraer valor de correlación
            corr_value = df_corr[[var1, var2]].corr().iloc[0, 1]
            correlaciones[f"{var1}-{var2}"] = corr_value
    
    return correlaciones

def _generar_datos_sinteticos(df, n_samples, numeric_cols, categorical_cols, 
                             cat_distributions, kdes, conditional_distributions, 
                             encoders, corr_matrix, tamanos_reales, 
                             dist_real_recursos, correlaciones_criticas):
    """
    Genera datos sintéticos utilizando el método de cópulas optimizado.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos originales
        n_samples (int): Número de muestras a generar
        numeric_cols (list): Lista de columnas numéricas
        categorical_cols (list): Lista de columnas categóricas
        cat_distributions (dict): Distribuciones marginales para variables categóricas
        kdes (dict): Funciones de densidad kernel para variables numéricas
        conditional_distributions (dict): Distribuciones condicionales
        encoders (dict): Codificadores para variables categóricas
        corr_matrix (pd.DataFrame): Matriz de correlación
        tamanos_reales (list): Valores reales para Tamaño_Tarea
        dist_real_recursos (dict): Distribución real de Cantidad_Recursos
        correlaciones_criticas (dict): Correlaciones a preservar
        
    Returns:
        list: Lista de diccionarios con datos sintéticos generados
    """
    print(f"\n=== GENERANDO {n_samples} DATOS SINTÉTICOS ===")
    
    # Generar datos con el método de cópulas
    print("  Aplicando método de cópulas gaussianas...")
    synthetic_data = generar_datos_con_copulas(
        df, n_samples, numeric_cols, categorical_cols,
        cat_distributions, kdes, conditional_distributions, 
        encoders, corr_matrix, tamanos_reales, dist_real_recursos,
        correlaciones_criticas
    )
    
    print(f"  Generación completada: {len(synthetic_data)} registros")
    return synthetic_data

def _validar_y_ajustar_datos(df_real, synthetic_data, numeric_cols, categorical_cols, 
                           correlaciones_criticas, tamanos_reales):
    """
    Valida y ajusta los datos sintéticos generados, aplicando correcciones
    cuando sea necesario para mejorar la calidad.
    
    Args:
        df_real (pd.DataFrame): DataFrame con datos reales
        synthetic_data (list): Lista de diccionarios con datos sintéticos
        numeric_cols (list): Lista de columnas numéricas
        categorical_cols (list): Lista de columnas categóricas
        correlaciones_criticas (dict): Correlaciones críticas a preservar
        tamanos_reales (list): Lista de valores reales para Tamaño_Tarea
        
    Returns:
        pd.DataFrame: DataFrame con datos sintéticos ajustados y validados
    """
    print("\n=== VALIDANDO Y AJUSTANDO DATOS SINTÉTICOS ===")
    
    # 1. Convertir lista de diccionarios a DataFrame
    synthetic_df = pd.DataFrame(synthetic_data)
    
    # 2. Aplicar ajustes para mejorar correlaciones
    print("  Aplicando ajustes para preservar correlaciones...")
    synthetic_df = ajustar_correlaciones(
        df_real, synthetic_df, numeric_cols, categorical_cols, 
        correlaciones_criticas, tamanos_reales
    )
    
    # 3. Validar los datos sintéticos con pruebas estadísticas rigurosas
    print("  Ejecutando pruebas estadísticas de validación...")
    resultados_validacion = validar_datos_sinteticos(df_real, synthetic_df, numeric_cols, categorical_cols)
    
    # 4. Calcular intervalos de confianza
    confidence_interval = np.percentile(synthetic_df["Tiempo_Ejecucion"], [2.5, 97.5])
    print(f"  Intervalo de confianza del 95% para Tiempo_Ejecucion: {confidence_interval}")
    
    # 5. Generar gráficos comparativos si hay suficientes datos
    if len(df_real) >= 20 and len(synthetic_df) >= 20:
        print("  Generando gráficos comparativos...")
        try:
            generar_graficos_comparativos(df_real, synthetic_df, numeric_cols, categorical_cols)
        except Exception as e:
            print(f"    Error al generar gráficos: {e}")
    
    # 6. Validación específica de correlaciones críticas
    print("\n  Realizando validación específica de correlaciones críticas...")
    variables_criticas = ["Complejidad", "Tamaño_Tarea", "Cantidad_Recursos", "Experiencia_R1"]
    if all(var in df_real.columns and var in synthetic_df.columns for var in variables_criticas):
        validar_correlaciones_criticas(df_real, synthetic_df, variables_criticas)
    
    # 7. Validación de la distribución conjunta para pares clave
    print("\n  Validando distribuciones conjuntas...")
    pares_criticos = [
        ("Carga_Trabajo_R1", "Cantidad_Recursos"),
        ("Experiencia_R1", "Tipo_Tarea"),
        ("Complejidad", "Fase_Tarea")
    ]
    validar_distribucion_conjunta(df_real, synthetic_df, pares_criticos)
    
    # 8. Redondeo final de variables numéricas discretas
    print("\n  Aplicando redondeo final a variables numéricas discretas...")
    for col in ["Complejidad", "Experiencia_R1", "Experiencia_Equipo", "Claridad_Requisitos"]:
        if col in synthetic_df.columns:
            synthetic_df[col] = synthetic_df[col].round().astype(int)
    
    if "Carga_Trabajo_R1" in synthetic_df.columns:
        synthetic_df["Carga_Trabajo_R1"] = synthetic_df["Carga_Trabajo_R1"].round().astype(int)
        synthetic_df["Carga_Trabajo_R1"] = synthetic_df["Carga_Trabajo_R1"].clip(1, 3)
    
    print("\n=== GENERACIÓN DE DATOS SINTÉTICOS COMPLETADA ===")
    return synthetic_df


def eliminar_outliers(df, columns, threshold=3):
    """Elimina outliers basados en el z-score"""
    df_clean = df.copy()
    for col in columns:
        if col in df.columns:
            z_scores = np.abs(
                (df_clean[col] - df_clean[col].mean()) / df_clean[col].std()
            )
            df_clean = df_clean[z_scores < threshold]
    return df_clean


def analizar_probabilidades_condicionales(df, categorical_cols, numeric_cols):
    """
    Analiza las probabilidades condicionales entre variables para mejorar la coherencia
    en la generación de datos sintéticos.
    
    Esta función calcula tres tipos de relaciones condicionales:
    1. Probabilidades condicionales entre pares de variables categóricas
    2. Distribuciones de variables numéricas condicionadas por variables categóricas
    3. Probabilidades condicionales entre variables categóricas y numéricas discretizadas
    
    Args:
        df (pd.DataFrame): DataFrame con los datos originales
        categorical_cols (list): Lista de columnas categóricas
        numeric_cols (list): Lista de columnas numéricas
        
    Returns:
        dict: Diccionario con las distribuciones condicionales calculadas
    """
    conditional_distributions = {}
    
    # 1. PROBABILIDADES CONDICIONALES ENTRE VARIABLES CATEGÓRICAS
    # Optimización: Priorizar pares de variables con más valores únicos
    cat_pairs = []
    for i, cat1 in enumerate(categorical_cols):
        for j, cat2 in enumerate(categorical_cols[i+1:], i+1):
            n_unique1 = df[cat1].nunique()
            n_unique2 = df[cat2].nunique()
            cat_pairs.append((cat1, cat2, n_unique1 * n_unique2))
    
    # Procesar pares de variables ordenados por complejidad (menos complejos primero)
    for cat1, cat2, _ in sorted(cat_pairs, key=lambda x: x[2]):
        # Verificar suficientes datos para crear tablas confiables
        valid_mask = df[cat1].notna() & df[cat2].notna()
        if valid_mask.sum() >= max(5, 0.01 * len(df)):  # Al menos 5 filas o 1% de datos
            try:
                # Crear tabla de contingencia normalizada de manera más eficiente
                cont_table = pd.crosstab(
                    df.loc[valid_mask, cat1], 
                    df.loc[valid_mask, cat2], 
                    normalize='index',
                    dropna=False
                )
                conditional_distributions[f"{cat2}|{cat1}"] = cont_table
                # También guardar la relación inversa si es útil
                cont_table_inverse = pd.crosstab(
                    df.loc[valid_mask, cat2], 
                    df.loc[valid_mask, cat1], 
                    normalize='index',
                    dropna=False
                )
                conditional_distributions[f"{cat1}|{cat2}"] = cont_table_inverse
            except Exception as e:
                print(f"Advertencia: Error al calcular tabla de contingencia {cat1}-{cat2}: {str(e)}")
    
    # 2. DISTRIBUCIONES NUMÉRICAS CONDICIONADAS POR VARIABLES CATEGÓRICAS
    for cat_col in categorical_cols:
        category_counts = df[cat_col].value_counts()
        # Solo procesar categorías con suficientes datos
        valid_categories = category_counts[category_counts >= 10].index
        
        for num_col in numeric_cols:
            kde_dict = {}
            valid_num_mask = df[num_col].notna()
            
            if valid_num_mask.sum() < 10:  # Verificar datos suficientes
                continue
                
            # Usar método optimizado de agrupación
            grouped_data = {}
            for category in valid_categories:
                cat_mask = (df[cat_col] == category) & valid_num_mask
                if cat_mask.sum() >= 10:  # Solo crear KDE con suficientes puntos
                    grouped_data[category] = df.loc[cat_mask, num_col].values
            
            # Crear KDEs de manera eficiente
            for cat, values in grouped_data.items():
                if len(values) >= 10:  # Verificar de nuevo para seguridad
                    try:
                        # Seleccionar ancho de banda adaptativo basado en la dispersión de datos
                        data_std = np.std(values)
                        if data_std > 0:
                            if len(values) > 100:
                                # Para muchos puntos, usar Scott's rule
                                kde_dict[cat] = gaussian_kde(values, bw_method='scott')
                            else:
                                # Para pocos puntos, usar un enfoque más conservador
                                kde_dict[cat] = gaussian_kde(values, bw_method=0.5)
                        else:
                            # Si no hay variación, no crear KDE
                            kde_dict[cat] = None
                    except Exception as e:
                        print(f"Advertencia: No se pudo crear KDE para {cat_col}={cat}, {num_col}: {str(e)}")
                        kde_dict[cat] = None
                        
            # Solo guardar si se generaron KDEs
            if kde_dict:
                conditional_distributions[f"{num_col}|{cat_col}"] = kde_dict
    
    # 3. PROBABILIDADES CONDICIONALES ENTRE NUMÉRICAS DISCRETIZADAS Y CATEGÓRICAS
    # Determinar número óptimo de bins para cada variable numérica
    bin_counts = {}
    for num_col in numeric_cols:
        # Determinar número óptimo de bins basado en la regla de Sturges o cantidad de datos
        n_valid = df[num_col].notna().sum()
        if n_valid < 20:
            continue  # Saltar si hay pocos datos
            
        # Calcular número óptimo de bins considerando la cardinalidad de los datos
        unique_values = df[num_col].nunique()
        if unique_values <= 5:
            bin_counts[num_col] = min(unique_values, 5)  # Usar valores únicos si son pocos
        else:
            # Usar regla de Sturges para datos continuos: k = log2(n) + 1
            bin_counts[num_col] = min(int(np.log2(n_valid) + 1), 10)
    
    # Crear binning eficiente para cada variable numérica
    binned_data = {}
    for num_col, bins in bin_counts.items():
        try:
            # Usar qcut para distribución más uniforme de los datos
            binned_data[num_col] = pd.qcut(
                df[num_col], 
                q=bins, 
                labels=False, 
                duplicates='drop',
                retbins=False
            )
        except Exception as e:
            try:
                # Si qcut falla, intentar con cut
                binned_data[num_col] = pd.cut(
                    df[num_col], 
                    bins=bins, 
                    labels=False, 
                    duplicates='drop',
                    retbins=False
                )
            except Exception as e2:
                print(f"Advertencia: No se pudo discretizar {num_col}: {str(e2)}")
                continue
    
    # Calcular probabilidades condicionales para variables discretizadas
    for num_col, binned_col in binned_data.items():
        bin_col_name = f"{num_col}_bin"
        temp_df = df.copy()
        temp_df[bin_col_name] = binned_col
        
        for cat_col in categorical_cols:
            valid_mask = temp_df[bin_col_name].notna() & temp_df[cat_col].notna()
            if valid_mask.sum() < 10:
                continue
                
            try:
                # Tabla de contingencia normalizada
                cont_table = pd.crosstab(
                    temp_df.loc[valid_mask, bin_col_name], 
                    temp_df.loc[valid_mask, cat_col], 
                    normalize='index',
                    dropna=False
                )
                conditional_distributions[f"{cat_col}|{num_col}_bin"] = cont_table
                
                # También calcular la relación inversa que puede ser útil
                cont_table_inverse = pd.crosstab(
                    temp_df.loc[valid_mask, cat_col], 
                    temp_df.loc[valid_mask, bin_col_name], 
                    normalize='index',
                    dropna=False
                )
                conditional_distributions[f"{num_col}_bin|{cat_col}"] = cont_table_inverse
            except Exception as e:
                print(f"Advertencia: Error en tabla de contingencia {num_col}_bin-{cat_col}: {str(e)}")
    
    # Información sobre el resultado
    print(f"Análisis de probabilidades condicionales completado:")
    print(f"- Relaciones categóricas: {sum(1 for k in conditional_distributions if '|' in k and not k.endswith('_bin'))}")
    print(f"- KDEs numéricas condicionales: {sum(1 for k in conditional_distributions if isinstance(conditional_distributions[k], dict) and any(v is not None for v in conditional_distributions[k].values()))}")
    print(f"- Relaciones discretizadas: {sum(1 for k in conditional_distributions if '_bin|' in k or '|_bin' in k)}")
    
    return conditional_distributions


def generar_secuencia_fibonacci(limite_superior=1000):
    """Genera una secuencia de Fibonacci hasta un límite especificado"""
    fibonacci = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]
    while fibonacci[-1] < limite_superior:
        fibonacci.append(fibonacci[-1] + fibonacci[-2])
    return fibonacci


def encontrar_fibonacci_mas_cercano(valor, secuencia_fibonacci):
    """Encuentra el número de Fibonacci más cercano a un valor dado"""
    return min(secuencia_fibonacci, key=lambda x: abs(x - valor))


def generar_datos_con_copulas(df, n_samples, numeric_cols, categorical_cols, 
                             cat_distributions, kdes, cond_dists, encoders, corr_matrix,
                             tamanos_reales, dist_real_recursos, correlaciones_criticas):
    """
    Genera datos sintéticos preservando correlaciones mediante cópulas gaussianas.
    
    Esta función implementa un enfoque sofisticado para generar datos sintéticos que mantienen
    las correlaciones y distribuciones estadísticas de los datos originales, utilizando
    cópulas gaussianas y técnicas de ajuste de distribución.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos originales
        n_samples (int): Número de muestras sintéticas a generar
        numeric_cols (list): Lista de columnas numéricas
        categorical_cols (list): Lista de columnas categóricas
        cat_distributions (dict): Distribuciones marginales para variables categóricas
        kdes (dict): Funciones de densidad kernel para variables numéricas
        cond_dists (dict): Distribuciones condicionales entre variables
        encoders (dict): Codificadores para las variables categóricas
        corr_matrix (pd.DataFrame): Matriz de correlación entre variables
        tamanos_reales (list): Lista de valores reales observados para Tamaño_Tarea
        dist_real_recursos (dict): Distribución real de la variable Cantidad_Recursos
        correlaciones_criticas (dict): Correlaciones clave a preservar
        
    Returns:
        list: Lista de diccionarios con los datos sintéticos generados
    """
    # 1. Preparar recursos para generación de datos
    synthetic_data = []
    distribuciones_calculadas = _preparar_distribuciones(df, correlaciones_criticas)
    modelos_prediccion = _preparar_modelos_prediccion(df, correlaciones_criticas)
    
    # 2. Generar datos numéricos correlacionados
    numeric_data = generar_datos_numericos_correlacionados(df, n_samples, numeric_cols, corr_matrix, kdes)
    
    # 3. Generar muestras individuales
    for i in range(n_samples):
        sample = _generar_muestra_individual(
            i, df, numeric_cols, categorical_cols, numeric_data, 
            cat_distributions, cond_dists, distribuciones_calculadas,
            modelos_prediccion, tamanos_reales, dist_real_recursos,
            correlaciones_criticas
        )
        synthetic_data.append(sample)
    
    # 4. Convertir a DataFrame y aplicar ajuste final de correlaciones
    synthetic_df = pd.DataFrame(synthetic_data)
    synthetic_df = ajustar_correlaciones(df, synthetic_df, numeric_cols, categorical_cols, 
                                        correlaciones_criticas, tamanos_reales)   
    
    return synthetic_df.to_dict('records')

def _preparar_distribuciones(df, correlaciones_criticas):
    """Prepara las distribuciones estadísticas necesarias para la generación de datos"""
    distribuciones = {
        'tamano_counts': df["Tamaño_Tarea"].value_counts(normalize=True).to_dict(),
        'complejidad_dist': df["Complejidad"].value_counts(normalize=True).to_dict(),
        'fase_por_complejidad': {},
        'tipo_por_experiencia': {},
        'carga_por_recursos': {}
    }
    
    # Calcular distribuciones condicionales para Fase_Tarea según Complejidad
    for comp in range(1, 6):
        mask = (df["Complejidad"] >= comp - 0.5) & (df["Complejidad"] < comp + 0.5)
        if sum(mask) > 0:
            distribuciones['fase_por_complejidad'][comp] = df.loc[mask, "Fase_Tarea"].value_counts(normalize=True).to_dict()
    
    # Calcular distribuciones condicionales para Tipo_Tarea según Experiencia_R1
    for exp in range(1, 6):
        mask = (df["Experiencia_R1"] >= exp - 0.5) & (df["Experiencia_R1"] < exp + 0.5)
        if sum(mask) > 0:
            distribuciones['tipo_por_experiencia'][exp] = df.loc[mask, "Tipo_Tarea"].value_counts(normalize=True).to_dict()
    
    # Calcular distribuciones condicionales para Carga_Trabajo según Cantidad_Recursos
    for cant in sorted(df["Cantidad_Recursos"].unique()):
        mask = df["Cantidad_Recursos"] == cant
        if sum(mask) > 0:
            distribuciones['carga_por_recursos'][cant] = {
                "mean": df.loc[mask, "Carga_Trabajo_R1"].mean(),
                "median": df.loc[mask, "Carga_Trabajo_R1"].median(),
                "std": df.loc[mask, "Carga_Trabajo_R1"].std(),
                "dist": df.loc[mask, "Carga_Trabajo_R1"].value_counts(normalize=True).to_dict()
            }
            print(f"Distribución real para {cant} recursos: media={distribuciones['carga_por_recursos'][cant]['mean']:.2f}, mediana={distribuciones['carga_por_recursos'][cant]['median']}, std={distribuciones['carga_por_recursos'][cant]['std']:.2f}")
    
    # Registrar estadísticas adicionales
    distribuciones['carga_trabajo_std'] = df["Carga_Trabajo_R1"].std()
    print(f"Desviación estándar real de Carga_Trabajo_R1: {distribuciones['carga_trabajo_std']:.2f}")
    
    return distribuciones

def _preparar_modelos_prediccion(df, correlaciones_criticas):
    """Prepara los modelos de predicción para preservar las correlaciones críticas"""
    modelos = {
        'carga_recursos': None,
        'tamano_carga': None,
        'carga_experiencia': None,
        'tiempo_recursos': None,
        'tiempo_carga': None
    }

     # Verificar que el DataFrame no esté vacío y tenga suficientes datos
    if df.empty:
        print("ADVERTENCIA: DataFrame vacío. No se pueden crear modelos de predicción.")
        return modelos
    
    # Verificar disponibilidad de columnas críticas
    cols_requeridas = ["Carga_Trabajo_R1", "Cantidad_Recursos", "Experiencia_Equipo", 
                       "Tiempo_Ejecucion", "Tamaño_Tarea"]
    
    cols_faltantes = [col for col in cols_requeridas if col not in df.columns]
    if cols_faltantes:
        print(f"ADVERTENCIA: Faltan columnas necesarias: {cols_faltantes}")
        return modelos
    
    if "Carga_Trabajo_R1" in df.columns and "Cantidad_Recursos" in df.columns:
        # Modelo para Carga_Trabajo_R1 ~ Cantidad_Recursos
        X = df[["Cantidad_Recursos"]].values.reshape(-1, 1)
        y = df["Carga_Trabajo_R1"].values
        modelos['carga_recursos'] = LinearRegression().fit(X, y)
        print(f"Modelo Carga_Trabajo_R1 ~ Cantidad_Recursos: coef={modelos['carga_recursos'].coef_[0]:.6f}, intercept={modelos['carga_recursos'].intercept_:.4f}")

        # Amplificar el coeficiente para lograr la correlación deseada
        corr_real = correlaciones_criticas.get("Carga_Trabajo_R1-Cantidad_Recursos", 0.15)
        modelos['carga_recursos'].coef_[0] = modelos['carga_recursos'].coef_[0] * 3.0
        print(f"Coeficiente ajustado: {modelos['carga_recursos'].coef_[0]:.6f}")
        
        # Modelo para Tiempo_Ejecucion ~ Carga_Trabajo_R1
        modelos['tiempo_carga'] = LinearRegression()
        modelos['tiempo_carga'].fit(df[["Carga_Trabajo_R1"]].values.reshape(-1, 1), df["Tiempo_Ejecucion"].values)
        print(f"Modelo Tiempo_Ejecucion ~ Carga_Trabajo_R1: coef={modelos['tiempo_carga'].coef_[0]:.4f}, intercept={modelos['tiempo_carga'].intercept_:.4f}")
        
        # Modelo para Carga_Trabajo_R1 ~ Experiencia_Equipo
        modelos['carga_experiencia'] = LinearRegression()
        modelos['carga_experiencia'].fit(df[["Experiencia_Equipo"]].values.reshape(-1, 1), df["Carga_Trabajo_R1"].values)
        print(f"Modelo Carga_Trabajo_R1 ~ Experiencia_Equipo: coef={modelos['carga_experiencia'].coef_[0]:.4f}, intercept={modelos['carga_experiencia'].intercept_:.4f}")
        
        # Corregir el signo del coeficiente si es necesario
        corr_real_carga_exp = correlaciones_criticas.get("Carga_Trabajo_R1-Experiencia_Equipo", 0.16)
        if (corr_real_carga_exp > 0 and modelos['carga_experiencia'].coef_[0] < 0) or (corr_real_carga_exp < 0 and modelos['carga_experiencia'].coef_[0] > 0):
            print("ADVERTENCIA: El modelo Carga-Experiencia tiene signo opuesto a la correlación real. Invirtiendo el coeficiente.")
            modelos['carga_experiencia'].coef_[0] = abs(modelos['carga_experiencia'].coef_[0]) * (1 if corr_real_carga_exp > 0 else -1)
        
        # Modelo para Tiempo_Ejecucion ~ Cantidad_Recursos
        modelos['tiempo_recursos'] = LinearRegression()
        modelos['tiempo_recursos'].fit(df[["Cantidad_Recursos"]].values.reshape(-1, 1), df["Tiempo_Ejecucion"].values)
        print(f"Modelo Tiempo_Ejecucion ~ Cantidad_Recursos: coef={modelos['tiempo_recursos'].coef_[0]:.4f}, intercept={modelos['tiempo_recursos'].intercept_:.4f}")

        # Amplificar el coeficiente para una correlación más fuerte
        corr_real_tiempo_recursos = correlaciones_criticas.get("Tiempo_Ejecucion-Cantidad_Recursos", 0.11)
        modelos['tiempo_recursos'].coef_[0] = modelos['tiempo_recursos'].coef_[0] * 2.5
        print(f"Coeficiente amplificado: {modelos['tiempo_recursos'].coef_[0]:.4f}")

        # Corregir el signo si es necesario
        if (corr_real_tiempo_recursos > 0 and modelos['tiempo_recursos'].coef_[0] < 0) or (corr_real_tiempo_recursos < 0 and modelos['tiempo_recursos'].coef_[0] > 0):
            print("ADVERTENCIA: El modelo Tiempo-Recursos tiene signo opuesto a la correlación real. Invirtiendo el coeficiente.")
            modelos['tiempo_recursos'].coef_[0] = abs(modelos['tiempo_recursos'].coef_[0]) * (1 if corr_real_tiempo_recursos > 0 else -1)
    
    return modelos

def _generar_muestra_individual(i, df, numeric_cols, categorical_cols, numeric_data, 
                              cat_distributions, cond_dists, distribuciones,
                              modelos, tamanos_reales, dist_real_recursos, correlaciones_criticas):
    """Genera una muestra individual de datos sintéticos"""
    sample = {}
    
    # 1. Generar valores numéricos
    for j, col in enumerate(numeric_cols):
        sample[col] = numeric_data[j][i]
        
        # Ajustar complejidad a enteros entre 1 y 5
        if col == "Complejidad":
            sample[col] = min(max(round(sample[col]), 1), 5)
            
        # Para Tamaño_Tarea, usar directamente un valor de los datos reales
        if col == "Tamaño_Tarea":
            if np.random.random() < 0.9:  # 90% de las veces, seguir la distribución real
                tamanos = list(distribuciones['tamano_counts'].keys())
                probs = list(distribuciones['tamano_counts'].values())
                sample[col] = np.random.choice(tamanos, p=probs)
            else:
                # 10% de las veces, utilizar el valor generado pero limitado a los valores reales
                sample[col] = min(tamanos_reales, key=lambda x: abs(x - sample[col]))
    
    # 2. Generar "Experiencia del Encuestado" si existe
    if "Experiencia del Encuestado" in df.columns:
        sample["Experiencia del Encuestado"] = np.random.choice(df["Experiencia del Encuestado"].unique())
    
    # 3. Generar variables categóricas con relaciones preservadas
    sample = _generar_tipo_tarea(sample, cond_dists, cat_distributions, distribuciones)
    sample = _generar_fase_tarea(sample, cond_dists, cat_distributions, distribuciones)
    sample = _generar_recursos(sample, dist_real_recursos, distribuciones)
    
    # 4. Generar Carga_Trabajo_R1 preservando correlaciones críticas
    sample = _generar_carga_trabajo(sample, modelos, df, distribuciones)
    
    # 5. Ajustar Tiempo_Ejecucion para preservar correlación con recursos
    sample = _ajustar_tiempo_ejecucion(sample, modelos)
    
    # 6. Ajustar Experiencia_Equipo según recursos para preservar correlación
    sample = _ajustar_experiencia_equipo(sample)
    
    # 7. Generar datos para R2 y R3 si corresponde
    sample = _generar_datos_recursos_adicionales(sample)
    
    return sample

def _generar_tipo_tarea(sample, cond_dists, cat_distributions, distribuciones):
    """Genera Tipo_Tarea considerando relaciones con Complejidad y Experiencia_R1"""
    complejidad = sample["Complejidad"]
    experiencia_r1 = sample["Experiencia_R1"]
    bin_idx = min(int(complejidad) - 1, 4)
    exp_idx = int(round(sample["Experiencia_R1"]))
    
    # Generar Tipo_Tarea con mejor correlación con Experiencia_R1
    if np.random.random() < 0.6:  # 60% basado en distribución condicional detallada
        if exp_idx in distribuciones['tipo_por_experiencia']:
            dist = distribuciones['tipo_por_experiencia'][exp_idx]
            tipos = list(dist.keys())
            probs = list(dist.values())
            if sum(probs) > 0:
                probs = [p/sum(probs) for p in probs]
                tipo_tarea = np.random.choice(tipos, p=probs)
            else:
                tipo_tarea = np.random.choice(
                    cat_distributions["Tipo_Tarea"].index,
                    p=cat_distributions["Tipo_Tarea"].values
                )
        else:
            # Fallback si no hay datos para esta experiencia
            tipo_tarea = np.random.choice(
                cat_distributions["Tipo_Tarea"].index,
                p=cat_distributions["Tipo_Tarea"].values
            )
    else:
        # 40% basado en método original para mantener variabilidad
        if np.random.random() < 0.7:  # 70% basado en Complejidad
            try:
                # Usar distribución condicional si está disponible
                if f"Tipo_Tarea|Complejidad_bin" in cond_dists:
                    dist = cond_dists[f"Tipo_Tarea|Complejidad_bin"]
                    if bin_idx in dist.index:
                        probs = dist.loc[bin_idx].values
                        cats = dist.columns
                        tipo_tarea = np.random.choice(cats, p=probs)
                    else:
                        tipo_tarea = np.random.choice(
                            cat_distributions["Tipo_Tarea"].index,
                            p=cat_distributions["Tipo_Tarea"].values
                        )
                else:
                    tipo_tarea = np.random.choice(
                        cat_distributions["Tipo_Tarea"].index,
                        p=cat_distributions["Tipo_Tarea"].values
                    )
            except:
                tipo_tarea = np.random.choice(
                    cat_distributions["Tipo_Tarea"].index,
                    p=cat_distributions["Tipo_Tarea"].values
                )
        else:  # 30% basado en Experiencia_R1 (para preservar correlación)
            if exp_idx in distribuciones['tipo_por_experiencia']:
                dist = distribuciones['tipo_por_experiencia'][exp_idx]
                tipos = list(dist.keys())
                probs = list(dist.values())
                if sum(probs) > 0:
                    probs = [p/sum(probs) for p in probs]
                    tipo_tarea = np.random.choice(tipos, p=probs)
                else:
                    tipo_tarea = np.random.choice(
                        cat_distributions["Tipo_Tarea"].index,
                        p=cat_distributions["Tipo_Tarea"].values
                    )
            else:
                tipo_tarea = np.random.choice(
                    cat_distributions["Tipo_Tarea"].index,
                    p=cat_distributions["Tipo_Tarea"].values
                )
    
    sample["Tipo_Tarea"] = tipo_tarea
    return sample

def _generar_fase_tarea(sample, cond_dists, cat_distributions, distribuciones):
    """Genera Fase_Tarea considerando relaciones con Tipo_Tarea y Complejidad"""
    complejidad = sample["Complejidad"]
    tipo_tarea = sample["Tipo_Tarea"]
    
    if np.random.random() < 0.7:  # 70% basado en Tipo_Tarea
        try:
            if f"Fase_Tarea|Tipo_Tarea" in cond_dists:
                dist = cond_dists[f"Fase_Tarea|Tipo_Tarea"]
                if tipo_tarea in dist.index:
                    probs = dist.loc[tipo_tarea].values
                    cats = dist.columns
                    fase_tarea = np.random.choice(cats, p=probs)
                else:
                    fase_tarea = np.random.choice(
                        cat_distributions["Fase_Tarea"].index,
                        p=cat_distributions["Fase_Tarea"].values
                    )
            else:
                fase_tarea = np.random.choice(
                    cat_distributions["Fase_Tarea"].index,
                    p=cat_distributions["Fase_Tarea"].values
                )
        except:
            fase_tarea = np.random.choice(
                cat_distributions["Fase_Tarea"].index,
                p=cat_distributions["Fase_Tarea"].values
            )
    else:  # 30% basado en Complejidad (para preservar correlación)
        if complejidad in distribuciones['fase_por_complejidad']:
            dist = distribuciones['fase_por_complejidad'][complejidad]
            fases = list(dist.keys())
            probs = list(dist.values())
            if sum(probs) > 0:
                probs = [p/sum(probs) for p in probs]
                fase_tarea = np.random.choice(fases, p=probs)
            else:
                fase_tarea = np.random.choice(
                    cat_distributions["Fase_Tarea"].index,
                    p=cat_distributions["Fase_Tarea"].values
                )
        else:
            fase_tarea = np.random.choice(
                cat_distributions["Fase_Tarea"].index,
                p=cat_distributions["Fase_Tarea"].values
            )
            
    sample["Fase_Tarea"] = fase_tarea
    return sample

def _generar_recursos(sample, dist_real_recursos, distribuciones):
    """Genera Cantidad_Recursos considerando dependencias con Complejidad"""
    complejidad = sample["Complejidad"]
    
    if np.random.random() < 0.95:  # 95% de las veces, usar distribución empírica directa
        recursos = list(dist_real_recursos.keys())
        probs = list(dist_real_recursos.values())
        cantidad_recursos = np.random.choice(recursos, p=probs)
    else:  # 5% de las veces, usar el método basado en Complejidad
        if complejidad >= 4:
            probs_recursos = [0.2, 0.4, 0.4]  # Probabilidades para 1, 2, 3 recursos
        elif complejidad >= 3:
            probs_recursos = [0.3, 0.5, 0.2]
        else:
            probs_recursos = [0.6, 0.3, 0.1]
            
        cantidad_recursos = np.random.choice([1, 2, 3], p=probs_recursos)
    
    sample["Cantidad_Recursos"] = cantidad_recursos
    return sample

def _generar_carga_trabajo(sample, modelos, df, distribuciones):
    """Genera Carga_Trabajo_R1 considerando múltiples factores y preservando correlaciones"""
    cantidad_recursos = sample["Cantidad_Recursos"]
    carga_trabajo_metodos = np.random.choice([1, 2, 3, 4], p=[0.3, 0.3, 0.2, 0.2])
    
    if carga_trabajo_metodos == 1 and modelos['carga_recursos'] is not None:
        # Método 1: Basado en Cantidad_Recursos (mantener correlación con recursos)
        carga_base = modelos['carga_recursos'].predict([[cantidad_recursos]])[0]
        noise_scale = 0.6  # Aumentar variabilidad
        noise = np.random.normal(0, noise_scale)
        carga_r1 = max(1, min(3, round(carga_base + noise)))
        
    elif carga_trabajo_metodos == 2 and modelos['tamano_carga'] is not None and "Tamaño_Tarea" in sample:
        # Método 2: Basado en Tamaño_Tarea (mejorar correlación con tamaño)
        carga_base = modelos['tamano_carga'].predict([[sample["Tamaño_Tarea"]]])[0]
        noise_scale = 0.6
        noise = np.random.normal(0, noise_scale)
        carga_r1 = max(1, min(3, round(carga_base + noise)))
        
    elif carga_trabajo_metodos == 3 and modelos['carga_experiencia'] is not None:
        # Método 3: Basado en Experiencia_Equipo (mejorar esta correlación clave)
        carga_base = modelos['carga_experiencia'].predict([[sample["Experiencia_Equipo"]]])[0]
        noise_scale = 0.5
        noise = np.random.normal(0, noise_scale)
        carga_r1 = max(1, min(3, round(carga_base + noise)))
        
    else:
        # Método 4: Distribución empírica directa para mayor variabilidad
        carga_values = [1, 2, 3]
        carga_dist_real = df["Carga_Trabajo_R1"].value_counts(normalize=True).sort_index()
        carga_probs = [carga_dist_real.get(val, 1/3) for val in carga_values]
        carga_probs = [p/sum(carga_probs) for p in carga_probs]
        carga_r1 = np.random.choice(carga_values, p=carga_probs)
    
    sample["Carga_Trabajo_R1"] = carga_r1
    
    # Aplicar ajuste adicional según Cantidad_Recursos
    if np.random.random() < 0.7:  # 70% de probabilidad de ajuste
        if cantidad_recursos == 1:
            # Si hay menos recursos, generalmente hay mayor carga de trabajo
            sample["Carga_Trabajo_R1"] = np.random.choice([1, 2, 3], p=[0.1, 0.3, 0.6])
        elif cantidad_recursos == 2:
            # Si hay recursos medios, distribución más equilibrada
            sample["Carga_Trabajo_R1"] = np.random.choice([1, 2, 3], p=[0.3, 0.4, 0.3])
        else:  # cantidad_recursos == 3
            # Si hay más recursos, generalmente hay menor carga de trabajo
            sample["Carga_Trabajo_R1"] = np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
            
    # Valores para R1 con mayor variabilidad
    # Añadir un componente aleatorio para incrementar variabilidad
    exp_r1_base = sample["Experiencia_R1"]
    variabilidad = np.random.normal(0, 0.5)  # Desviación estándar mayor
    sample["Experiencia_R1"] = round(min(max(exp_r1_base + variabilidad, 1), 5))
    
    sample["Carga_Trabajo_R1"] = round(min(max(sample["Carga_Trabajo_R1"], 1), 3))
    return sample

def _ajustar_tiempo_ejecucion(sample, modelos):
    """Ajusta Tiempo_Ejecucion para preservar correlaciones con recursos"""
    if modelos['tiempo_recursos'] is not None:
        if np.random.random() < 0.8:  # 80% de probabilidad de ajuste
            tiempo_base = sample["Tiempo_Ejecucion"]
            cantidad_recursos = sample["Cantidad_Recursos"]
            tiempo_modelo = modelos['tiempo_recursos'].predict([[cantidad_recursos]])[0]
            
            # Aumentar significativamente el peso del modelo
            peso_modelo = 0.7
            tiempo_ajustado = tiempo_base * (1 - peso_modelo) + tiempo_modelo * peso_modelo
            
            # Reducir el ruido para preservar mejor la señal
            ruido = np.random.normal(0, tiempo_base * 0.1)
            sample["Tiempo_Ejecucion"] = max(0.1, tiempo_ajustado + ruido)
    
    return sample

def _ajustar_experiencia_equipo(sample):
    """Ajusta Experiencia_Equipo según Cantidad_Recursos para preservar correlación"""
    cantidad_recursos = sample["Cantidad_Recursos"]
    if np.random.random() < 0.3:  # 30% de probabilidad de ajuste
        if cantidad_recursos == 1:
            # Si hay menos recursos, generalmente hay menor experiencia de equipo
            exp_equipo_base = sample["Experiencia_Equipo"] 
            sample["Experiencia_Equipo"] = max(1, min(5, round(exp_equipo_base * 0.8)))
        elif cantidad_recursos == 3:
            # Si hay más recursos, generalmente hay mayor experiencia de equipo
            exp_equipo_base = sample["Experiencia_Equipo"]
            sample["Experiencia_Equipo"] = max(1, min(5, round(exp_equipo_base * 1.2)))
    
    # Normalizar valores para recursos
    sample["Experiencia_Equipo"] = round(min(max(sample["Experiencia_Equipo"], 1), 5))
    sample["Claridad_Requisitos"] = round(min(max(sample["Claridad_Requisitos"], 1), 5))
    
    return sample

def _generar_datos_recursos_adicionales(sample):
    """Genera datos para R2 y R3 si la cantidad de recursos lo requiere"""
    cantidad_recursos = sample["Cantidad_Recursos"]
    
    # Generar valores para R2 si hay al menos 2 recursos
    if cantidad_recursos >= 2:
        # Generar valores correlacionados con R1 pero con más variabilidad
        variabilidad_carga = np.random.normal(0, 0.3)
        variabilidad_exp = np.random.normal(0, 0.4)
        
        carga_r2 = min(max(round(sample["Carga_Trabajo_R1"] * 
                   np.random.normal(1, 0.3) + variabilidad_carga), 1), 3)
        exp_r2 = min(max(round(sample["Experiencia_R1"] * 
                np.random.normal(1, 0.4) + variabilidad_exp), 1), 5)
        
        sample["Carga_Trabajo_R2"] = carga_r2
        sample["Experiencia_R2"] = exp_r2
    else:
        sample["Carga_Trabajo_R2"] = np.nan
        sample["Experiencia_R2"] = np.nan
    
    # Generar datos para R3 si hay 3 recursos
    if cantidad_recursos == 3:
        # Generar valores correlacionados con promedio de R1 y R2
        avg_carga = (sample["Carga_Trabajo_R1"] + sample["Carga_Trabajo_R2"]) / 2
        avg_exp = (sample["Experiencia_R1"] + sample["Experiencia_R2"]) / 2
        
        variabilidad_carga = np.random.normal(0, 0.3)
        variabilidad_exp = np.random.normal(0, 0.4)
        
        carga_r3 = min(max(round(avg_carga * 
                   np.random.normal(1, 0.3) + variabilidad_carga), 1), 3)
        exp_r3 = min(max(round(avg_exp * 
                np.random.normal(1, 0.4) + variabilidad_exp), 1), 5)
        
        sample["Carga_Trabajo_R3"] = carga_r3
        sample["Experiencia_R3"] = exp_r3
    else:
        sample["Carga_Trabajo_R3"] = np.nan
        sample["Experiencia_R3"] = np.nan
        
    return sample

def generar_datos_numericos_correlacionados(df, n_samples, numeric_cols, corr_matrix, kdes):
    """
    Genera variables numéricas correlacionadas usando descomposición de Cholesky con optimizaciones.
    
    Esta función implementa la generación de datos correlacionados respetando tanto las correlaciones
    entre variables como sus distribuciones marginales individuales, utilizando un proceso de dos pasos:
    1. Genera datos normales correlacionados mediante descomposición de Cholesky
    2. Aplica transformación de cuantiles para mapear a las distribuciones marginales originales
    
    Args:
        df (pd.DataFrame): DataFrame con los datos originales
        n_samples (int): Número de muestras a generar
        numeric_cols (list): Lista de columnas numéricas a generar
        corr_matrix (pd.DataFrame): Matriz de correlación entre variables
        kdes (dict): Diccionario con funciones de densidad kernel para cada variable
    
    Returns:
        list: Lista de listas con los datos sintéticos generados para cada variable
    """
    # 1. PREPARACIÓN DE LA MATRIZ DE CORRELACIÓN
    # Extraer submatriz de correlación para variables numéricas
    num_corr = corr_matrix.loc[numeric_cols, numeric_cols].values
    
    # Verificación de matriz semidefinida positiva con mejor manejo de errores numéricos
    min_eig = np.min(np.linalg.eigvals(num_corr))
    if min_eig < 0:
        # Ajuste proporcional: usar factor basado en el autovalor mínimo
        adjustment = abs(min_eig) * 1.1
        num_corr = num_corr + np.eye(len(num_corr)) * adjustment
        print(f"Matriz de correlación ajustada (autovalor mínimo: {min_eig:.6f})")
    
    # Regularización óptima adaptativa basada en el tamaño de la matriz
    reg_factor = max(0.005, min(0.02, 0.05 / len(numeric_cols)))
    num_corr = (1 - reg_factor) * num_corr + reg_factor * np.eye(len(num_corr))
    
    # 2. GENERACIÓN DE DATOS CORRELACIONADOS
    try:
        # Descomposición de Cholesky con manejo de excepciones
        L = np.linalg.cholesky(num_corr)
    except np.linalg.LinAlgError:
        # Si falla, intentar con regularización adicional
        print("Advertencia: La descomposición de Cholesky falló. Aplicando regularización adicional.")
        reg_factor = 0.05
        num_corr = (1 - reg_factor) * num_corr + reg_factor * np.eye(len(num_corr))
        L = np.linalg.cholesky(num_corr)
    
    # Generación optimizada de datos correlacionados
    uncorrelated = np.random.normal(size=(len(numeric_cols), n_samples))
    correlated = np.dot(L, uncorrelated)
    
    # 3. TRANSFORMACIÓN A DISTRIBUCIONES MARGINALES
    transformed_data = []

    for i, col in enumerate(numeric_cols):
        # Convertir a distribución uniforme usando CDF de normal estándar
        uniform_data = norm.cdf(correlated[i])
        
        # Invertir CDF usando KDE y grid de alta resolución
        kde = kdes[col]
        
        # Crear grid adaptativo: más densidad en regiones importantes
        # Expandir ligeramente el rango para manejar valores extremos
        data_min = df[col].min() * 0.95
        data_max = df[col].max() * 1.05
        
        # Grid de resolución adaptativa con más puntos en variables continuas
        n_grid = 3000 if df[col].nunique() > 100 else 1000
        x_grid = np.linspace(data_min, data_max, n_grid)
        
        # Evaluar KDE (vectorizado)
        kde_vals = kde.evaluate(x_grid)
        
        # Normalizar para asegurar que sume 1
        kde_vals = kde_vals / kde_vals.sum()
        
        # Calcular CDF empírica (acumulada)
        kde_cdf = np.cumsum(kde_vals)
        
        # Asegurar que CDF termine en 1 exactamente
        kde_cdf = kde_cdf / kde_cdf[-1]
        
        # 4. TRANSFORMACIÓN DE CUANTILES OPTIMIZADA 
        # Preasignar array para valores transformados
        col_data = np.zeros(n_samples)
        
        # Búsqueda binaria vectorizada para mayor eficiencia
        indices = np.searchsorted(kde_cdf, uniform_data)
        
        # Corregir índices límite
        indices = np.clip(indices, 1, len(kde_cdf) - 1)
        
        # Interpolación lineal vectorizada
        # Calcular índices izquierdo y derecho para interpolación
        indices_left = indices - 1
        
        # Obtener valores x e y para interpolación
        x_left = x_grid[indices_left]
        x_right = x_grid[indices]
        y_left = kde_cdf[indices_left]
        y_right = kde_cdf[indices]
        
        # Calcular pendiente evitando división por cero
        denominador = y_right - y_left
        pendiente = np.where(denominador > 1e-10, 
                            (x_right - x_left) / denominador,
                            0)
        
        # Interpolación vectorizada
        x_interp = x_left + (uniform_data - y_left) * pendiente
        col_data = x_interp
        
        # 5. AJUSTE DE VARIABILIDAD PARA VARIABLES ESPECÍFICAS
        # Aplicar ruido controlado para ciertas variables
        if col in ["Tamaño_Tarea", "Experiencia_R1"]:
            # Factor de ruido adaptativo
            noise_factor = 0.05 if col == "Tamaño_Tarea" else 0.1
            
            # Generar ruido uniforme centrado
            noise = np.random.uniform(-noise_factor, noise_factor, size=n_samples)
            
            # Aplicar ruido multiplicativo preservando signo
            col_data = col_data * (1 + noise)
            
            # Asegurar límites válidos si la variable tiene restricciones conocidas
            if col == "Experiencia_R1":
                col_data = np.clip(col_data, 0.5, 5.5)  # Para redondeo posterior
        
        transformed_data.append(col_data)

    return transformed_data


def ajustar_correlaciones(df_real, df_sintetico, numeric_cols, categorical_cols, 
                         correlaciones_criticas, tamanos_reales):
    """
    Ajusta las correlaciones en los datos sintéticos para que se asemejen más a los datos reales.
    
    Esta función realiza varios ajustes para asegurar que las correlaciones entre variables
    y sus distribuciones coincidan lo más posible con los datos reales, lo que mejora
    la calidad y representatividad de los datos sintéticos generados.
    
    Args:
        df_real (pd.DataFrame): DataFrame con los datos reales
        df_sintetico (pd.DataFrame): DataFrame con los datos sintéticos a ajustar
        numeric_cols (list): Lista de columnas numéricas
        categorical_cols (list): Lista de columnas categóricas
        correlaciones_criticas (dict): Diccionario con correlaciones objetivo clave
        tamanos_reales (list): Lista de valores reales para Tamaño_Tarea
        
    Returns:
        pd.DataFrame: DataFrame con los datos sintéticos ajustados
    """
    print("\n=== INICIANDO AJUSTE DE CORRELACIONES EN DATOS SINTÉTICOS ===")
    
    # 1. AJUSTE DE DISTRIBUCIONES UNIVARIADAS
    df_sintetico = _ajustar_distribucion_tamano_tarea(df_real, df_sintetico)
    df_sintetico = _ajustar_distribucion_experiencia(df_real, df_sintetico)
    
    # 2. AJUSTE DE CORRELACIONES BIVARIADAS CRÍTICAS
    pares_criticos = [
        ("Complejidad", "Fase_Tarea"),
        ("Carga_Trabajo_R1", "Cantidad_Recursos"),
        ("Experiencia_R1", "Tipo_Tarea"),
        ("Tiempo_Ejecucion", "Cantidad_Recursos"),
        ("Tamaño_Tarea", "Carga_Trabajo_R1"),
        ("Carga_Trabajo_R1", "Experiencia_Equipo")
    ]
    
    # Diccionario con funciones específicas para cada par de correlación
    ajustadores = {
        ("Complejidad", "Fase_Tarea"): _ajustar_complejidad_fase,
        ("Carga_Trabajo_R1", "Cantidad_Recursos"): _ajustar_carga_recursos,
        ("Experiencia_R1", "Tipo_Tarea"): _ajustar_experiencia_tipo,
        ("Tiempo_Ejecucion", "Cantidad_Recursos"): _ajustar_tiempo_recursos,
        ("Tamaño_Tarea", "Carga_Trabajo_R1"): _ajustar_tamano_carga,
        ("Carga_Trabajo_R1", "Experiencia_Equipo"): _ajustar_carga_experiencia
    }
    
    # Procesar cada par de variables críticas
    for var1, var2 in pares_criticos:
        par = (var1, var2)
        key = f"{var1}-{var2}"
        
        if key in correlaciones_criticas and par in ajustadores:
            print(f"\n=== Ajustando correlación {key} ===")
            corr_objetivo = correlaciones_criticas[key]
            df_sintetico = ajustadores[par](df_real, df_sintetico, corr_objetivo)
    
    # 3. AJUSTE FINAL DE VARIABILIDAD
    df_sintetico = _ajustar_variabilidad(df_real, df_sintetico)
    
    print("\n=== AJUSTE DE CORRELACIONES FINALIZADO ===")
    return df_sintetico

def _ajustar_distribucion_tamano_tarea(df_real, df_sintetico):
    """Ajusta la distribución de Tamaño_Tarea para que coincida con los datos reales"""
    print("\n--- Ajustando distribución de Tamaño_Tarea ---")
    
    # Calcular distribuciones
    dist_real_tamano = df_real["Tamaño_Tarea"].value_counts(normalize=True)
    dist_sint_tamano = df_sintetico["Tamaño_Tarea"].value_counts(normalize=True)

    # Ajustar muestras para acercarse a la distribución real
    for tamano in dist_real_tamano.index:
        if tamano in dist_sint_tamano.index:
            # Determinar si necesitamos más muestras de este tamaño
            pct_real = dist_real_tamano[tamano]
            n_actual = sum(df_sintetico["Tamaño_Tarea"] == tamano)
            n_deseado = int(pct_real * len(df_sintetico))

            if n_actual < n_deseado:  # Necesitamos más muestras de este tamaño
                # Identificar tamaños sobrerrepresentados para reemplazar
                sobrerep = [t for t, p in dist_sint_tamano.items() 
                           if p > dist_real_tamano.get(t, 0) and t != tamano]
                
                if sobrerep:
                    # Seleccionar aleatoriamente filas para cambiar
                    n_cambiar = min(
                        n_deseado - n_actual,
                        sum(df_sintetico["Tamaño_Tarea"].isin(sobrerep)),
                    )
                    if n_cambiar > 0:
                        mask_cambiar = df_sintetico["Tamaño_Tarea"].isin(sobrerep)
                        indices_cambiar = (
                            df_sintetico[mask_cambiar].sample(n=n_cambiar).index
                        )
                        df_sintetico.loc[indices_cambiar, "Tamaño_Tarea"] = tamano
                        print(f"  Ajustados {n_cambiar} registros a Tamaño_Tarea = {tamano}")
    
    # Verificación final
    dist_final = df_sintetico["Tamaño_Tarea"].value_counts(normalize=True)
    print(f"  Distribución final de Tamaño_Tarea: {dist_final.sort_index().to_dict()}")
    
    return df_sintetico

def _ajustar_distribucion_experiencia(df_real, df_sintetico):
    """Ajusta la distribución de Experiencia_R1 para que coincida con los datos reales"""
    print("\n--- Ajustando distribución de Experiencia_R1 ---")
    
    # Calcular distribuciones
    dist_real_experiencia = df_real["Experiencia_R1"].value_counts(normalize=True)
    dist_sint_experiencia = df_sintetico["Experiencia_R1"].value_counts(normalize=True)
    
    # Corregir para cada nivel de experiencia
    for nivel in range(1, 6):
        pct_real = dist_real_experiencia.get(nivel, 0)
        n_actual = sum(df_sintetico["Experiencia_R1"] == nivel)
        n_deseado = int(pct_real * len(df_sintetico))
        
        if n_actual < n_deseado:  # Necesitamos más muestras de este nivel
            # Identificar niveles sobrerrepresentados para reemplazar
            sobrerep = [n for n, p in dist_sint_experiencia.items() 
                       if p > dist_real_experiencia.get(n, 0) and n != nivel]
            
            if sobrerep:
                # Seleccionar filas para cambiar
                n_cambiar = min(n_deseado - n_actual, sum(df_sintetico["Experiencia_R1"].isin(sobrerep)))
                if n_cambiar > 0:
                    mask_cambiar = df_sintetico["Experiencia_R1"].isin(sobrerep)
                    indices_cambiar = df_sintetico[mask_cambiar].sample(n=n_cambiar).index
                    df_sintetico.loc[indices_cambiar, "Experiencia_R1"] = nivel
                    print(f"  Ajustados {n_cambiar} registros a Experiencia_R1 = {nivel}")
    
    # Verificación final
    dist_final = df_sintetico["Experiencia_R1"].value_counts(normalize=True)
    print(f"  Distribución final de Experiencia_R1: {dist_final.sort_index().to_dict()}")
    
    return df_sintetico

def _ajustar_complejidad_fase(df_real, df_sintetico, corr_objetivo):
    """Ajusta la correlación entre Complejidad y Fase_Tarea"""
    print(f"  Ajustando correlación Complejidad-Fase_Tarea (objetivo: {corr_objetivo:.4f})")
    
    # Codificar Fase_Tarea para correlación
    le = LabelEncoder()
    df_sintetico_temp = df_sintetico.copy()
    
    # Convertir todas las fases a strings para asegurar compatibilidad
    fases_unicas = [str(fase) for fase in df_sintetico["Fase_Tarea"].unique()]
    le.fit(fases_unicas)
    
    # Convertir a string antes de transformar
    df_sintetico_temp["Fase_Tarea_cod"] = df_sintetico["Fase_Tarea"].astype(str).map(
        lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan
    )
    
    # Identificar pares de registros que al intercambiar Fase_Tarea mejoren la correlación
    corr_actual = df_sintetico_temp[["Complejidad", "Fase_Tarea_cod"]].corr().iloc[0, 1]
    print(f"  Correlación inicial: {corr_actual:.4f}")
    
    # Realizar intercambios para mejorar correlación
    n_intercambios = min(int(len(df_sintetico) * 0.05), 200)  # Máximo 5% o 200 filas
    mejoras = 0
    
    for _ in range(n_intercambios):
        # Seleccionar aleatoriamente dos filas
        idx1, idx2 = df_sintetico.sample(n=2).index
        
        # Realizar intercambio temporal
        fase_temp = df_sintetico.loc[idx1, "Fase_Tarea"]
        df_sintetico.loc[idx1, "Fase_Tarea"] = df_sintetico.loc[idx2, "Fase_Tarea"]
        df_sintetico.loc[idx2, "Fase_Tarea"] = fase_temp
        
        # Actualizar codificación
        df_sintetico_temp.loc[idx1, "Fase_Tarea_cod"] = le.transform([str(df_sintetico.loc[idx1, "Fase_Tarea"])])[0]
        df_sintetico_temp.loc[idx2, "Fase_Tarea_cod"] = le.transform([str(df_sintetico.loc[idx2, "Fase_Tarea"])])[0]
        
        # Calcular nueva correlación
        nueva_corr = df_sintetico_temp[["Complejidad", "Fase_Tarea_cod"]].corr().iloc[0, 1]
        
        # Si la nueva correlación es peor (más lejos del objetivo), deshacer el intercambio
        if abs(nueva_corr - corr_objetivo) > abs(corr_actual - corr_objetivo):
            # Deshacer intercambio
            fase_temp = df_sintetico.loc[idx1, "Fase_Tarea"]
            df_sintetico.loc[idx1, "Fase_Tarea"] = df_sintetico.loc[idx2, "Fase_Tarea"]
            df_sintetico.loc[idx2, "Fase_Tarea"] = fase_temp
            
            # Revertir codificación
            df_sintetico_temp.loc[idx1, "Fase_Tarea_cod"] = le.transform([str(df_sintetico.loc[idx1, "Fase_Tarea"])])[0]
            df_sintetico_temp.loc[idx2, "Fase_Tarea_cod"] = le.transform([str(df_sintetico.loc[idx2, "Fase_Tarea"])])[0]
        else:
            corr_actual = nueva_corr
            mejoras += 1
    
    # Verificar correlación final
    corr_final = df_sintetico_temp[["Complejidad", "Fase_Tarea_cod"]].corr().iloc[0, 1]
    print(f"  Correlación final: {corr_final:.4f} ({mejoras} intercambios efectivos)")
    
    return df_sintetico

def _ajustar_carga_recursos(df_real, df_sintetico, corr_objetivo):
    """Ajusta la correlación entre Carga_Trabajo_R1 y Cantidad_Recursos"""
    print(f"  Ajustando correlación Carga_Trabajo_R1-Cantidad_Recursos (objetivo: {corr_objetivo:.4f})")
    
    corr_actual = df_sintetico[["Carga_Trabajo_R1", "Cantidad_Recursos"]].corr().iloc[0, 1]
    print(f"  Correlación inicial: {corr_actual:.4f}")
    
    # Corrección para correlación invertida - más agresiva
    if (corr_actual < 0 and corr_objetivo > 0) or (corr_actual > 0 and corr_objetivo < 0):
        print("  CORRECCIÓN DE EMERGENCIA: Detectada correlación invertida entre Carga_Trabajo_R1 y Cantidad_Recursos")
        
        # Obtener distribución original por cada nivel de recursos
        carga_por_recursos = {}
        for cant in sorted(df_real["Cantidad_Recursos"].unique()):
            mask = df_real["Cantidad_Recursos"] == cant
            if sum(mask) > 0:
                carga_por_recursos[cant] = df_real.loc[mask, "Carga_Trabajo_R1"].value_counts(normalize=True).to_dict()
        
        # Aplicar reasignación completa basada en la distribución real condicional
        for cant in sorted(df_sintetico["Cantidad_Recursos"].unique()):
            if cant in carga_por_recursos:
                # Obtener la distribución real para esta cantidad de recursos
                dist = carga_por_recursos[cant]
                cargas = list(dist.keys())
                probs = list(dist.values())
                
                # Seleccionar todas las filas con esta cantidad de recursos
                mask = df_sintetico["Cantidad_Recursos"] == cant
                indices = df_sintetico[mask].index
                
                # Reasignar los valores de carga según la distribución real
                if len(indices) > 0 and len(cargas) > 0:
                    nuevas_cargas = np.random.choice(cargas, size=len(indices), p=probs)
                    df_sintetico.loc[indices, "Carga_Trabajo_R1"] = nuevas_cargas
                    print(f"  Ajustados {len(indices)} registros para Cantidad_Recursos = {cant}")
    else:
        # Ajuste progresivo para correlaciones con mismo signo pero diferente magnitud
        # Determinar cuánto necesitamos ajustar
        diff = corr_objetivo - corr_actual
        
        # División de los datos por cantidad de recursos
        for recursos in sorted(df_sintetico["Cantidad_Recursos"].unique()):
            indices = df_sintetico[df_sintetico["Cantidad_Recursos"] == recursos].index
            if len(indices) < 10:
                continue
            
            # Calcular incrementos o decrementos según la dirección necesaria
            if corr_objetivo > 0:
                # Para correlación positiva: más recursos, valores más altos
                ajuste = (recursos - 2) * 0.1 * abs(diff)  # Factor proporcional a la diferencia
            else:
                # Para correlación negativa: más recursos, valores más bajos
                ajuste = (2 - recursos) * 0.1 * abs(diff)
            
            # Aplicar ajuste progresivo
            n_ajustados = 0
            for idx in indices:
                carga_actual = df_sintetico.loc[idx, "Carga_Trabajo_R1"]
                nueva_carga = round(max(1, min(3, carga_actual + ajuste)))
                if nueva_carga != carga_actual:
                    df_sintetico.loc[idx, "Carga_Trabajo_R1"] = nueva_carga
                    n_ajustados += 1
            
            print(f"  Ajustados {n_ajustados} registros para Cantidad_Recursos = {recursos} (ajuste: {ajuste:.4f})")
    
    # Verificar correlación después del ajuste
    corr_final = df_sintetico[["Carga_Trabajo_R1", "Cantidad_Recursos"]].corr().iloc[0, 1]
    print(f"  Correlación después de ajustes: {corr_final:.4f}")
    
    # Si todavía es de signo incorrecto, último recurso: corrección binaria
    if (corr_final < 0 and corr_objetivo > 0) or (corr_final > 0 and corr_objetivo < 0):
        print("  CORRECCIÓN BINARIA FINAL: Invirtiendo asignación de Carga_Trabajo_R1")
        
        # Aplicación de patrones fuertes según cantidad de recursos
        patrones = {
            1: [1, 1, 1, 1, 2, 3],  # Recursos=1: mayoría carga baja
            2: [1, 2, 2, 2, 2, 3],  # Recursos=2: mayoría carga media
            3: [2, 2, 3, 3, 3, 3]   # Recursos=3: mayoría carga alta
        }
        
        n_total_ajustados = 0
        # Aplicar estos patrones al 80% de los datos
        for cant, patron in patrones.items():
            mask = df_sintetico["Cantidad_Recursos"] == cant
            indices = df_sintetico[mask].index
            
            if len(indices) > 0:
                # Aplicar a una gran proporción de los datos
                indices_cambio = np.random.choice(indices, size=int(len(indices) * 0.8), replace=False)
                nuevas_cargas = np.random.choice(patron, size=len(indices_cambio))
                df_sintetico.loc[indices_cambio, "Carga_Trabajo_R1"] = nuevas_cargas
                n_total_ajustados += len(indices_cambio)
        
        print(f"  Ajustados {n_total_ajustados} registros mediante corrección binaria")
        
        # Verificación final
        corr_final = df_sintetico[["Carga_Trabajo_R1", "Cantidad_Recursos"]].corr().iloc[0, 1]
        print(f"  Correlación final después de corrección binaria: {corr_final:.4f}")
    
    return df_sintetico

def _ajustar_experiencia_tipo(df_real, df_sintetico, corr_objetivo):
    """Ajusta la correlación entre Experiencia_R1 y Tipo_Tarea"""
    print(f"  Ajustando correlación Experiencia_R1-Tipo_Tarea (objetivo: {corr_objetivo:.4f})")
    
    # Codificar Tipo_Tarea para poder trabajar con correlaciones
    le = LabelEncoder()
    df_sintetico_temp = df_sintetico.copy()
    
    # Asegurar que todos los tipos sean strings
    tipos_unicos = [str(tipo) for tipo in df_sintetico["Tipo_Tarea"].unique()]
    le.fit(tipos_unicos)
    
    # Convertir a string antes de transformar
    df_sintetico_temp["Tipo_Tarea_cod"] = df_sintetico["Tipo_Tarea"].astype(str).map(
        lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan
    )
    
    corr_actual = df_sintetico_temp[["Experiencia_R1", "Tipo_Tarea_cod"]].corr().iloc[0, 1]
    print(f"  Correlación inicial: {corr_actual:.4f}")
    
    # Preparar distribución condicional de Tipo_Tarea por nivel de experiencia
    # Primero obtener la distribución real
    tipo_por_experiencia = {}
    for exp in range(1, 6):
        mask = (df_real["Experiencia_R1"] == exp)
        if sum(mask) > 0:
            tipo_por_experiencia[exp] = df_real.loc[mask, "Tipo_Tarea"].value_counts(normalize=True).to_dict()
    
    # Aplicar ajuste dirigido para casos con mayor desviación
    n_total_ajustados = 0
    
    # Determinar qué tipos de tarea son más comunes para cada nivel de experiencia
    for exp_level in range(1, 6):
        if exp_level not in tipo_por_experiencia:
            continue
            
        # Encontrar el tipo de tarea más común para este nivel de experiencia
        tipo_dist = tipo_por_experiencia[exp_level]
        tipo_preferido = max(tipo_dist.items(), key=lambda x: x[1])[0]
        
        # Obtener registros sintéticos con este nivel de experiencia
        indices = df_sintetico[df_sintetico["Experiencia_R1"] == exp_level].index
        if len(indices) == 0:
            continue
            
        # Ajustar un porcentaje de registros al tipo preferido
        n_ajustar = int(len(indices) * 0.15)  # Ajustar 15% de los casos
        indices_ajustar = np.random.choice(indices, min(n_ajustar, len(indices)), replace=False)
        df_sintetico.loc[indices_ajustar, "Tipo_Tarea"] = tipo_preferido
        n_total_ajustados += len(indices_ajustar)
        
        # Actualizar codificación
        for idx in indices_ajustar:
            df_sintetico_temp.loc[idx, "Tipo_Tarea_cod"] = le.transform([str(tipo_preferido)])[0]
    
    print(f"  Ajustados {n_total_ajustados} registros mediante asignación directa")
    
    # Continuar con intercambios aleatorios para refinamiento
    n_intercambios = min(int(len(df_sintetico) * 0.10) + 300, 500)
    mejoras = 0
    
    for _ in range(n_intercambios):
        idx1, idx2 = df_sintetico.sample(n=2).index
        
        temp_tipo = df_sintetico.loc[idx1, "Tipo_Tarea"]
        df_sintetico.loc[idx1, "Tipo_Tarea"] = df_sintetico.loc[idx2, "Tipo_Tarea"]
        df_sintetico.loc[idx2, "Tipo_Tarea"] = temp_tipo
        
        # Actualizar codificación
        df_sintetico_temp.loc[idx1, "Tipo_Tarea_cod"] = le.transform([str(df_sintetico.loc[idx1, "Tipo_Tarea"])])[0]
        df_sintetico_temp.loc[idx2, "Tipo_Tarea_cod"] = le.transform([str(df_sintetico.loc[idx2, "Tipo_Tarea"])])[0]
        
        nueva_corr = df_sintetico_temp[["Experiencia_R1", "Tipo_Tarea_cod"]].corr().iloc[0, 1]
        
        if abs(nueva_corr - corr_objetivo) > abs(corr_actual - corr_objetivo):
            # Deshacer intercambio
            temp_tipo = df_sintetico.loc[idx1, "Tipo_Tarea"]
            df_sintetico.loc[idx1, "Tipo_Tarea"] = df_sintetico.loc[idx2, "Tipo_Tarea"]
            df_sintetico.loc[idx2, "Tipo_Tarea"] = temp_tipo
            
            # Revertir codificación
            df_sintetico_temp.loc[idx1, "Tipo_Tarea_cod"] = le.transform([str(df_sintetico.loc[idx1, "Tipo_Tarea"])])[0]
            df_sintetico_temp.loc[idx2, "Tipo_Tarea_cod"] = le.transform([str(df_sintetico.loc[idx2, "Tipo_Tarea"])])[0]
        else:
            corr_actual = nueva_corr
            mejoras += 1
    
    # Verificar correlación final
    corr_final = df_sintetico_temp[["Experiencia_R1", "Tipo_Tarea_cod"]].corr().iloc[0, 1]
    print(f"  Correlación final: {corr_final:.4f} ({mejoras} intercambios efectivos)")
    
    return df_sintetico

def _ajustar_tiempo_recursos(df_real, df_sintetico, corr_objetivo):
    """Ajusta la correlación entre Tiempo_Ejecucion y Cantidad_Recursos"""
    print(f"  Ajustando correlación Tiempo_Ejecucion-Cantidad_Recursos (objetivo: {corr_objetivo:.4f})")
    
    corr_actual = df_sintetico[["Tiempo_Ejecucion", "Cantidad_Recursos"]].corr().iloc[0, 1]
    print(f"  Correlación inicial: {corr_actual:.4f}")
    
    # Si la correlación ya está sobreajustada, corregir en dirección opuesta
    if (corr_objetivo > 0 and corr_actual > corr_objetivo * 1.5) or (corr_objetivo < 0 and corr_actual < corr_objetivo * 1.5):
        print("  ADVERTENCIA: Correlación Tiempo-Recursos sobreajustada. Aplicando corrección inversa.")
        
        # Aplicar un enfoque más directo basado en factores fijos
        factores_tiempo = {
            1: 0.75,  # Para recursos=1, reducir tiempo
            2: 1.0,   # Para recursos=2, mantener tiempo base
            3: 1.25   # Para recursos=3, aumentar tiempo
        }
        
        n_total_ajustados = 0
        # Aplicar estos factores a una gran proporción de los datos
        for cant, factor in factores_tiempo.items():
            mask = df_sintetico["Cantidad_Recursos"] == cant
            indices = df_sintetico[mask].index
            
            if len(indices) > 10:  # Solo si hay suficientes datos
                # Aplicar a una gran proporción
                indices_ajustar = np.random.choice(indices, size=int(len(indices)*0.8), replace=False)
                
                for idx in indices_ajustar:
                    tiempo_original = df_sintetico.loc[idx, "Tiempo_Ejecucion"]
                    # Aplicar factor con un pequeño ruido para mantener variabilidad
                    ruido = np.random.uniform(0.9, 1.1)
                    df_sintetico.loc[idx, "Tiempo_Ejecucion"] = tiempo_original * factor * ruido
                    n_total_ajustados += 1
        
        print(f"  Ajustados {n_total_ajustados} registros mediante factores fijos")
    else:
        # Enfoque para ajustar la correlación: reescalamiento selectivo con factor reducido
        n_total_ajustados = 0
        for cantidad in df_sintetico["Cantidad_Recursos"].unique():
            mask = df_sintetico["Cantidad_Recursos"] == cantidad
            if sum(mask) < 10:  # Saltar si hay pocos datos
                continue
                
            # Ajustar factor según dirección de correlación objetivo
            if corr_objetivo > 0:
                # Si la correlación debe ser positiva: más recursos => más tiempo
                factor_ajuste = 1.0 + (cantidad - 2) * 0.05  # Factor más moderado
            else:
                # Si la correlación debe ser negativa: más recursos => menos tiempo
                factor_ajuste = 1.0 - (cantidad - 2) * 0.05  # Factor más moderado
                
            # Aplicar ajuste a una proporción de los datos
            indices = df_sintetico.loc[mask].sample(frac=0.4).index  # Proporción reducida
            for idx in indices:
                tiempo_original = df_sintetico.loc[idx, "Tiempo_Ejecucion"]
                df_sintetico.loc[idx, "Tiempo_Ejecucion"] = tiempo_original * factor_ajuste
                n_total_ajustados += 1
        
        print(f"  Ajustados {n_total_ajustados} registros mediante factores progresivos")
    
    # Comprobar correlación después del ajuste
    corr_final = df_sintetico[["Tiempo_Ejecucion", "Cantidad_Recursos"]].corr().iloc[0, 1]
    print(f"  Correlación final: {corr_final:.4f}")
    
    return df_sintetico

def _ajustar_tamano_carga(df_real, df_sintetico, corr_objetivo):
    """Ajusta la correlación entre Tamaño_Tarea y Carga_Trabajo_R1"""
    print(f"  Ajustando correlación Tamaño_Tarea-Carga_Trabajo_R1 (objetivo: {corr_objetivo:.4f})")
    
    corr_actual = df_sintetico[["Tamaño_Tarea", "Carga_Trabajo_R1"]].corr().iloc[0, 1]
    print(f"  Correlación inicial: {corr_actual:.4f}")
    
    # Si la correlación está lejos del objetivo
    if abs(corr_actual - corr_objetivo) > 0.08:
        # Crear un modelo simple para ajustar la relación
        X = df_real[["Tamaño_Tarea"]].values
        y = df_real["Carga_Trabajo_R1"].values
        modelo_simple = LinearRegression().fit(X, y)
        print(f"  Modelo lineal: coef={modelo_simple.coef_[0]:.4f}, intercept={modelo_simple.intercept_:.4f}")
        
        # Identificar registros que más contribuirían a mejorar la correlación
        tamaños_grandes = df_sintetico["Tamaño_Tarea"] > df_sintetico["Tamaño_Tarea"].median()
        n_total_ajustados = 0
        
        if corr_objetivo > 0:
            # Si queremos correlación positiva:
            # Para tamaños grandes, aumentar carga
            indices_grandes = df_sintetico[tamaños_grandes].sample(frac=0.4).index
            for idx in indices_grandes:
                tamano = df_sintetico.loc[idx, "Tamaño_Tarea"]
                carga_estimada = max(1, min(3, round(modelo_simple.predict([[tamano]])[0])))
                # Aplicar a algunos casos para no sobreajustar
                if np.random.random() < 0.7:
                    carga_anterior = df_sintetico.loc[idx, "Carga_Trabajo_R1"]
                    if carga_estimada != carga_anterior:
                        df_sintetico.loc[idx, "Carga_Trabajo_R1"] = carga_estimada
                        n_total_ajustados += 1
            
            # Para tamaños pequeños, reducir carga
            indices_pequeños = df_sintetico[~tamaños_grandes].sample(frac=0.3).index
            for idx in indices_pequeños:
                if df_sintetico.loc[idx, "Carga_Trabajo_R1"] > 1 and np.random.random() < 0.6:
                    df_sintetico.loc[idx, "Carga_Trabajo_R1"] -= 1
                    n_total_ajustados += 1
        else:
            # Si queremos correlación negativa
            # Lógica inversa
            indices_grandes = df_sintetico[tamaños_grandes].sample(frac=0.4).index
            for idx in indices_grandes:
                if df_sintetico.loc[idx, "Carga_Trabajo_R1"] > 1 and np.random.random() < 0.6:
                    df_sintetico.loc[idx, "Carga_Trabajo_R1"] -= 1
                    n_total_ajustados += 1
            
            indices_pequeños = df_sintetico[~tamaños_grandes].sample(frac=0.3).index
            for idx in indices_pequeños:
                if df_sintetico.loc[idx, "Carga_Trabajo_R1"] < 3 and np.random.random() < 0.6:
                    df_sintetico.loc[idx, "Carga_Trabajo_R1"] += 1
                    n_total_ajustados += 1
        
        print(f"  Ajustados {n_total_ajustados} registros")
    
    # Comprobar correlación después del ajuste
    corr_final = df_sintetico[["Tamaño_Tarea", "Carga_Trabajo_R1"]].corr().iloc[0, 1]
    print(f"  Correlación final: {corr_final:.4f}")
    
    return df_sintetico

def _ajustar_carga_experiencia(df_real, df_sintetico, corr_objetivo):
    """Ajusta la correlación entre Carga_Trabajo_R1 y Experiencia_Equipo"""
    print(f"  Ajustando correlación Carga_Trabajo_R1-Experiencia_Equipo (objetivo: {corr_objetivo:.4f})")
    
    corr_actual = df_sintetico[["Carga_Trabajo_R1", "Experiencia_Equipo"]].corr().iloc[0, 1]
    print(f"  Correlación inicial: {corr_actual:.4f}")
    
    if abs(corr_actual - corr_objetivo) > 0.08:
        # Enfoque basado en modelo
        X = df_real[["Experiencia_Equipo"]].values
        y = df_real["Carga_Trabajo_R1"].values
        modelo_carga_exp = LinearRegression().fit(X, y)
        print(f"  Modelo lineal: coef={modelo_carga_exp.coef_[0]:.4f}, intercept={modelo_carga_exp.intercept_:.4f}")
        
        # Identificar registros para ajustar
        exp_alta = df_sintetico["Experiencia_Equipo"] >= 4
        exp_baja = df_sintetico["Experiencia_Equipo"] <= 2
        n_total_ajustados = 0
        
        # Ajustar según dirección de correlación objetivo
        if corr_objetivo > 0:  
            # Correlación positiva: mayor experiencia, mayor carga
            indices_exp_alta = df_sintetico[exp_alta].sample(frac=0.5).index
            for idx in indices_exp_alta:
                experiencia = df_sintetico.loc[idx, "Experiencia_Equipo"]
                carga_estimada = modelo_carga_exp.predict([[experiencia]])[0]
                carga_ajustada = max(1, min(3, round(carga_estimada)))
                
                # Aplicar ajuste gradual para no sobreajustar
                carga_actual = df_sintetico.loc[idx, "Carga_Trabajo_R1"]
                if carga_ajustada > carga_actual:
                    df_sintetico.loc[idx, "Carga_Trabajo_R1"] = min(3, carga_actual + 1)
                    n_total_ajustados += 1
            
            # Para experiencia baja, ajustar carga hacia abajo
            indices_exp_baja = df_sintetico[exp_baja].sample(frac=0.4).index
            for idx in indices_exp_baja:
                experiencia = df_sintetico.loc[idx, "Experiencia_Equipo"]
                carga_estimada = modelo_carga_exp.predict([[experiencia]])[0]
                carga_ajustada = max(1, min(3, round(carga_estimada)))
                
                carga_actual = df_sintetico.loc[idx, "Carga_Trabajo_R1"]
                if carga_ajustada < carga_actual:
                    df_sintetico.loc[idx, "Carga_Trabajo_R1"] = max(1, carga_actual - 1)
                    n_total_ajustados += 1
        else:
            # Correlación negativa: mayor experiencia, menor carga
            indices_exp_alta = df_sintetico[exp_alta].sample(frac=0.5).index
            for idx in indices_exp_alta:
                carga_actual = df_sintetico.loc[idx, "Carga_Trabajo_R1"]
                if carga_actual > 1:
                    df_sintetico.loc[idx, "Carga_Trabajo_R1"] = carga_actual - 1
                    n_total_ajustados += 1
            
            indices_exp_baja = df_sintetico[exp_baja].sample(frac=0.4).index
            for idx in indices_exp_baja:
                carga_actual = df_sintetico.loc[idx, "Carga_Trabajo_R1"]
                if carga_actual < 3:
                    df_sintetico.loc[idx, "Carga_Trabajo_R1"] = carga_actual + 1
                    n_total_ajustados += 1
        
        print(f"  Ajustados {n_total_ajustados} registros")
    
    # Comprobar correlación después del ajuste
    corr_final = df_sintetico[["Carga_Trabajo_R1", "Experiencia_Equipo"]].corr().iloc[0, 1]
    print(f"  Correlación final: {corr_final:.4f}")
    
    return df_sintetico

def _ajustar_variabilidad(df_real, df_sintetico):
    """Ajusta la variabilidad de Carga_Trabajo_R1 para que coincida con los datos reales"""
    print("\n--- Ajustando variabilidad de variables clave ---")
    
    # Ajustar variabilidad de Carga_Trabajo_R1
    std_real = df_real["Carga_Trabajo_R1"].std()
    std_sint = df_sintetico["Carga_Trabajo_R1"].std()
    print(f"  Desviación estándar real de Carga_Trabajo_R1: {std_real:.4f}")
    print(f"  Desviación estándar sintética de Carga_Trabajo_R1: {std_sint:.4f}")

    if std_sint < std_real:
        factor_ajuste = std_real / std_sint
        print(f"  Factor de ajuste de variabilidad: {factor_ajuste:.4f}")
        
        # Seleccionar un subconjunto aleatorio para aplicar perturbaciones
        indices_ajuste = df_sintetico.sample(frac=0.4).index
        n_ajustados = 0
        
        for idx in indices_ajuste:
            carga_actual = df_sintetico.loc[idx, "Carga_Trabajo_R1"]
            # Añadir perturbación aleatoria proporcional
            perturbacion = np.random.choice([-1, 0, 1])
            nueva_carga = max(1, min(3, carga_actual + perturbacion))
            if nueva_carga != carga_actual:  # Solo aplicar si cambia el valor
                df_sintetico.loc[idx, "Carga_Trabajo_R1"] = nueva_carga
                n_ajustados += 1
        
        print(f"  Ajustados {n_ajustados} registros para aumentar variabilidad")
        
        # Verificar resultado
        std_final = df_sintetico["Carga_Trabajo_R1"].std()
        print(f"  Desviación estándar final de Carga_Trabajo_R1: {std_final:.4f}")
    
    return df_sintetico


def validar_datos_sinteticos(df_real, df_sintetico, columnas_numericas, columnas_categoricas):
    """
    Valida los datos sintéticos con pruebas estadísticas rigurosas.
    
    Esta función realiza tres tipos de validaciones:
    1. Prueba Kolmogorov-Smirnov para evaluar la similitud de distribuciones numéricas
    2. Prueba Chi-cuadrado para evaluar la similitud de distribuciones categóricas
    3. Evaluación de correlaciones entre variables para validar la preservación de relaciones
    
    Args:
        df_real (pd.DataFrame): DataFrame con los datos originales reales
        df_sintetico (pd.DataFrame): DataFrame con los datos sintéticos generados
        columnas_numericas (list): Lista de columnas numéricas a validar
        columnas_categoricas (list): Lista de columnas categóricas a validar
    
    Returns:
        dict: Diccionario con los resultados de las diferentes pruebas estadísticas
    """
    print("\n=== VALIDACIÓN DE DATOS SINTÉTICOS ===")
    
    # Inicializar diccionario para almacenar resultados
    resultados = {
        "ks_test": {},
        "chi2_test": {},
        "correlaciones": {"mae": None, "discrepancias": []}
    }
    
    # 1. VALIDAR VARIABLES NUMÉRICAS (KS TEST)
    resultados["ks_test"] = _validar_variables_numericas(df_real, df_sintetico, columnas_numericas)
    
    # 2. VALIDAR VARIABLES CATEGÓRICAS (CHI2)
    resultados["chi2_test"] = _validar_variables_categoricas(df_real, df_sintetico, columnas_categoricas)
    
    # 3. EVALUAR CORRELACIONES
    resultados["correlaciones"] = _evaluar_correlaciones(df_real, df_sintetico, columnas_numericas, columnas_categoricas)
    
    return resultados

def _validar_variables_numericas(df_real, df_sintetico, columnas_numericas):
    """Valida variables numéricas usando la prueba Kolmogorov-Smirnov"""
    print("\n--- Prueba Kolmogorov-Smirnov para variables numéricas ---")
    ks_results = {}
    
    # Filtrar columnas que existen en ambos dataframes
    cols_validas = [col for col in columnas_numericas if col in df_real.columns and col in df_sintetico.columns]
    
    for col in cols_validas:
        try:
            # Extraer series no nulas una sola vez para optimizar
            real_values = df_real[col].dropna().values
            sint_values = df_sintetico[col].dropna().values
            
            # Calcular estadísticas básicas
            real_stats = {
                "media": np.mean(real_values),
                "std": np.std(real_values),
                "min": np.min(real_values),
                "max": np.max(real_values)
            }
            
            sint_stats = {
                "media": np.mean(sint_values),
                "std": np.std(sint_values),
                "min": np.min(sint_values),
                "max": np.max(sint_values)
            }
            
            # Realizar prueba KS
            ks_stat, p_value = ks_2samp(real_values, sint_values)
            ks_results[col] = {
                "statistic": ks_stat, 
                "p-value": p_value,
                "real_stats": real_stats,
                "sint_stats": sint_stats
            }
            
            print(f"{col}: KS statistic={ks_stat:.4f}, p-value={p_value:.4f}")
            print(f"  Real - Media: {real_stats['media']:.2f}, Std: {real_stats['std']:.2f}, "
                  f"Min: {real_stats['min']:.2f}, Max: {real_stats['max']:.2f}")
            print(f"  Sint - Media: {sint_stats['media']:.2f}, Std: {sint_stats['std']:.2f}, "
                  f"Min: {sint_stats['min']:.2f}, Max: {sint_stats['max']:.2f}")
            
            # Interpretar resultado
            alpha = 0.05
            if p_value < alpha:
                print(f"  ⚠️ Las distribuciones son significativamente diferentes (p < {alpha})")
            else:
                print(f"  ✅ No se detectan diferencias significativas entre las distribuciones")
                
        except Exception as e:
            ks_results[col] = {"error": str(e)}
            print(f"❌ Error en prueba KS para {col}: {e}")
    
    return ks_results

def _validar_variables_categoricas(df_real, df_sintetico, columnas_categoricas):
    """Valida variables categóricas usando la prueba Chi-cuadrado"""
    print("\n--- Prueba Chi-cuadrado para variables categóricas ---")
    chi2_results = {}
    
    # Filtrar columnas que existen en ambos dataframes
    cols_validas = [col for col in columnas_categoricas if col in df_real.columns and col in df_sintetico.columns]
    
    for col in cols_validas:
        try:
            # Obtener todas las categorías posibles con operación de conjunto más eficiente
            all_categories = sorted(set(df_real[col].dropna()) | set(df_sintetico[col].dropna()))
            
            # Crear arrays para frecuencias (más eficiente que Series)
            real_freq = np.zeros(len(all_categories))
            sint_freq = np.zeros(len(all_categories))
            
            # Mapeo de categoría a índice
            cat_to_idx = {cat: idx for idx, cat in enumerate(all_categories)}
            
            # Calcular frecuencias de manera más eficiente
            real_counts = df_real[col].value_counts()
            sint_counts = df_sintetico[col].value_counts()
            
            for cat, count in real_counts.items():
                if cat in cat_to_idx:
                    real_freq[cat_to_idx[cat]] = count
                    
            for cat, count in sint_counts.items():
                if cat in cat_to_idx:
                    sint_freq[cat_to_idx[cat]] = count
            
            # Tabla de contingencia
            obs = np.vstack([real_freq, sint_freq])
            
            # Asegurar que los datos son válidos para la prueba
            if np.all(obs.sum(axis=0) > 0) and obs.shape[1] > 1:
                # Prueba Chi-cuadrado
                chi2, p, dof, expected = chi2_contingency(obs)
                chi2_results[col] = {"statistic": chi2, "p-value": p, "dof": dof}
                
                print(f"{col}: Chi2 statistic={chi2:.4f}, p-value={p:.4f}, df={dof}")
                
                # Calcular distribuciones en porcentaje para mostrar
                real_pct = 100 * real_freq / np.sum(real_freq) if np.sum(real_freq) > 0 else np.zeros_like(real_freq)
                sint_pct = 100 * sint_freq / np.sum(sint_freq) if np.sum(sint_freq) > 0 else np.zeros_like(sint_freq)
                
                # Mostrar las distribuciones más relevantes (top 5)
                relevance = (real_pct + sint_pct) / 2
                top_indices = np.argsort(relevance)[::-1][:min(5, len(all_categories))]
                
                print("  Distribuciones principales:")
                for idx in top_indices:
                    cat = all_categories[idx]
                    print(f"  {cat}: Real={real_pct[idx]:.1f}%, Sint={sint_pct[idx]:.1f}%, "
                          f"Diff={abs(real_pct[idx]-sint_pct[idx]):.1f}%")
                
                # Interpretar resultado
                alpha = 0.05
                if p < alpha:
                    print(f"  ⚠️ Las distribuciones son significativamente diferentes (p < {alpha})")
                else:
                    print(f"  ✅ No se detectan diferencias significativas entre las distribuciones")
            else:
                print(f"  ❌ No hay suficientes datos para realizar prueba Chi-cuadrado en {col}")
                chi2_results[col] = {"error": "Datos insuficientes para la prueba"}
        except Exception as e:
            chi2_results[col] = {"error": str(e)}
            print(f"❌ Error en prueba Chi2 para {col}: {e}")
    
    return chi2_results

def _evaluar_correlaciones(df_real, df_sintetico, columnas_numericas, columnas_categoricas):
    """Evalúa la preservación de correlaciones entre variables"""
    print("\n--- Evaluación de correlaciones ---")
    correlaciones = {"mae": None, "discrepancias": []}
    
    try:
        # Optimizar la preparación de datos para correlación
        df_real_corr, df_sint_corr = _preparar_datos_para_correlacion(
            df_real, df_sintetico, columnas_numericas, columnas_categoricas
        )
        
        # Columns para correlación (filtrar solo las disponibles)
        all_cols = [col for col in columnas_numericas + columnas_categoricas 
                    if col in df_real_corr.columns and col in df_sint_corr.columns]
        
        if len(all_cols) < 2:
            print("❌ Se requieren al menos 2 columnas para analizar correlaciones")
            return correlaciones
            
        # Calcular matrices de correlación eficientemente
        real_corr = df_real_corr[all_cols].corr(method='spearman').fillna(0)
        sint_corr = df_sint_corr[all_cols].corr(method='spearman').fillna(0)
        
        # Calcular error medio absoluto optimizado
        # Usamos la matriz de diferencias completa para evitar recálculos
        diff_matrix = np.abs(real_corr - sint_corr)
        mae = diff_matrix.mean().mean()
        correlaciones["mae"] = mae
        print(f"Error Absoluto Medio de correlaciones: {mae:.4f}")

        # Identificar las correlaciones con mayor discrepancia
        # Usar operación vectorizada para encontrar el percentil 90
        threshold = np.percentile(diff_matrix.values.flatten(), 90)
        
        print(f"\nCorrelaciones con mayor discrepancia (>{threshold:.2f}):")
        
        # Lista para almacenar discrepancias encontradas
        discrepancias = []
        
        # Solo procesamos la mitad triangular superior para evitar duplicados
        for i in range(len(all_cols)):
            for j in range(i + 1, len(all_cols)):
                if diff_matrix.iloc[i, j] > threshold:
                    var1, var2 = all_cols[i], all_cols[j]
                    diff = diff_matrix.iloc[i, j]
                    real_val = real_corr.iloc[i, j]
                    sint_val = sint_corr.iloc[i, j]
                    
                    discrepancias.append({
                        "var1": var1,
                        "var2": var2,
                        "real": real_val,
                        "sint": sint_val,
                        "diff": diff
                    })
                    
                    print(f"  {var1} - {var2}: "
                          f"Real={real_val:.2f}, "
                          f"Sint={sint_val:.2f}, "
                          f"Diff={diff:.2f}")
        
        correlaciones["discrepancias"] = discrepancias
        
        if mae < 0.15:
            print("\n✅ Las correlaciones se mantienen bien en general")
        elif mae < 0.25:
            print("\n⚠️ Las correlaciones muestran diferencias moderadas")
        else:
            print("\n❌ Las correlaciones muestran diferencias significativas")
            
    except Exception as e:
        correlaciones["error"] = str(e)
        print(f"❌ Error en evaluación de correlaciones: {e}")
        print(f"Detalles: {traceback.format_exc()}")
    
    return correlaciones

def _preparar_datos_para_correlacion(df_real, df_sintetico, columnas_numericas, columnas_categoricas):
    """Prepara los datos para calcular correlaciones codificando variables categóricas"""
    # Crear copias para no modificar los originales
    df_real_corr = df_real.copy()
    df_sint_corr = df_sintetico.copy()
    
    # Usar LabelEncoder por columna - más eficiente que OneHotEncoding para correlaciones
    for col in columnas_categoricas:
        if col != "Cantidad_Recursos" and col in df_real.columns and col in df_sintetico.columns:
            le = LabelEncoder()
            
            # Convertir ambos conjuntos a strings para garantizar compatibilidad
            real_values = df_real[col].astype(str).dropna().values
            sint_values = df_sintetico[col].astype(str).dropna().values
            
            # Combinar valores para garantizar el mismo encoding
            combined_values = np.concatenate([real_values, sint_values])
            le.fit(combined_values)
            
            # Transformar, preservando NaN
            df_real_corr[col] = df_real[col].astype(str).map(
                lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan
            )
            df_sint_corr[col] = df_sintetico[col].astype(str).map(
                lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan
            )
    
    return df_real_corr, df_sint_corr


def generar_graficos_comparativos(df_real, df_sintetico, columnas_numericas, columnas_categoricas):
    """
    Genera gráficos comparativos mejorados entre datos reales y sintéticos.
    
    Esta función crea visualizaciones para comparar las distribuciones y correlaciones
    entre los datos reales y los datos sintéticos generados, facilitando la validación
    visual de la calidad de los datos sintéticos.
    
    Args:
        df_real (pd.DataFrame): DataFrame con los datos originales
        df_sintetico (pd.DataFrame): DataFrame con los datos sintéticos
        columnas_numericas (list): Lista de columnas numéricas
        columnas_categoricas (list): Lista de columnas categóricas
        
    Returns:
        dict: Diccionario con rutas de los archivos generados
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    import os
    
    # Crear directorio para guardar gráficos si no existe
    output_dir = "graficos_comparativos"
    os.makedirs(output_dir, exist_ok=True)
    
    resultados = {
        'graficos_numericos': None,
        'graficos_categoricos': None,
        'matriz_correlacion': None
    }
    
    # 1. GRÁFICOS PARA VARIABLES NUMÉRICAS
    try:
        _generar_comparativas_numericas(
            df_real, df_sintetico, columnas_numericas, 
            os.path.join(output_dir, 'comparacion_distribuciones_numericas.png')
        )
        resultados['graficos_numericos'] = os.path.join(output_dir, 'comparacion_distribuciones_numericas.png')
    except Exception as e:
        print(f"Error al generar gráficos de variables numéricas: {e}")
    
    # 2. GRÁFICOS PARA VARIABLES CATEGÓRICAS
    try:
        _generar_comparativas_categoricas(
            df_real, df_sintetico, columnas_categoricas,
            os.path.join(output_dir, 'comparacion_distribuciones_categoricas.png')
        )
        resultados['graficos_categoricos'] = os.path.join(output_dir, 'comparacion_distribuciones_categoricas.png')
    except Exception as e:
        print(f"Error al generar gráficos de variables categóricas: {e}")
    
    # 3. MATRICES DE CORRELACIÓN
    try:
        _generar_matrices_correlacion(
            df_real, df_sintetico, columnas_numericas, columnas_categoricas,
            os.path.join(output_dir, 'comparacion_correlaciones.png')
        )
        resultados['matriz_correlacion'] = os.path.join(output_dir, 'comparacion_correlaciones.png')
    except Exception as e:
        print(f"Error al generar matrices de correlación: {e}")
    
    print(f"\nGráficos comparativos generados en el directorio: {output_dir}")
    return resultados

def _generar_comparativas_numericas(df_real, df_sintetico, columnas_numericas, ruta_salida):
    """Genera gráficos comparativos para variables numéricas"""
    import matplotlib.pyplot as plt
    import numpy as np
    import seaborn as sns
    
    # Filtrar columnas existentes en ambos dataframes
    columnas_validas = [col for col in columnas_numericas 
                         if col in df_real.columns and col in df_sintetico.columns]
    
    if not columnas_validas:
        print("No hay columnas numéricas válidas para comparar")
        return
        
    # Configurar layout óptimo
    n_cols = min(3, len(columnas_validas))
    n_rows = (len(columnas_validas) + n_cols - 1) // n_cols
    
    # Crear figura con tamaño adecuado
    fig = plt.figure(figsize=(15, n_rows * 4))
    
    # Mejorar estilo global
    plt.style.use('seaborn-v0_8-whitegrid')
    
    for i, col in enumerate(columnas_validas):
        ax = fig.add_subplot(n_rows, n_cols, i + 1)
        
        # Extraer datos no nulos una sola vez (eficiencia)
        real_values = df_real[col].dropna().values
        sint_values = df_sintetico[col].dropna().values
        
        # Calcular bins óptimos usando la regla de Freedman-Diaconis para ambos conjuntos
        all_values = np.concatenate([real_values, sint_values])
        
        if len(all_values) > 0:
            # Calcular rango
            data_range = np.max(all_values) - np.min(all_values)
            
            # Número de bins adaptativo
            if df_real[col].nunique() <= 10 and df_sintetico[col].nunique() <= 10:
                # Para variables discretas con pocos valores únicos, usar esos valores como bins
                bins = np.unique(np.concatenate([np.unique(real_values), np.unique(sint_values)]))
            else:
                # Para variables continuas, usar regla de Scott
                iqr = np.percentile(all_values, 75) - np.percentile(all_values, 25)
                if iqr == 0:  # Si IQR es cero, usar regla simple
                    bins = min(30, max(10, int(np.sqrt(len(all_values)))))
                else:
                    bin_width = 2 * iqr / (len(all_values) ** (1/3))
                    bins = max(10, min(50, int(data_range / bin_width)))
            
            # Histograma para datos reales
            sns.histplot(real_values, bins=bins, alpha=0.6, label='Real', 
                         kde=True, stat="density", color='blue', ax=ax)
            
            # Histograma para datos sintéticos
            sns.histplot(sint_values, bins=bins, alpha=0.6, label='Sintético', 
                         kde=True, stat="density", color='orange', ax=ax)
            
            # Añadir estadísticas a la leyenda
            ax.text(0.5, 0.97, 
                   f'Real: μ={np.mean(real_values):.2f}, σ={np.std(real_values):.2f}\n'
                   f'Sint: μ={np.mean(sint_values):.2f}, σ={np.std(sint_values):.2f}',
                   horizontalalignment='center', verticalalignment='top',
                   transform=ax.transAxes, fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
            
            ax.set_title(f'Distribución de {col}', fontsize=12, fontweight='bold')
            ax.legend()
            
            # Ajustar ejes para mejor visualización
            if data_range > 0:
                margin = data_range * 0.05
                ax.set_xlim([np.min(all_values) - margin, np.max(all_values) + margin])
    
    plt.tight_layout(pad=3.0)
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráficos comparativos de variables numéricas guardados como '{ruta_salida}'")

def _generar_comparativas_categoricas(df_real, df_sintetico, columnas_categoricas, ruta_salida):
    """Genera gráficos comparativos para variables categóricas"""
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    
    # Filtrar columnas existentes en ambos dataframes
    columnas_validas = [col for col in columnas_categoricas 
                        if col in df_real.columns and col in df_sintetico.columns]
    
    if not columnas_validas:
        print("No hay columnas categóricas válidas para comparar")
        return
    
    # Configurar layout óptimo
    n_cols = min(2, len(columnas_validas))
    n_rows = (len(columnas_validas) + n_cols - 1) // n_cols
    
    # Crear figura con tamaño adecuado
    fig = plt.figure(figsize=(15, n_rows * 5))
    
    # Mejorar estilo global
    plt.style.use('seaborn-v0_8-whitegrid')
    
    for i, col in enumerate(columnas_validas):
        ax = fig.add_subplot(n_rows, n_cols, i + 1)
        
        # Convertir categorías a strings para evitar problemas de comparación
        real_counts = df_real[col].astype(str).value_counts(normalize=True)
        sint_counts = df_sintetico[col].astype(str).value_counts(normalize=True)
        
        # Obtener todas las categorías únicas eficientemente
        all_cats = sorted(set(real_counts.index) | set(sint_counts.index))
        
        # Preparar datos para el gráfico de barras
        categories = []
        real_values = []
        sint_values = []
        
        for cat in all_cats:
            categories.append(cat)
            real_values.append(real_counts.get(cat, 0))
            sint_values.append(sint_counts.get(cat, 0))
        
        # Calcular ancho de barras adaptativo
        width = min(0.35, 0.8 / 2)  # Ajusta ancho según número de categorías
        x = np.arange(len(categories))
        
        # Crear gráfico de barras
        bars1 = ax.bar(x - width/2, real_values, width, label='Real', color='blue', alpha=0.7)
        bars2 = ax.bar(x + width/2, sint_values, width, label='Sintético', color='orange', alpha=0.7)
        
        # Añadir valores encima de las barras si hay pocas categorías
        if len(categories) <= 8:
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    if height >= 0.05:  # Solo mostrar etiquetas para valores significativos
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                                f'{height:.2f}', ha='center', va='bottom', 
                                fontsize=8, rotation=0)
        
        # Configurar ejes y leyendas
        ax.set_xlabel('Categoría', fontweight='bold')
        ax.set_ylabel('Frecuencia relativa', fontweight='bold')
        ax.set_title(f'Distribución de {col}', fontsize=12, fontweight='bold')
        
        # Rotar etiquetas para mejor legibilidad
        if len(categories) > 4:
            rotation = 45
            ha = 'right'
        else:
            rotation = 0
            ha = 'center'
            
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=rotation, ha=ha)
        
        # Añadir rejilla horizontal para mejor legibilidad
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.legend()
        
        # Calcular y mostrar la diferencia absoluta media
        diff = np.mean([abs(r - s) for r, s in zip(real_values, sint_values)])
        ax.text(0.5, 0.97, f'Diferencia media: {diff:.3f}',
                horizontalalignment='center', verticalalignment='top',
                transform=ax.transAxes, fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    plt.tight_layout(pad=3.0)
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráficos comparativos de variables categóricas guardados como '{ruta_salida}'")

def _generar_matrices_correlacion(df_real, df_sintetico, columnas_numericas, columnas_categoricas, ruta_salida):
    """Genera matrices de correlación comparativas"""
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    from sklearn.preprocessing import LabelEncoder
    import pandas as pd
    
    # Seleccionar columnas para la matriz de correlación
    all_cols = list(columnas_numericas) + [c for c in columnas_categoricas if c != "Cantidad_Recursos"]
    
    # Filtrar columnas existentes en ambos dataframes
    all_cols = [col for col in all_cols 
                if col in df_real.columns and col in df_sintetico.columns]
    
    if not all_cols:
        print("No hay suficientes columnas para generar matrices de correlación")
        return
    
    # Preparar dataframes para correlación
    df_real_corr = df_real[all_cols].copy()
    df_sint_corr = df_sintetico[all_cols].copy()
    
    # Codificar variables categóricas
    for col in all_cols:
        if col in columnas_categoricas:
            le = LabelEncoder()
            
            # Combinar valores de ambos dataframes para asegurar consistencia
            combined_values = pd.concat([
                df_real[col].astype(str).dropna(),
                df_sintetico[col].astype(str).dropna()
            ]).unique()
            
            le.fit(combined_values)
            
            # Transformar valores en los dataframes
            df_real_corr[col] = df_real[col].astype(str).apply(
                lambda x: le.transform([x])[0] if pd.notna(x) else np.nan
            )
            df_sint_corr[col] = df_sintetico[col].astype(str).apply(
                lambda x: le.transform([x])[0] if pd.notna(x) else np.nan
            )
    
    # Calcular matrices de correlación
    corr_real = df_real_corr.corr(method='spearman').fillna(0)
    corr_sint = df_sint_corr.corr(method='spearman').fillna(0)
    
    # Configurar figura
    fig, axes = plt.subplots(1, 3, figsize=(21, 7))
    
    # Configurar colormap efectivo
    cmap = 'coolwarm'
    
    # 1. Matriz de correlación real
    sns.heatmap(corr_real, annot=True, cmap=cmap, fmt='.2f', 
                square=True, linewidths=0.5, ax=axes[0], vmin=-1, vmax=1)
    axes[0].set_title('Correlaciones - Datos Reales', fontsize=14, fontweight='bold')
    
    # 2. Matriz de correlación sintética
    sns.heatmap(corr_sint, annot=True, cmap=cmap, fmt='.2f', 
                square=True, linewidths=0.5, ax=axes[1], vmin=-1, vmax=1)
    axes[1].set_title('Correlaciones - Datos Sintéticos', fontsize=14, fontweight='bold')
    
    # 3. Matriz de diferencias absolutas
    diff_matrix = np.abs(corr_real - corr_sint)
    im = sns.heatmap(diff_matrix, annot=True, cmap='Reds', fmt='.2f',
                square=True, linewidths=0.5, ax=axes[2], vmin=0, vmax=1)
    axes[2].set_title('Diferencias Absolutas', fontsize=14, fontweight='bold')
    
    # Mostrar colorbar con etiquetas claras
    cbar = im.collections[0].colorbar
    cbar.set_ticks([0, 0.25, 0.5, 0.75, 1])
    cbar.set_ticklabels(['0 (Igual)', '0.25', '0.5', '0.75', '1 (Diferente)'])
    
    # Mostrar error absoluto medio global
    mae = np.mean(diff_matrix)
    fig.suptitle(f'Comparación de Correlaciones (Error Abs. Medio: {mae:.4f})', 
                fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Matrices de correlación comparativas guardadas como '{ruta_salida}'")
    print(f"Error absoluto medio en correlaciones: {mae:.4f}")



def validar_correlaciones_criticas(df_real, df_sintetico, variables_criticas):
    """
    Valida específicamente las correlaciones entre variables críticas.
    
    Esta función analiza y compara las correlaciones entre variables críticas
    en los conjuntos de datos reales y sintéticos, permitiendo validar que las 
    relaciones importantes se han conservado en los datos generados.
    
    Args:
        df_real (pd.DataFrame): DataFrame con los datos originales reales
        df_sintetico (pd.DataFrame): DataFrame con los datos sintéticos generados
        variables_criticas (list): Lista de variables críticas a evaluar
        
    Returns:
        dict: Diccionario con los resultados de la validación
    """
    print("\n=== VALIDACIÓN DE CORRELACIONES CRÍTICAS ===")
    
    # Inicializar diccionario para almacenar resultados
    resultados = {
        "matrices_correlacion": {"real": None, "sintetico": None, "diferencia": None},
        "estadisticas_univariadas": {},
        "correlaciones_especificas": {},
        "discrepancias_principales": []
    }
    
    # 1. ANÁLISIS DE CORRELACIÓN GLOBAL
    # Optimización: Seleccionar solo las variables necesarias en lugar de copiar
    variables_existentes = [var for var in variables_criticas 
                          if var in df_real.columns and var in df_sintetico.columns]
    
    if len(variables_existentes) < 2:
        print("⚠️ Se requieren al menos 2 variables para analizar correlaciones.")
        return resultados
    
    # Preparar datos para correlación optimizada
    df_real_proc, df_sint_proc = _preparar_datos_para_validacion(
        df_real[variables_existentes], 
        df_sintetico[variables_existentes]
    )
    
    # Calcular matrices de correlación
    corr_real = df_real_proc.corr(method='spearman').fillna(0)
    corr_sint = df_sint_proc.corr(method='spearman').fillna(0)
    diff_matrix = np.abs(corr_real - corr_sint)
    
    # Guardar resultados
    resultados["matrices_correlacion"]["real"] = corr_real.to_dict()
    resultados["matrices_correlacion"]["sintetico"] = corr_sint.to_dict()
    resultados["matrices_correlacion"]["diferencia"] = diff_matrix.to_dict()
    
    # Calcular error absoluto medio
    mae = diff_matrix.values.mean()
    resultados["mae_correlaciones"] = mae
    
    # Imprimir resumen de correlaciones
    print("\n--- Resumen de correlaciones entre variables críticas ---")
    print(f"\n• Error absoluto medio en correlaciones: {mae:.4f}")
    
    # Formatear y mostrar matrices de correlación
    pd.set_option('display.precision', 2)
    print("\n• Matriz de correlación - DATOS REALES")
    print(corr_real.round(2))
    
    print("\n• Matriz de correlación - DATOS SINTÉTICOS")
    print(corr_sint.round(2))
    
    print("\n• Diferencias absolutas")
    print(diff_matrix.round(2))
    
    # 2. ESTADÍSTICAS DESCRIPTIVAS UNIVARIADAS
    print("\n--- Distribución de variables críticas ---")
    
    for var in variables_existentes:
        # Calcular estadísticas de forma vectorizada
        real_values = df_real[var].dropna()
        sint_values = df_sintetico[var].dropna()
        
        # Usar numpy para cálculos estadísticos más rápidos
        real_stats = {
            "n": len(real_values),
            "mean": np.mean(real_values),
            "std": np.std(real_values),
            "min": np.min(real_values) if len(real_values) > 0 else np.nan,
            "max": np.max(real_values) if len(real_values) > 0 else np.nan
        }
        
        sint_stats = {
            "n": len(sint_values),
            "mean": np.mean(sint_values),
            "std": np.std(sint_values),
            "min": np.min(sint_values) if len(sint_values) > 0 else np.nan,
            "max": np.max(sint_values) if len(sint_values) > 0 else np.nan
        }
        
        resultados["estadisticas_univariadas"][var] = {
            "real": real_stats,
            "sintetico": sint_stats
        }
        
        # Mostrar estadísticas
        print(f"\n• {var}:")
        print(f"  Real  - Media: {real_stats['mean']:.2f}, Std: {real_stats['std']:.2f}, "
              f"Min: {real_stats['min']:.2f}, Max: {real_stats['max']:.2f}, N: {real_stats['n']}")
        print(f"  Sint  - Media: {sint_stats['mean']:.2f}, Std: {sint_stats['std']:.2f}, "
              f"Min: {sint_stats['min']:.2f}, Max: {sint_stats['max']:.2f}, N: {sint_stats['n']}")
        
        # Para variables categóricas o discretas, mostrar frecuencias
        if var in ["Cantidad_Recursos", "Complejidad", "Experiencia_R1"] or min(df_real[var].nunique(), df_sintetico[var].nunique()) < 20:
            # Optimizado: Calcular frecuencias de una sola vez
            real_freq = df_real[var].value_counts(normalize=True).sort_index()
            sint_freq = df_sintetico[var].value_counts(normalize=True).sort_index()
            
            # Guardar frecuencias en resultados
            resultados["estadisticas_univariadas"][var]["frecuencias"] = {
                "real": real_freq.to_dict(),
                "sintetico": sint_freq.to_dict()
            }
            
            # Mostrar frecuencias de forma más compacta
            print("  Frecuencias:")
            
            # Obtener todas las categorías posibles
            all_cats = sorted(set(real_freq.index) | set(sint_freq.index))
            
            for cat in all_cats:
                real_pct = real_freq.get(cat, 0) * 100
                sint_pct = sint_freq.get(cat, 0) * 100
                diff_pct = abs(real_pct - sint_pct)
                
                print(f"    {cat}: Real={real_pct:.1f}%, Sint={sint_pct:.1f}%, Diff={diff_pct:.1f}%")
    
    # 3. CORRELACIONES ESPECÍFICAS
    print("\n--- Correlaciones específicas identificadas como críticas ---")
    
    # Definir pares críticos con prioridad
    correlaciones_especificas = [
        ("Complejidad", "Fase_Tarea"),
        ("Carga_Trabajo_R1", "Cantidad_Recursos"),
        ("Experiencia_R1", "Tipo_Tarea"),
        ("Experiencia_Equipo", "Cantidad_Recursos"),
        ("Tamaño_Tarea", "Carga_Trabajo_R1"),
        ("Tiempo_Ejecucion", "Cantidad_Recursos")
    ]
    
    # Diccionario para reutilizar encoders
    encoders = {}
    resultados["correlaciones_especificas"] = {}
    
    # Variables categóricas que necesitan ser codificadas
    categorical_vars = ["Fase_Tarea", "Tipo_Tarea"]
    
    # Pre-codificar variables categóricas (una sola vez)
    for var in categorical_vars:
        if var in df_real.columns and var in df_sintetico.columns:
            # Crear y almacenar encoder
            le = LabelEncoder()
            combined_values = list(set(
                df_real[var].astype(str).dropna().tolist() + 
                df_sintetico[var].astype(str).dropna().tolist()
            ))
            le.fit(combined_values)
            encoders[var] = le
    
    # Analizar cada par crítico
    for var1, var2 in correlaciones_especificas:
        # Verificar que ambas variables existan
        if var1 not in df_real.columns or var2 not in df_real.columns or \
           var1 not in df_sintetico.columns or var2 not in df_sintetico.columns:
            print(f"  ❌ {var1} - {var2}: Variables no disponibles en los datos")
            continue
        
        # Crear copias temporales solo para las columnas necesarias (evitar copia completa)
        df_real_temp = df_real[[var1, var2]].copy()
        df_sint_temp = df_sintetico[[var1, var2]].copy()
        
        # Codificar variables categóricas si es necesario
        for var in [var1, var2]:
            if var in categorical_vars:
                # Usar encoder pre-calculado
                le = encoders.get(var)
                if le:
                    # Convertir a string y transformar vectorialmente
                    df_real_temp[var] = df_real_temp[var].astype(str).apply(
                        lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan
                    )
                    df_sint_temp[var] = df_sint_temp[var].astype(str).apply(
                        lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan
                    )
        
        try:
            # Calcular correlaciones de forma optimizada
            corr_real = df_real_temp.corr(method='spearman').iloc[0, 1]
            corr_sint = df_sint_temp.corr(method='spearman').iloc[0, 1]
            diff = abs(corr_real - corr_sint)
            
            resultados["correlaciones_especificas"][f"{var1}_{var2}"] = {
                "real": corr_real,
                "sintetico": corr_sint,
                "diferencia": diff
            }
            
            # Clasificar la calidad del ajuste
            calidad = "✅ Excelente" if diff < 0.05 else ("⚠️ Regular" if diff < 0.15 else "❌ Deficiente")
            
            print(f"  {calidad} | {var1} - {var2}: Real={corr_real:.2f}, Sint={corr_sint:.2f}, Diff={diff:.2f}")
            
            # Agregar a discrepancias principales si la diferencia es grande
            if diff >= 0.15:
                resultados["discrepancias_principales"].append({
                    "var1": var1, 
                    "var2": var2, 
                    "diff": diff,
                    "real": corr_real,
                    "sint": corr_sint
                })
                
        except Exception as e:
            print(f"  ❌ Error al calcular correlación entre {var1} y {var2}: {e}")
            resultados["correlaciones_especificas"][f"{var1}_{var2}"] = {"error": str(e)}
    
    # 4. RESUMEN FINAL
    print("\n--- Resumen de la validación ---")
    
    # Calcular puntuación global (0-100)
    discrepancias = resultados.get("discrepancias_principales", [])
    num_pares_analizados = len(resultados["correlaciones_especificas"])
    
    if num_pares_analizados > 0:
        score = 100 * (1 - len(discrepancias) / num_pares_analizados) * (1 - min(mae, 0.5) / 0.5)
        resultados["score"] = score
        
        # Mostrar resultado final con evaluación cualitativa
        if score >= 90:
            print(f"Puntuación general: {score:.1f}/100 - ✅ Excelente conservación de correlaciones críticas")
        elif score >= 75:
            print(f"Puntuación general: {score:.1f}/100 - ✅ Buena conservación de correlaciones críticas")
        elif score >= 60:
            print(f"Puntuación general: {score:.1f}/100 - ⚠️ Conservación aceptable de correlaciones críticas")
        else:
            print(f"Puntuación general: {score:.1f}/100 - ❌ Deficiente conservación de correlaciones críticas")
    
    if discrepancias:
        print("\n• Correlaciones críticas con problemas:")
        for d in sorted(discrepancias, key=lambda x: x["diff"], reverse=True):
            print(f"  → {d['var1']} - {d['var2']}: Diferencia {d['diff']:.2f} (Real={d['real']:.2f}, Sint={d['sint']:.2f})")
    else:
        print("\n• Todas las correlaciones críticas están bien preservadas")
    
    print("\n=== FIN DE VALIDACIÓN DE CORRELACIONES CRÍTICAS ===")
    return resultados

def _preparar_datos_para_validacion(df_real, df_sint):
    """
    Prepara los datos para la validación de correlaciones.
    
    Esta función auxiliar procesa los dataframes para asegurar que las variables categóricas
    estén correctamente codificadas para el cálculo de correlaciones.
    
    Args:
        df_real (pd.DataFrame): DataFrame con datos reales (solo columnas relevantes)
        df_sint (pd.DataFrame): DataFrame con datos sintéticos (solo columnas relevantes)
        
    Returns:
        tuple: Par de DataFrames procesados (real, sintético)
    """
    # Crear copias superficiales (solo referencias - más eficiente)
    df_real_proc = df_real.copy(deep=False)
    df_sint_proc = df_sint.copy(deep=False)
    
    # Identificar columnas categóricas
    categorical_cols = []
    for col in df_real.columns:
        if df_real[col].dtype == 'object' or df_sint[col].dtype == 'object' or \
           (col in ["Fase_Tarea", "Tipo_Tarea"]):
            categorical_cols.append(col)
    
    # Codificar variables categóricas
    for col in categorical_cols:
        if col != "Cantidad_Recursos":  # Esta ya suele ser numérica
            # Crea un encoder común para ambos conjuntos
            le = LabelEncoder()
            combined_values = list(set(
                df_real[col].astype(str).dropna().tolist() + 
                df_sint[col].astype(str).dropna().tolist()
            ))
            le.fit(combined_values)
            
            # Transformar ambos conjuntos con el mismo encoder
            df_real_proc[col] = df_real[col].astype(str).map(
                lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan
            )
            df_sint_proc[col] = df_sint[col].astype(str).map(
                lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan
            )
    
    return df_real_proc, df_sint_proc


def validar_distribucion_conjunta(df_real, df_sintetico, pares_variables):
    """
    Valida la distribución conjunta entre pares de variables para verificar
    que las relaciones se mantienen en los datos sintéticos.
    
    Esta función analiza pares de variables específicos para validar que sus 
    distribuciones conjuntas se mantienen de forma similar entre los datos 
    reales y sintéticos, usando pruebas estadísticas específicas según el tipo de variables.
    
    Args:
        df_real (pd.DataFrame): DataFrame con los datos originales
        df_sintetico (pd.DataFrame): DataFrame con los datos sintéticos
        pares_variables (list): Lista de tuplas (var1, var2) con pares de variables a analizar
        
    Returns:
        dict: Resultados de validación para cada par de variables
    """
    import numpy as np
    import pandas as pd
    from scipy.stats import chi2_contingency
    
    # Inicializar diccionario para almacenar resultados
    resultados = {}
    
    for var1, var2 in pares_variables:
        print(f"\n=== Distribución conjunta de {var1} y {var2} ===")
        
        # Verificar existencia de variables en ambos dataframes
        if var1 not in df_real.columns or var2 not in df_real.columns or \
           var1 not in df_sintetico.columns or var2 not in df_sintetico.columns:
            print(f"❌ El par de variables {var1}-{var2} no está disponible en ambos datasets")
            resultados[f"{var1}_{var2}"] = {"error": "Variables no disponibles"}
            continue
        
        # Preparar contenedor para resultados del par actual
        par_resultados = {
            "tipo_analisis": None,
            "diferencia_media": None,
            "chi2": None,
            "p_valor": None,
            "dist_real": None,
            "dist_sintetica": None
        }
        
        # Analizar según el tipo de variables (numéricas o categóricas)
        ambas_numericas = _son_ambas_numericas(df_real, df_sintetico, var1, var2)
        
        if ambas_numericas:
            par_resultados["tipo_analisis"] = "numéricas"
            # Analizar variables numéricas
            _analizar_numericas(df_real, df_sintetico, var1, var2, par_resultados)
        else:
            par_resultados["tipo_analisis"] = "categóricas"
            # Analizar variables con al menos una categórica
            _analizar_categoricas(df_real, df_sintetico, var1, var2, par_resultados)
        
        # Evaluar y mostrar conclusión
        if par_resultados["p_valor"] is not None:
            if par_resultados["p_valor"] < 0.05:
                print("⚠️ Las distribuciones conjuntas son significativamente diferentes (p < 0.05)")
                par_resultados["conclusion"] = "diferentes"
            else:
                print("✅ No hay diferencias significativas entre las distribuciones conjuntas")
                par_resultados["conclusion"] = "similares"
                
        # Evaluar por diferencia media si no hay p-valor
        elif par_resultados["diferencia_media"] is not None:
            if par_resultados["diferencia_media"] < 0.1:
                print(f"✅ Distribuciones similares (diferencia media: {par_resultados['diferencia_media']:.4f})")
                par_resultados["conclusion"] = "similares"
            elif par_resultados["diferencia_media"] < 0.2:
                print(f"⚠️ Distribuciones moderadamente diferentes (diferencia media: {par_resultados['diferencia_media']:.4f})")
                par_resultados["conclusion"] = "moderadamente_diferentes"
            else:
                print(f"❌ Distribuciones muy diferentes (diferencia media: {par_resultados['diferencia_media']:.4f})")
                par_resultados["conclusion"] = "muy_diferentes"
                
        # Guardar resultados
        resultados[f"{var1}_{var2}"] = par_resultados
    
    return resultados

def _son_ambas_numericas(df_real, df_sintetico, var1, var2):
    """Determina si ambas variables son numéricas en ambos dataframes"""
    return (var1 in df_real.select_dtypes(include=[np.number]).columns and 
            var2 in df_real.select_dtypes(include=[np.number]).columns and
            var1 in df_sintetico.select_dtypes(include=[np.number]).columns and 
            var2 in df_sintetico.select_dtypes(include=[np.number]).columns)

def _analizar_numericas(df_real, df_sintetico, var1, var2, resultados):
    """Analiza distribuciones conjuntas de variables numéricas"""
    try:
        # 1. Crear tablas de contingencia con binning adecuado (optimización)
        bins1 = _determinar_bins_optimos(df_real[var1], df_sintetico[var1])
        bins2 = _determinar_bins_optimos(df_real[var2], df_sintetico[var2])
        
        # 2. Crear tablas de contingencia (sin copiar datos)
        table_real = pd.crosstab(
            pd.cut(df_real[var1], bins=bins1),
            pd.cut(df_real[var2], bins=bins2), 
            normalize=True
        )
        
        table_sint = pd.crosstab(
            pd.cut(df_sintetico[var1], bins=bins1),
            pd.cut(df_sintetico[var2], bins=bins2), 
            normalize=True
        )
        
        # 3. Calcular diferencias eficientemente
        diferencia = _calcular_diferencia_tablas(table_real, table_sint)
        resultados["diferencia_media"] = diferencia
        
        # 4. Mostrar resumen
        print(f"\n• Diferencia absoluta media en distribución conjunta: {diferencia:.4f}")
        
        # 5. Hacer prueba Chi-cuadrado para validación estadística
        resultados["chi2"], resultados["p_valor"] = _realizar_chi2(table_real, table_sint)
        print(f"• Prueba Chi-cuadrado: chi2={resultados['chi2']:.4f}, p-value={resultados['p_valor']:.4f}")
        
        # 6. Guardar distribuciones resumidas
        resultados["dist_real"] = _resumir_distribucion(table_real)
        resultados["dist_sintetica"] = _resumir_distribucion(table_sint)
        
    except Exception as e:
        print(f"❌ Error al analizar distribución conjunta numérica: {e}")
        resultados["error"] = str(e)

def _analizar_categoricas(df_real, df_sintetico, var1, var2, resultados):
    """Analiza distribuciones conjuntas cuando al menos una variable es categórica"""
    try:
        # 1. Convertir categóricas a string de forma eficiente
        df_real_temp = pd.DataFrame()
        df_sint_temp = pd.DataFrame()
        
        # Optimización: procesar datos sin copiar el dataframe entero
        for var, es_categorica in [(var1, not pd.api.types.is_numeric_dtype(df_real[var1])), 
                                  (var2, not pd.api.types.is_numeric_dtype(df_real[var2]))]:
            if es_categorica:
                df_real_temp[var] = df_real[var].astype(str)
                df_sint_temp[var] = df_sintetico[var].astype(str)
            else:
                # 2. Si es numérica, aplicar bins óptimos
                bins = _determinar_bins_optimos(df_real[var], df_sintetico[var])
                df_real_temp[var] = pd.cut(df_real[var], bins=bins)
                df_sint_temp[var] = pd.cut(df_sintetico[var], bins=bins)
        
        # 3. Crear tablas de contingencia
        table_real = pd.crosstab(df_real_temp[var1], df_real_temp[var2], normalize=True)
        table_sint = pd.crosstab(df_sint_temp[var1], df_sint_temp[var2], normalize=True)
        
        # 4. Calcular diferencia media absoluta
        diferencia = _calcular_diferencia_tablas(table_real, table_sint)
        resultados["diferencia_media"] = diferencia
        
        print(f"\n• Diferencia absoluta media en distribución conjunta: {diferencia:.4f}")
        
        # 5. Realizar prueba Chi-cuadrado de forma eficiente
        resultados["chi2"], resultados["p_valor"] = _realizar_chi2(table_real, table_sint)
        print(f"• Prueba Chi-cuadrado: chi2={resultados['chi2']:.4f}, p-value={resultados['p_valor']:.4f}")
        
        # 6. Guardar distribuciones resumidas
        resultados["dist_real"] = _resumir_distribucion(table_real)
        resultados["dist_sintetica"] = _resumir_distribucion(table_sint)
        
    except Exception as e:
        print(f"❌ Error al analizar distribución conjunta categórica: {e}")
        resultados["error"] = str(e)

def _determinar_bins_optimos(serie_real, serie_sint):
    """Determina el número óptimo de bins para discretizar variables numéricas"""
    # Combinar datos para análisis unificado
    todos_valores = np.concatenate([serie_real.dropna().values, serie_sint.dropna().values])
    
    if len(todos_valores) <= 1:
        return 2  # Mínimo de bins en casos extremos
        
    n_unique = np.unique(todos_valores).size
    
    # Si hay pocos valores únicos, usar cada valor único como bin
    if n_unique <= 10:
        return np.unique(todos_valores)
        
    # Calcular número de bins con regla de Sturges mejorada
    n = len(todos_valores)
    bins_sturges = max(5, min(20, int(np.ceil(np.log2(n) + 1))))
    
    # Para datasets grandes, usar regla de Freedman-Diaconis
    if n >= 1000:
        q75, q25 = np.percentile(todos_valores, [75, 25])
        iqr = q75 - q25
        if iqr > 0:
            bin_width = 2 * iqr / (n ** (1/3))
            data_range = np.max(todos_valores) - np.min(todos_valores)
            bins_fd = max(5, min(50, int(np.ceil(data_range / bin_width))))
            return bins_fd
            
    return bins_sturges

def _calcular_diferencia_tablas(table1, table2):
    """Calcula la diferencia media absoluta entre dos tablas de contingencia de forma eficiente"""
    # Crear índices y columnas unificados
    all_idx = sorted(set(table1.index) | set(table2.index))
    all_cols = sorted(set(table1.columns) | set(table2.columns))
    
    # Crear DataFrames completos rellenados con ceros (más eficiente)
    table1_full = pd.DataFrame(0, index=all_idx, columns=all_cols)
    table2_full = pd.DataFrame(0, index=all_idx, columns=all_cols)
    
    # Rellenar valores existentes (vectorizado)
    table1_full.update(table1)
    table2_full.update(table2)
    
    # Calcular diferencia absoluta media usando operaciones vectorizadas
    return np.abs(table1_full - table2_full).mean().mean()

def _realizar_chi2(table1, table2):
    """Realiza la prueba chi-cuadrado entre dos tablas de contingencia"""
    try:
        # 1. Convertir tablas a formato aplanado para chi2_contingency
        flat_data = []
        
        # Usar técnica de stack-unstack para alinear estructuras
        all_idx = sorted(set(table1.index) | set(table2.index))
        all_cols = sorted(set(table1.columns) | set(table2.columns))
        
        # Crear tablas completas con índices y columnas idénticos
        t1_aligned = pd.DataFrame(0, index=all_idx, columns=all_cols)
        t2_aligned = pd.DataFrame(0, index=all_idx, columns=all_cols)
        
        # Actualizar con valores reales (más eficiente que remapping)
        t1_aligned.update(table1)
        t2_aligned.update(table2)
        
        # Convertir a formato necesario para chi2_contingency
        t1_values = t1_aligned.values.flatten() * 1000  # Multiplicar para evitar problemas numéricos
        t2_values = t2_aligned.values.flatten() * 1000
        
        # Verificar validez para prueba chi-cuadrado
        if np.sum(t1_values) > 0 and np.sum(t2_values) > 0:
            chi2, p, _, _ = chi2_contingency([t1_values, t2_values])
            return chi2, p
    except Exception as e:
        print(f"  Advertencia en prueba chi-cuadrado: {e}")
    
    # Valores predeterminados si falla
    return None, None

def _resumir_distribucion(tabla):
    """Genera un resumen de la distribución para almacenar en resultados"""
    # Extraer elementos más significativos
    datos_planos = tabla.unstack()
    top_valores = datos_planos.sort_values(ascending=False).head(8)
    
    # Convertir a diccionario con formato legible
    resumen = {}
    for (idx1, idx2), valor in top_valores.items():
        resumen[f"{idx1},{idx2}"] = round(valor, 4)
        
    return resumen



# Ejemplo de uso
if __name__ == "__main__":
    generar_datos_monte_carlo("E:/Tesis/APP_2.0/estimacion_tiempos_2k.csv", 20000, "datos_sinteticos_version_2.csv")
