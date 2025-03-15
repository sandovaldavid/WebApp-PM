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


def generar_datos_monte_carlo(
    csv_path, n_samples=1000, output_path="datos_sinteticos.csv"
):
    """
    Genera datos sintéticos para el entrenamiento de redes neuronales de estimación de tiempos
    en proyectos de software mediante un enfoque de Monte Carlo mejorado.

    Este método preserva las correlaciones entre variables y asegura la coherencia de los datos
    para proporcionar un conjunto de entrenamiento robusto para la red neuronal.

    Args:
        csv_path (str): Ruta al archivo CSV con datos reales
        n_samples (int): Número de muestras sintéticas a generar
        output_path (str): Ruta donde guardar el archivo CSV con datos sintéticos
    """
    # Cargar el archivo CSV
    df = pd.read_csv(csv_path, encoding='latin-1')

    # Corregir el nombre de la columna si es necesario
    if "TamaÃ±o_Tarea" in df.columns:
        df.rename(columns={"TamaÃ±o_Tarea": "Tamaño_Tarea"}, inplace=True)

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

    # Eliminar outliers para mejorar la calidad del KDE
    df_clean = eliminar_outliers(df, numeric_cols, threshold=3)

    # Estandarizar tipos de datos categóricos para evitar problemas de mezcla de tipos
    for col in categorical_cols:
        if col != "Cantidad_Recursos":  # Cantidad_Recursos ya es numérica
            df_clean[col] = df_clean[col].astype(str)

    # Crear diccionario para almacenar los KDEs con bandwidth óptimo
    kdes = {}
    for col in numeric_cols:
        # Usar Scott's rule para bandwidth óptimo
        kdes[col] = gaussian_kde(df_clean[col].dropna(), bw_method='scott')

    # Analizar distribuciones de variables categóricas
    cat_distributions = {}
    for col in categorical_cols:
        cat_distributions[col] = df_clean[col].value_counts(normalize=True)

    # Análisis de probabilidades condicionales más detallado
    conditional_distributions = analizar_probabilidades_condicionales(
        df_clean, categorical_cols, numeric_cols
    )

    # Preparar datos para preservar correlaciones
    df_corr = df_clean.copy()
    encoders = {}

    for col in categorical_cols:
        if col != "Cantidad_Recursos":  # Cantidad_Recursos ya es numérica
            encoders[col] = LabelEncoder()
            df_corr[col] = encoders[col].fit_transform(df_corr[col])

    # Calcular matriz de correlación incluyendo todas las variables
    all_cols = numeric_cols + categorical_cols
    corr_matrix = df_corr[all_cols].corr()

    # Extraer valores únicos de Tamaño_Tarea de los datos reales para limitar los sintéticos
    tamanos_reales = sorted(df_clean["Tamaño_Tarea"].unique())
    print(f"Valores únicos de Tamaño_Tarea en datos reales: {tamanos_reales}")

    # Extraer la distribución real de Cantidad_Recursos
    dist_real_recursos = (
        df_clean["Cantidad_Recursos"].value_counts(normalize=True).to_dict()
    )
    print(f"Distribución real de Cantidad_Recursos: {dist_real_recursos}")

    # Extraer correlaciones críticas
    correlaciones_criticas = {
        "Complejidad-Fase_Tarea": df_corr[["Complejidad", "Fase_Tarea"]]
        .corr()
        .iloc[0, 1],
        "Carga_Trabajo_R1-Cantidad_Recursos": df_corr[
            ["Carga_Trabajo_R1", "Cantidad_Recursos"]
        ]
        .corr()
        .iloc[0, 1],
        "Experiencia_R1-Tipo_Tarea": df_corr[["Experiencia_R1", "Tipo_Tarea"]]
        .corr()
        .iloc[0, 1],
        "Experiencia_Equipo-Cantidad_Recursos": df_corr[
            ["Experiencia_Equipo", "Cantidad_Recursos"]
        ]
        .corr()
        .iloc[0, 1],
        "Tiempo_Ejecucion-Cantidad_Recursos": df_corr[
            ["Tiempo_Ejecucion", "Cantidad_Recursos"]
        ]
        .corr()
        .iloc[0, 1],
        "Tamaño_Tarea-Carga_Trabajo_R1": df_corr[["Tamaño_Tarea", "Carga_Trabajo_R1"]]
        .corr()
        .iloc[0, 1],
        "Carga_Trabajo_R1-Experiencia_Equipo": df_corr[
            ["Carga_Trabajo_R1", "Experiencia_Equipo"]
        ]
        .corr()
        .iloc[0, 1],
    }
    print("Correlaciones críticas en datos reales:", correlaciones_criticas)

    # Informar más detalladamente sobre las correlaciones críticas
    print("\n=== Correlaciones críticas objetivo ===")
    for key, value in correlaciones_criticas.items():
        print(f"{key}: {value:.4f}")

    # Generar datos sintéticos utilizando un enfoque basado en Cópulas con parámetros mejorados
    synthetic_data = generar_datos_con_copulas(
        df_clean,
        n_samples,
        numeric_cols,
        categorical_cols,
        cat_distributions,
        kdes,
        conditional_distributions,
        encoders,
        corr_matrix,
        tamanos_reales,
        dist_real_recursos,
        correlaciones_criticas,
    )

    # Crear DataFrame con los datos generados
    synthetic_df = pd.DataFrame(synthetic_data)

    # Validar los datos sintéticos con pruebas estadísticas rigurosas
    validar_datos_sinteticos(df_clean, synthetic_df, numeric_cols, categorical_cols)

    # Calcular intervalos de confianza
    confidence_interval = np.percentile(synthetic_df["Tiempo_Ejecucion"], [2.5, 97.5])
    print(
        f"Intervalo de confianza del 95% para Tiempo_Ejecucion: {confidence_interval}"
    )

    # Guardar en un archivo CSV
    synthetic_df.to_csv(output_path, index=False)
    print(f"Datos sintéticos guardados en {output_path}")

    # Generar gráficos comparativos para la documentación
    generar_graficos_comparativos(
        df_clean, synthetic_df, numeric_cols, categorical_cols
    )

    # Después de generar los datos, realizamos una validación adicional específica
    print("\n=== VALIDACIÓN ESPECÍFICA DE CORRELACIONES CRÍTICAS ===")
    validar_correlaciones_criticas(
        df_clean,
        synthetic_df,
        ["Complejidad", "Tamaño_Tarea", "Cantidad_Recursos", "Experiencia_R1"],
    )

    # Validación adicional de la distribución conjunta
    print("\n=== Validación de la distribución conjunta ===")
    validar_distribucion_conjunta(
        df_clean,
        synthetic_df,
        [
            ("Carga_Trabajo_R1", "Cantidad_Recursos"),
            ("Experiencia_R1", "Tipo_Tarea"),
            ("Complejidad", "Fase_Tarea"),
        ],
    )

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
    """Analiza las probabilidades condicionales entre variables para mejorar la coherencia"""
    conditional_distributions = {}

    # Probabilidades condicionales entre variables categóricas
    for i, cat1 in enumerate(categorical_cols):
        for j, cat2 in enumerate(categorical_cols):
            if i < j:  # Evitar duplicación
                # Crear tabla de contingencia normalizada
                cont_table = pd.crosstab(df[cat1], df[cat2], normalize='index')
                conditional_distributions[f"{cat2}|{cat1}"] = cont_table

    # Probabilidades condicionales para variables numéricas dadas categóricas
    for cat_col in categorical_cols:
        for num_col in numeric_cols:
            # Para cada categoría, calcular distribución de la variable numérica
            grouped = df.groupby(cat_col)[num_col].apply(list).to_dict()

            # Crear KDE para cada grupo
            kde_dict = {}
            for cat, values in grouped.items():
                if len(values) > 10:  # Suficientes datos para KDE
                    try:
                        kde_dict[cat] = gaussian_kde(values, bw_method='scott')
                    except:
                        # En caso de error, usar distribución general
                        kde_dict[cat] = None

            conditional_distributions[f"{num_col}|{cat_col}"] = kde_dict

    # Discretizar variables numéricas para calcular probabilidades condicionales
    # entre numéricas y categóricas
    for num_col in numeric_cols:
        # Discretizar en 5 bins
        bins = 5
        df[f"{num_col}_bin"] = pd.qcut(
            df[num_col], q=bins, labels=False, duplicates='drop'
        )

        for cat_col in categorical_cols:
            # Tabla de contingencia normalizada
            cont_table = pd.crosstab(
                df[f"{num_col}_bin"], df[cat_col], normalize='index'
            )
            conditional_distributions[f"{cat_col}|{num_col}_bin"] = cont_table

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


def generar_datos_con_copulas(
    df,
    n_samples,
    numeric_cols,
    categorical_cols,
    cat_distributions,
    kdes,
    cond_dists,
    encoders,
    corr_matrix,
    tamanos_reales,
    dist_real_recursos,
    correlaciones_criticas,
):
    """Genera datos sintéticos preservando correlaciones mediante cópulas gaussianas"""
    synthetic_data = []

    # Obtener matriz de correlación completa para todas las variables
    all_cols = numeric_cols + categorical_cols

    # 1. Generar datos numéricos correlacionados utilizando descomposición de Cholesky con correlación mejorada
    numeric_data = generar_datos_numericos_correlacionados(
        df, n_samples, numeric_cols, corr_matrix, kdes
    )

    # Asegurar que usamos exclusivamente los valores reales de Tamaño_Tarea
    # No generamos secuencia de Fibonacci, sino que usamos los valores reales observados

    # Calcular la distribución empírica de Tamaño_Tarea en datos reales
    tamano_counts = df["Tamaño_Tarea"].value_counts(normalize=True).to_dict()

    # Analizar distribuciones condicionales de Fase_Tarea según Complejidad
    fase_por_complejidad = {}
    for comp in range(1, 6):
        mask = (df["Complejidad"] >= comp - 0.5) & (df["Complejidad"] < comp + 0.5)
        if sum(mask) > 0:
            fase_por_complejidad[comp] = (
                df.loc[mask, "Fase_Tarea"].value_counts(normalize=True).to_dict()
            )

    # Analizar distribuciones condicionales de Tipo_Tarea según Experiencia_R1
    tipo_por_experiencia = {}
    for exp in range(1, 6):
        mask = (df["Experiencia_R1"] >= exp - 0.5) & (df["Experiencia_R1"] < exp + 0.5)
        if sum(mask) > 0:
            tipo_por_experiencia[exp] = (
                df.loc[mask, "Tipo_Tarea"].value_counts(normalize=True).to_dict()
            )

    # Extraer información sobre relaciones críticas
    relacion_carga_recursos = correlaciones_criticas.get(
        "Carga_Trabajo_R1-Cantidad_Recursos", 0.15
    )
    relacion_experiencia_tipo = correlaciones_criticas.get(
        "Experiencia_R1-Tipo_Tarea", 0.12
    )
    relacion_complejidad_fase = correlaciones_criticas.get(
        "Complejidad-Fase_Tarea", 0.10
    )
    relacion_tiempo_recursos = correlaciones_criticas.get(
        "Tiempo_Ejecucion-Cantidad_Recursos", 0.11
    )

    # Cargar más correlaciones críticas adicionales para mejorar la generación
    relacion_tiempo_carga = correlaciones_criticas.get(
        "Tiempo_Ejecucion-Carga_Trabajo_R1", -0.04
    )
    relacion_carga_experiencia = correlaciones_criticas.get(
        "Carga_Trabajo_R1-Experiencia_Equipo", 0.16
    )
    relacion_claridad_recursos = correlaciones_criticas.get(
        "Claridad_Requisitos-Cantidad_Recursos", -0.09
    )
    relacion_tamano_carga = correlaciones_criticas.get(
        "Tamaño_Tarea-Carga_Trabajo_R1", 0.12
    )  # Añadir esta correlación clave

    # Guardar la distribución original de Carga_Trabajo_R1 para preservar la variabilidad
    carga_trabajo_std_real = df["Carga_Trabajo_R1"].std()
    print(f"Desviación estándar real de Carga_Trabajo_R1: {carga_trabajo_std_real:.2f}")

    # Registrar la distribución de Complejidad para asegurar representación correcta
    complejidad_dist_real = df["Complejidad"].value_counts(normalize=True).to_dict()
    print(f"Distribución real de Complejidad: {complejidad_dist_real}")

    # Ajustar un modelo de regresión lineal para preservar mejor las correlaciones
    # Especialmente importante para Carga_Trabajo_R1 y Cantidad_Recursos
    modelo_carga_recursos = None
    modelo_tamano_carga = None  # Nuevo modelo para Tamaño_Tarea y Carga_Trabajo_R1
    modelo_carga_experiencia = (
        None  # Modelo específico para Carga_Trabajo_R1 y Experiencia_Equipo
    )
    modelo_tiempo_recursos = (
        None  # Modelo específico para Tiempo_Ejecucion y Cantidad_Recursos
    )

    if "Carga_Trabajo_R1" in df.columns and "Cantidad_Recursos" in df.columns:
        # Analizar la distribución condicional real para entender la relación
        carga_por_recursos = {}
        for cant in sorted(df["Cantidad_Recursos"].unique()):
            mask = df["Cantidad_Recursos"] == cant
            if sum(mask) > 0:
                carga_por_recursos[cant] = {
                    "mean": df.loc[mask, "Carga_Trabajo_R1"].mean(),
                    "median": df.loc[mask, "Carga_Trabajo_R1"].median(),
                    "std": df.loc[mask, "Carga_Trabajo_R1"].std(),
                    "dist": df.loc[mask, "Carga_Trabajo_R1"]
                    .value_counts(normalize=True)
                    .to_dict(),
                }
                print(
                    f"Distribución real para {cant} recursos: media={carga_por_recursos[cant]['mean']:.2f}, mediana={carga_por_recursos[cant]['median']}, std={carga_por_recursos[cant]['std']:.2f}"
                )

        # Construir modelo asegurando la correlación correcta
        X = df[["Cantidad_Recursos"]].values.reshape(-1, 1)
        y = df["Carga_Trabajo_R1"].values
        modelo_carga_recursos = LinearRegression()
        modelo_carga_recursos.fit(X, y)
        print(
            f"Modelo Carga_Trabajo_R1 ~ Cantidad_Recursos: coef={modelo_carga_recursos.coef_[0]:.6f}, intercept={modelo_carga_recursos.intercept_:.4f}"
        )

        # Forzar un coeficiente más fuerte para reflejar mejor la correlación real
        corr_real = correlaciones_criticas.get(
            "Carga_Trabajo_R1-Cantidad_Recursos", 0.15
        )
        # Amplificar el coeficiente para lograr la correlación deseada
        modelo_carga_recursos.coef_[0] = (
            modelo_carga_recursos.coef_[0] * 3.0
        )  # Multiplicar por 3 para amplificar el efecto
        print(f"Coeficiente ajustado: {modelo_carga_recursos.coef_[0]:.6f}")

        # Construir modelos adicionales para capturar otras correlaciones críticas
        # Modelo para Tiempo_Ejecucion ~ Carga_Trabajo_R1
        modelo_tiempo_carga = LinearRegression()
        modelo_tiempo_carga.fit(
            df[["Carga_Trabajo_R1"]].values.reshape(-1, 1),
            df["Tiempo_Ejecucion"].values,
        )
        print(
            f"Modelo Tiempo_Ejecucion ~ Carga_Trabajo_R1: coef={modelo_tiempo_carga.coef_[0]:.4f}, intercept={modelo_tiempo_carga.intercept_:.4f}"
        )

        # Modelo para Carga_Trabajo_R1 ~ Experiencia_Equipo
        modelo_carga_experiencia = LinearRegression()
        modelo_carga_experiencia.fit(
            df[["Experiencia_Equipo"]].values.reshape(-1, 1),
            df["Carga_Trabajo_R1"].values,
        )
        print(
            f"Modelo Carga_Trabajo_R1 ~ Experiencia_Equipo: coef={modelo_carga_experiencia.coef_[0]:.4f}, intercept={modelo_carga_experiencia.intercept_:.4f}"
        )

        # Verificar y ajustar coeficiente si necesario para Carga_Trabajo_R1 ~ Experiencia_Equipo
        corr_real_carga_exp = correlaciones_criticas.get(
            "Carga_Trabajo_R1-Experiencia_Equipo", 0.16
        )
        if (corr_real_carga_exp > 0 and modelo_carga_experiencia.coef_[0] < 0) or (
            corr_real_carga_exp < 0 and modelo_carga_experiencia.coef_[0] > 0
        ):
            print(
                "ADVERTENCIA: El modelo Carga-Experiencia tiene signo opuesto a la correlación real. Invirtiendo el coeficiente."
            )
            modelo_carga_experiencia.coef_[0] = abs(
                modelo_carga_experiencia.coef_[0]
            ) * (1 if corr_real_carga_exp > 0 else -1)

        # Modelo específico para Tiempo_Ejecucion ~ Cantidad_Recursos
        modelo_tiempo_recursos = LinearRegression()
        modelo_tiempo_recursos.fit(
            df[["Cantidad_Recursos"]].values.reshape(-1, 1),
            df["Tiempo_Ejecucion"].values,
        )
        print(
            f"Modelo Tiempo_Ejecucion ~ Cantidad_Recursos: coef={modelo_tiempo_recursos.coef_[0]:.4f}, intercept={modelo_tiempo_recursos.intercept_:.4f}"
        )

        # Amplificar el coeficiente para lograr una correlación más fuerte
        corr_real_tiempo_recursos = correlaciones_criticas.get(
            "Tiempo_Ejecucion-Cantidad_Recursos", 0.11
        )
        # Multiplicar por un factor mayor para aumentar el efecto
        modelo_tiempo_recursos.coef_[0] = modelo_tiempo_recursos.coef_[0] * 2.5
        print(f"Coeficiente amplificado: {modelo_tiempo_recursos.coef_[0]:.4f}")

        # Verificar y ajustar coeficiente para Tiempo_Ejecucion ~ Cantidad_Recursos
        corr_real_tiempo_recursos = correlaciones_criticas.get(
            "Tiempo_Ejecucion-Cantidad_Recursos", 0.11
        )
        if (corr_real_tiempo_recursos > 0 and modelo_tiempo_recursos.coef_[0] < 0) or (
            corr_real_tiempo_recursos < 0 and modelo_tiempo_recursos.coef_[0] > 0
        ):
            print(
                "ADVERTENCIA: El modelo Tiempo-Recursos tiene signo opuesto a la correlación real. Invirtiendo el coeficiente."
            )
            modelo_tiempo_recursos.coef_[0] = abs(modelo_tiempo_recursos.coef_[0]) * (
                1 if corr_real_tiempo_recursos > 0 else -1
            )

    # 2. Generar datos categóricos basados en distribuciones condicionales con más precisión
    for i in range(n_samples):
        sample = {}

        # Copiar datos numéricos generados
        for j, col in enumerate(numeric_cols):
            sample[col] = numeric_data[j][i]

            # Ajustar complejidad a enteros entre 1 y 5
            if col == "Complejidad":
                sample[col] = min(max(round(sample[col]), 1), 5)

            # Para Tamaño_Tarea, usar directamente un valor de los datos reales
            # basado en la distribución empírica
            if col == "Tamaño_Tarea":
                if (
                    np.random.random() < 0.9
                ):  # 90% de las veces, seguir la distribución real
                    tamanos = list(tamano_counts.keys())
                    probs = list(tamano_counts.values())
                    sample[col] = np.random.choice(tamanos, p=probs)
                else:
                    # 10% de las veces, utilizar el valor generado pero limitado a los valores reales
                    sample[col] = min(
                        tamanos_reales, key=lambda x: abs(x - sample[col])
                    )

        # Generar "Experiencia del Encuestado" si existe
        if "Experiencia del Encuestado" in df.columns:
            sample["Experiencia del Encuestado"] = np.random.choice(
                df["Experiencia del Encuestado"].unique()
            )

        # Generar Tipo_Tarea condicionado por Complejidad y Experiencia_R1 (para mejorar correlación)
        complejidad = sample["Complejidad"]
        experiencia_r1 = sample["Experiencia_R1"]
        bin_idx = min(int(complejidad) - 1, 4)
        exp_idx = min(int(experiencia_r1), 5)

        # Generar Tipo_Tarea con mejor correlación con Experiencia_R1
        if np.random.random() < 0.6:  # 60% basado en distribución condicional detallada
            exp_idx = int(round(sample["Experiencia_R1"]))
            if exp_idx in tipo_por_experiencia:
                dist = tipo_por_experiencia[exp_idx]
                tipos = list(dist.keys())
                probs = list(dist.values())
                if sum(probs) > 0:
                    probs = [p / sum(probs) for p in probs]
                    tipo_tarea = np.random.choice(tipos, p=probs)
                else:
                    # Fallback a distribución general
                    tipo_tarea = np.random.choice(
                        cat_distributions["Tipo_Tarea"].index,
                        p=cat_distributions["Tipo_Tarea"].values,
                    )
            else:
                # Fallback si no hay datos para esta experiencia
                tipo_tarea = np.random.choice(
                    cat_distributions["Tipo_Tarea"].index,
                    p=cat_distributions["Tipo_Tarea"].values,
                )
        else:
            # 40% basado en método original para mantener variabilidad
            if np.random.random() < 0.7:  # 70% basado en Complejidad (como antes)
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
                                p=cat_distributions["Tipo_Tarea"].values,
                            )
                    else:
                        tipo_tarea = np.random.choice(
                            cat_distributions["Tipo_Tarea"].index,
                            p=cat_distributions["Tipo_Tarea"].values,
                        )
                except:
                    tipo_tarea = np.random.choice(
                        cat_distributions["Tipo_Tarea"].index,
                        p=cat_distributions["Tipo_Tarea"].values,
                    )
            else:  # 30% basado en Experiencia_R1 (para preservar correlación)
                if exp_idx in tipo_por_experiencia:
                    dist = tipo_por_experiencia[exp_idx]
                    tipos = list(dist.keys())
                    probs = list(dist.values())
                    if sum(probs) > 0:
                        probs = [p / sum(probs) for p in probs]
                        tipo_tarea = np.random.choice(tipos, p=probs)
                    else:
                        tipo_tarea = np.random.choice(
                            cat_distributions["Tipo_Tarea"].index,
                            p=cat_distributions["Tipo_Tarea"].values,
                        )
                else:
                    tipo_tarea = np.random.choice(
                        cat_distributions["Tipo_Tarea"].index,
                        p=cat_distributions["Tipo_Tarea"].values,
                    )

        sample["Tipo_Tarea"] = tipo_tarea

        # Generar Fase_Tarea condicionado por Tipo_Tarea y Complejidad (para mejorar correlación)
        if np.random.random() < 0.7:  # 70% basado en Tipo_Tarea (como antes)
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
                            p=cat_distributions["Fase_Tarea"].values,
                        )
                else:
                    fase_tarea = np.random.choice(
                        cat_distributions["Fase_Tarea"].index,
                        p=cat_distributions["Fase_Tarea"].values,
                    )
            except:
                fase_tarea = np.random.choice(
                    cat_distributions["Fase_Tarea"].index,
                    p=cat_distributions["Fase_Tarea"].values,
                )
        else:  # 30% basado en Complejidad (para preservar correlación)
            if complejidad in fase_por_complejidad:
                dist = fase_por_complejidad[complejidad]
                fases = list(dist.keys())
                probs = list(dist.values())
                if sum(probs) > 0:
                    probs = [p / sum(probs) for p in probs]
                    fase_tarea = np.random.choice(fases, p=probs)
                else:
                    fase_tarea = np.random.choice(
                        cat_distributions["Fase_Tarea"].index,
                        p=cat_distributions["Fase_Tarea"].values,
                    )
            else:
                fase_tarea = np.random.choice(
                    cat_distributions["Fase_Tarea"].index,
                    p=cat_distributions["Fase_Tarea"].values,
                )

        sample["Fase_Tarea"] = fase_tarea

        # Generar Cantidad_Recursos primero para asegurar coherencia
        if (
            np.random.random() < 0.95
        ):  # 95% de las veces, usar distribución empírica directa
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

        # Generar Carga_Trabajo_R1 considerando múltiples factores para mejorar correlaciones
        carga_trabajo_metodos = np.random.choice([1, 2, 3, 4], p=[0.3, 0.3, 0.2, 0.2])

        if carga_trabajo_metodos == 1 and modelo_carga_recursos is not None:
            # Método 1: Basado en Cantidad_Recursos (mantener correlación con recursos)
            carga_base = modelo_carga_recursos.predict([[cantidad_recursos]])[0]
            noise_scale = 0.6  # Aumentar variabilidad
            noise = np.random.normal(0, noise_scale)
            carga_r1 = max(1, min(3, round(carga_base + noise)))

        elif (
            carga_trabajo_metodos == 2
            and modelo_tamano_carga is not None
            and "Tamaño_Tarea" in sample
        ):
            # Método 2: Basado en Tamaño_Tarea (mejorar correlación con tamaño)
            carga_base = modelo_tamano_carga.predict([[sample["Tamaño_Tarea"]]])[0]
            noise_scale = 0.6
            noise = np.random.normal(0, noise_scale)
            carga_r1 = max(1, min(3, round(carga_base + noise)))

        elif carga_trabajo_metodos == 3 and modelo_carga_experiencia is not None:
            # Método 3: Basado en Experiencia_Equipo (mejorar esta correlación clave)
            carga_base = modelo_carga_experiencia.predict(
                [[sample["Experiencia_Equipo"]]]
            )[0]
            noise_scale = 0.5
            noise = np.random.normal(0, noise_scale)
            carga_r1 = max(1, min(3, round(carga_base + noise)))

        else:
            # Método 4: Distribución empírica directa para mayor variabilidad
            carga_values = [1, 2, 3]
            carga_dist_real = (
                df["Carga_Trabajo_R1"].value_counts(normalize=True).sort_index()
            )
            carga_probs = [carga_dist_real.get(val, 1 / 3) for val in carga_values]
            carga_probs = [p / sum(carga_probs) for p in carga_probs]
            carga_r1 = np.random.choice(carga_values, p=carga_probs)

        sample["Carga_Trabajo_R1"] = carga_r1

        # Ajustar Tiempo_Ejecucion para mejorar correlación con Cantidad_Recursos
        if modelo_tiempo_recursos is not None:
            # Incrementamos la frecuencia de ajuste de 0.4 a 0.8
            if np.random.random() < 0.8:
                tiempo_base = sample["Tiempo_Ejecucion"]
                tiempo_modelo = modelo_tiempo_recursos.predict([[cantidad_recursos]])[0]

                # Aumentar significativamente el peso del modelo
                peso_modelo = 0.7  # Aumentado de aprox. 0.4
                tiempo_ajustado = (
                    tiempo_base * (1 - peso_modelo) + tiempo_modelo * peso_modelo
                )

                # Reducir el ruido para preservar mejor la señal
                ruido = np.random.normal(0, tiempo_base * 0.1)  # Reducido de 0.15
                sample["Tiempo_Ejecucion"] = max(0.1, tiempo_ajustado + ruido)

        # Ajustar Experiencia_Equipo según Cantidad_Recursos para preservar correlación
        if (
            np.random.random() < 0.3
        ):  # 30% de las veces, ajustar basado en Cantidad_Recursos
            if cantidad_recursos == 1:
                # Si hay menos recursos, generalmente hay menor experiencia de equipo
                exp_equipo_base = sample["Experiencia_Equipo"]
                sample["Experiencia_Equipo"] = max(
                    1, min(5, round(exp_equipo_base * 0.8))
                )
            elif cantidad_recursos == 3:
                # Si hay más recursos, generalmente hay mayor experiencia de equipo
                exp_equipo_base = sample["Experiencia_Equipo"]
                sample["Experiencia_Equipo"] = max(
                    1, min(5, round(exp_equipo_base * 1.2))
                )

        # Reemplazar el código existente por:
        # Ajustar Carga_Trabajo_R1 según Cantidad_Recursos para preservar correlación
        if np.random.random() < 0.7:  # Aumentamos la frecuencia de 0.3 a 0.7
            if cantidad_recursos == 1:
                # Si hay menos recursos, generalmente hay mayor carga de trabajo
                sample["Carga_Trabajo_R1"] = np.random.choice(
                    [1, 2, 3], p=[0.1, 0.3, 0.6]
                )
            elif cantidad_recursos == 2:
                # Si hay recursos medios, distribución más equilibrada
                sample["Carga_Trabajo_R1"] = np.random.choice(
                    [1, 2, 3], p=[0.3, 0.4, 0.3]
                )
            else:  # cantidad_recursos == 3
                # Si hay más recursos, generalmente hay menor carga de trabajo
                sample["Carga_Trabajo_R1"] = np.random.choice(
                    [1, 2, 3], p=[0.6, 0.3, 0.1]
                )

        # Generar valores para recursos con mayor variabilidad
        sample["Experiencia_Equipo"] = round(
            min(max(sample["Experiencia_Equipo"], 1), 5)
        )
        sample["Claridad_Requisitos"] = round(
            min(max(sample["Claridad_Requisitos"], 1), 5)
        )

        # Valores para R1 con mayor variabilidad
        # Añadir un componente aleatorio para incrementar variabilidad
        exp_r1_base = sample["Experiencia_R1"]
        variabilidad = np.random.normal(
            0, 0.5
        )  # Desviación estándar mayor para más variabilidad
        sample["Experiencia_R1"] = round(min(max(exp_r1_base + variabilidad, 1), 5))

        sample["Carga_Trabajo_R1"] = round(min(max(sample["Carga_Trabajo_R1"], 1), 3))

        # Agregar datos para R2 si hay al menos 2 recursos
        if cantidad_recursos >= 2:
            # Generar valores correlacionados con R1 pero con más variabilidad
            variabilidad_carga = np.random.normal(0, 0.3)  # Más variabilidad
            variabilidad_exp = np.random.normal(0, 0.4)  # Más variabilidad

            carga_r2 = min(
                max(
                    round(
                        sample["Carga_Trabajo_R1"] * np.random.normal(1, 0.3)
                        + variabilidad_carga
                    ),
                    1,
                ),
                3,
            )
            exp_r2 = min(
                max(
                    round(
                        sample["Experiencia_R1"] * np.random.normal(1, 0.4)
                        + variabilidad_exp
                    ),
                    1,
                ),
                5,
            )

            sample["Carga_Trabajo_R2"] = carga_r2
            sample["Experiencia_R2"] = exp_r2
        else:
            sample["Carga_Trabajo_R2"] = np.nan
            sample["Experiencia_R2"] = np.nan

        # Agregar datos para R3 si hay 3 recursos
        if cantidad_recursos == 3:
            # Generar valores correlacionados con promedio de R1 y R2, con más variabilidad
            avg_carga = (sample["Carga_Trabajo_R1"] + sample["Carga_Trabajo_R2"]) / 2
            avg_exp = (sample["Experiencia_R1"] + sample["Experiencia_R2"]) / 2

            variabilidad_carga = np.random.normal(0, 0.3)
            variabilidad_exp = np.random.normal(0, 0.4)

            carga_r3 = min(
                max(
                    round(avg_carga * np.random.normal(1, 0.3) + variabilidad_carga), 1
                ),
                3,
            )
            exp_r3 = min(
                max(round(avg_exp * np.random.normal(1, 0.4) + variabilidad_exp), 1), 5
            )

            sample["Carga_Trabajo_R3"] = carga_r3
            sample["Experiencia_R3"] = exp_r3
        else:
            sample["Carga_Trabajo_R3"] = np.nan
            sample["Experiencia_R3"] = np.nan

        synthetic_data.append(sample)

    # Crear DataFrame para poder ajustar correlaciones
    synthetic_df = pd.DataFrame(synthetic_data)

    # Aplicar ajuste final para mejorar correlaciones
    synthetic_df = ajustar_correlaciones(
        df,
        synthetic_df,
        numeric_cols,
        categorical_cols,
        correlaciones_criticas,
        tamanos_reales,
    )

    return synthetic_df.to_dict('records')


def generar_datos_numericos_correlacionados(
    df, n_samples, numeric_cols, corr_matrix, kdes
):
    """Genera variables numéricas correlacionadas usando descomposición de Cholesky con método mejorado"""

    # Extraer submatriz de correlación para variables numéricas
    num_corr = corr_matrix.loc[numeric_cols, numeric_cols].values

    # Asegurar que la matriz es semidefinida positiva (requerido para Cholesky)
    min_eig = np.min(np.linalg.eigvals(num_corr))
    if min_eig < 0:
        num_corr -= min_eig * np.eye(*num_corr.shape) * 1.1

    # Aplicar un pequeño factor de regularización para mejorar estabilidad
    regularization = 0.01
    num_corr = (1 - regularization) * num_corr + regularization * np.eye(
        *num_corr.shape
    )

    # Descomposición de Cholesky
    L = np.linalg.cholesky(num_corr)

    # Generar datos correlacionados
    uncorrelated = np.random.normal(size=(len(numeric_cols), n_samples))
    correlated = np.dot(L, uncorrelated)

    # Transformar a distribuciones marginales usando KDEs con mayor precisión
    transformed_data = []

    for i, col in enumerate(numeric_cols):
        # Convertir a distribución uniforme usando función de distribución acumulativa
        # de la normal estándar
        uniform_data = norm.cdf(correlated[i])

        # Invertir CDF de la distribución objetivo (usando KDE) con resolución aumentada
        kde = kdes[col]

        # Generar valores únicos para crear una CDF empírica con más resolución
        x_grid = np.linspace(
            df[col].min() * 0.9, df[col].max() * 1.1, 2000
        )  # Más puntos y rango expandido
        kde_vals = kde.evaluate(x_grid)
        kde_cdf = np.cumsum(kde_vals) / np.sum(kde_vals)

        # Para cada valor uniforme, encontrar el valor correspondiente en la CDF con interpolación
        col_data = []
        for u in uniform_data:
            idx = np.abs(kde_cdf - u).argmin()

            # Interpolación para mayor precisión
            if idx > 0 and idx < len(kde_cdf) - 1:
                idx_left = max(0, idx - 1)
                idx_right = min(len(kde_cdf) - 1, idx + 1)

                x_left, x_right = x_grid[idx_left], x_grid[idx_right]
                y_left, y_right = kde_cdf[idx_left], kde_cdf[idx_right]

                # Interpolación lineal si es posible
                if y_right > y_left:
                    x_interp = x_left + (u - y_left) * (x_right - x_left) / (
                        y_right - y_left
                    )
                    col_data.append(x_interp)
                else:
                    col_data.append(x_grid[idx])
            else:
                col_data.append(x_grid[idx])

        # Aplicar un pequeño ruido para aumentar variabilidad en los casos necesarios
        if col in ["Tamaño_Tarea", "Experiencia_R1"]:
            noise_factor = 0.05 if col == "Tamaño_Tarea" else 0.1
            col_data = [
                val * (1 + np.random.uniform(-noise_factor, noise_factor))
                for val in col_data
            ]

        transformed_data.append(col_data)

    return transformed_data


def ajustar_correlaciones(
    df_real,
    df_sintetico,
    numeric_cols,
    categorical_cols,
    correlaciones_criticas,
    tamanos_reales,
):
    """Ajusta las correlaciones en los datos sintéticos para que se asemejen más a los datos reales"""

    # 1. Forzar Tamaño_Tarea a seguir la distribución real - más estricto ahora
    # Calcular la distribución deseada (real)
    dist_real_tamano = df_real["Tamaño_Tarea"].value_counts(normalize=True)

    # Calcular la distribución actual (sintética)
    dist_sint_tamano = df_sintetico["Tamaño_Tarea"].value_counts(normalize=True)

    # Ajustar muestras para acercarse a la distribución real
    for tamano in dist_real_tamano.index:
        if tamano in dist_sint_tamano.index:
            # Determinar si necesitamos más o menos muestras de este tamaño
            pct_real = dist_real_tamano[tamano]
            pct_sint = dist_sint_tamano.get(tamano, 0)

            n_actual = sum(df_sintetico["Tamaño_Tarea"] == tamano)
            n_deseado = int(pct_real * len(df_sintetico))

            if n_actual < n_deseado:  # Necesitamos más muestras de este tamaño
                # Identificar tamaños sobrerrepresentados para reemplazar
                sobrerep = []
                for t, p in dist_sint_tamano.items():
                    if p > dist_real_tamano.get(t, 0) and t != tamano:
                        sobrerep.append(t)

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

    # 2. Ajustar las correlaciones críticas específicas

    # Para Complejidad-Fase_Tarea
    if "Complejidad-Fase_Tarea" in correlaciones_criticas:
        corr_objetivo = correlaciones_criticas["Complejidad-Fase_Tarea"]
        # Codificar Fase_Tarea para correlación
        le = LabelEncoder()
        df_sintetico_temp = df_sintetico.copy()

        # Convertir todas las fases a strings para asegurar compatibilidad
        fases_unicas = [str(fase) for fase in df_sintetico["Fase_Tarea"].unique()]
        le.fit(fases_unicas)

        # Convertir a string antes de transformar
        df_sintetico_temp["Fase_Tarea_cod"] = (
            df_sintetico["Fase_Tarea"].astype(str).map(lambda x: le.transform([x])[0])
        )

        # Identificar pares de registros que al intercambiar Fase_Tarea mejoren la correlación
        corr_actual = (
            df_sintetico_temp[["Complejidad", "Fase_Tarea_cod"]].corr().iloc[0, 1]
        )

        # Realizar intercambios para mejorar correlación
        n_intercambios = min(
            int(len(df_sintetico) * 0.05), 200
        )  # Máximo 5% o 200 filas
        for _ in range(n_intercambios):
            # Seleccionar aleatoriamente dos filas
            idx1, idx2 = df_sintetico.sample(n=2).index

            # Realizar intercambio temporal
            fase_temp = df_sintetico.loc[idx1, "Fase_Tarea"]
            df_sintetico.loc[idx1, "Fase_Tarea"] = df_sintetico.loc[idx2, "Fase_Tarea"]
            df_sintetico.loc[idx2, "Fase_Tarea"] = fase_temp

            # Actualizar codificación - convertir a string antes de transformar
            df_sintetico_temp.loc[idx1, "Fase_Tarea_cod"] = le.transform(
                [str(df_sintetico.loc[idx1, "Fase_Tarea"])]
            )[0]
            df_sintetico_temp.loc[idx2, "Fase_Tarea_cod"] = le.transform(
                [str(df_sintetico.loc[idx2, "Fase_Tarea"])]
            )[0]

            # Calcular nueva correlación
            nueva_corr = (
                df_sintetico_temp[["Complejidad", "Fase_Tarea_cod"]].corr().iloc[0, 1]
            )

            # Si la nueva correlación es peor (más lejos del objetivo), deshacer el intercambio
            if abs(nueva_corr - corr_objetivo) > abs(corr_actual - corr_objetivo):
                # Deshacer intercambio
                fase_temp = df_sintetico.loc[idx1, "Fase_Tarea"]
                df_sintetico.loc[idx1, "Fase_Tarea"] = df_sintetico.loc[
                    idx2, "Fase_Tarea"
                ]
                df_sintetico.loc[idx2, "Fase_Tarea"] = fase_temp

                # Revertir codificación - convertir a string antes de transformar
                df_sintetico_temp.loc[idx1, "Fase_Tarea_cod"] = le.transform(
                    [str(df_sintetico.loc[idx1, "Fase_Tarea"])]
                )[0]
                df_sintetico_temp.loc[idx2, "Fase_Tarea_cod"] = le.transform(
                    [str(df_sintetico.loc[idx2, "Fase_Tarea"])]
                )[0]
            else:
                corr_actual = nueva_corr

    # Aplicar procedimiento similar para las otras correlaciones críticas

    # Para Carga_Trabajo_R1-Cantidad_Recursos
    if "Carga_Trabajo_R1-Cantidad_Recursos" in correlaciones_criticas:
        corr_objetivo = correlaciones_criticas["Carga_Trabajo_R1-Cantidad_Recursos"]
        corr_actual = (
            df_sintetico[["Carga_Trabajo_R1", "Cantidad_Recursos"]].corr().iloc[0, 1]
        )

        print(
            f"\nCorrelación inicial Carga_Trabajo_R1-Cantidad_Recursos: {corr_actual:.4f} (objetivo: {corr_objetivo:.4f})"
        )

        # Corrección para correlación invertida - más agresiva
        if (corr_actual < 0 and corr_objetivo > 0) or (
            corr_actual > 0 and corr_objetivo < 0
        ):
            print(
                "CORRECCIÓN DE EMERGENCIA: Detectada correlación invertida entre Carga_Trabajo_R1 y Cantidad_Recursos"
            )

            # Obtener distribución original por cada nivel de recursos
            carga_por_recursos = {}
            for cant in sorted(df_real["Cantidad_Recursos"].unique()):
                mask = df_real["Cantidad_Recursos"] == cant
                if sum(mask) > 0:
                    carga_por_recursos[cant] = (
                        df_real.loc[mask, "Carga_Trabajo_R1"]
                        .value_counts(normalize=True)
                        .to_dict()
                    )

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
                        nuevas_cargas = np.random.choice(
                            cargas, size=len(indices), p=probs
                        )
                        df_sintetico.loc[indices, "Carga_Trabajo_R1"] = nuevas_cargas
        else:
            # Ajuste progresivo para correlaciones con mismo signo pero diferente magnitud
            # Determinar cuánto necesitamos ajustar
            diff = corr_objetivo - corr_actual

            # División de los datos por cantidad de recursos
            for recursos in sorted(df_sintetico["Cantidad_Recursos"].unique()):
                indices = df_sintetico[
                    df_sintetico["Cantidad_Recursos"] == recursos
                ].index
                if len(indices) < 10:
                    continue

                # Calcular incrementos o decrementos según la dirección necesaria
                if corr_objetivo > 0:
                    # Para correlación positiva: más recursos, valores más altos
                    ajuste = (
                        (recursos - 2) * 0.1 * abs(diff)
                    )  # Factor proporcional a la diferencia
                else:
                    # Para correlación negativa: más recursos, valores más bajos
                    ajuste = (2 - recursos) * 0.1 * abs(diff)

                # Aplicar ajuste progresivo
                for idx in indices:
                    carga_actual = df_sintetico.loc[idx, "Carga_Trabajo_R1"]
                    nueva_carga = carga_actual + ajuste
                    df_sintetico.loc[idx, "Carga_Trabajo_R1"] = max(
                        1, min(3, round(nueva_carga))
                    )

        # Verificar correlación después del ajuste
        corr_final = (
            df_sintetico[["Carga_Trabajo_R1", "Cantidad_Recursos"]].corr().iloc[0, 1]
        )
        print(f"Correlación después de ajustes: {corr_final:.4f}")

        # Si todavía es de signo incorrecto, último recurso: corrección binaria
        if (corr_final < 0 and corr_objetivo > 0) or (
            corr_final > 0 and corr_objetivo < 0
        ):
            print(
                "CORRECCIÓN BINARIA FINAL: Invirtiendo asignación de Carga_Trabajo_R1"
            )

            # Aplicación de patrones fuertes según cantidad de recursos
            patrones = {
                1: [1, 1, 1, 1, 2, 3],  # Recursos=1: mayoría carga baja
                2: [1, 2, 2, 2, 2, 3],  # Recursos=2: mayoría carga media
                3: [2, 2, 3, 3, 3, 3],  # Recursos=3: mayoría carga alta
            }

            # Aplicar estos patrones al 80% de los datos
            for cant, patron in patrones.items():
                mask = df_sintetico["Cantidad_Recursos"] == cant
                indices = df_sintetico[mask].index

                if len(indices) > 0:
                    # Aplicar a una gran proporción de los datos
                    indices_cambio = np.random.choice(
                        indices, size=int(len(indices) * 0.8), replace=False
                    )
                    nuevas_cargas = np.random.choice(patron, size=len(indices_cambio))
                    df_sintetico.loc[indices_cambio, "Carga_Trabajo_R1"] = nuevas_cargas

            # Verificación final
            corr_final = (
                df_sintetico[["Carga_Trabajo_R1", "Cantidad_Recursos"]]
                .corr()
                .iloc[0, 1]
            )
            print(f"Correlación final después de corrección binaria: {corr_final:.4f}")

    # Para Experiencia_R1-Tipo_Tarea
    if "Experiencia_R1-Tipo_Tarea" in correlaciones_criticas:
        corr_objetivo = correlaciones_criticas["Experiencia_R1-Tipo_Tarea"]

        # Codificar Tipo_Tarea para poder trabajar con correlaciones
        le = LabelEncoder()
        df_sintetico_temp = df_sintetico.copy()

        # Asegurar que todos los tipos sean strings
        tipos_unicos = [str(tipo) for tipo in df_sintetico["Tipo_Tarea"].unique()]
        le.fit(tipos_unicos)

        # Convertir a string antes de transformar
        df_sintetico_temp["Tipo_Tarea_cod"] = (
            df_sintetico["Tipo_Tarea"].astype(str).map(lambda x: le.transform([x])[0])
        )

        corr_actual = (
            df_sintetico_temp[["Experiencia_R1", "Tipo_Tarea_cod"]].corr().iloc[0, 1]
        )
        print(
            f"\nCorrelación inicial Experiencia_R1-Tipo_Tarea: {corr_actual:.4f} (objetivo: {corr_objetivo:.4f})"
        )

        # Preparar distribución condicional de Tipo_Tarea por nivel de experiencia
        # Primero obtener la distribución real
        tipo_por_experiencia = {}
        for exp in range(1, 6):
            mask = df_real["Experiencia_R1"] == exp
            if sum(mask) > 0:
                tipo_por_experiencia[exp] = (
                    df_real.loc[mask, "Tipo_Tarea"]
                    .value_counts(normalize=True)
                    .to_dict()
                )

        # Aplicar ajuste dirigido para casos con mayor desviación
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
            indices_ajustar = np.random.choice(
                indices, min(n_ajustar, len(indices)), replace=False
            )
            df_sintetico.loc[indices_ajustar, "Tipo_Tarea"] = tipo_preferido

            # Actualizar codificación
            for idx in indices_ajustar:
                df_sintetico_temp.loc[idx, "Tipo_Tarea_cod"] = le.transform(
                    [str(tipo_preferido)]
                )[0]

        # Continuar con intercambios aleatorios para refinamiento
        n_intercambios = min(int(len(df_sintetico) * 0.10) + 300, 500)
        for _ in range(n_intercambios):
            idx1, idx2 = df_sintetico.sample(n=2).index

            temp_tipo = df_sintetico.loc[idx1, "Tipo_Tarea"]
            df_sintetico.loc[idx1, "Tipo_Tarea"] = df_sintetico.loc[idx2, "Tipo_Tarea"]
            df_sintetico.loc[idx2, "Tipo_Tarea"] = temp_tipo

            # Actualizar codificación
            df_sintetico_temp.loc[idx1, "Tipo_Tarea_cod"] = le.transform(
                [str(df_sintetico.loc[idx1, "Tipo_Tarea"])]
            )[0]
            df_sintetico_temp.loc[idx2, "Tipo_Tarea_cod"] = le.transform(
                [str(df_sintetico.loc[idx2, "Tipo_Tarea"])]
            )[0]

            nueva_corr = (
                df_sintetico_temp[["Experiencia_R1", "Tipo_Tarea_cod"]]
                .corr()
                .iloc[0, 1]
            )

            if abs(nueva_corr - corr_objetivo) > abs(corr_actual - corr_objetivo):
                # Deshacer intercambio
                temp_tipo = df_sintetico.loc[idx1, "Tipo_Tarea"]
                df_sintetico.loc[idx1, "Tipo_Tarea"] = df_sintetico.loc[
                    idx2, "Tipo_Tarea"
                ]
                df_sintetico.loc[idx2, "Tipo_Tarea"] = temp_tipo

                # Revertir codificación
                df_sintetico_temp.loc[idx1, "Tipo_Tarea_cod"] = le.transform(
                    [str(df_sintetico.loc[idx1, "Tipo_Tarea"])]
                )[0]
                df_sintetico_temp.loc[idx2, "Tipo_Tarea_cod"] = le.transform(
                    [str(df_sintetico.loc[idx2, "Tipo_Tarea"])]
                )[0]
            else:
                corr_actual = nueva_corr

            # En la función ajustar_correlaciones()
            # Añade este código para corregir la distribución de Experiencia_R1:

            # Corrección de la distribución de Experiencia_R1
            dist_real_experiencia = df_real["Experiencia_R1"].value_counts(
                normalize=True
            )
            dist_sint_experiencia = df_sintetico["Experiencia_R1"].value_counts(
                normalize=True
            )

            # Corregir para cada nivel de experiencia
            for nivel in range(1, 6):
                pct_real = dist_real_experiencia.get(nivel, 0)
                pct_sint = dist_sint_experiencia.get(nivel, 0)
                n_actual = sum(df_sintetico["Experiencia_R1"] == nivel)
                n_deseado = int(pct_real * len(df_sintetico))

                if n_actual < n_deseado:  # Necesitamos más muestras de este nivel
                    # Identificar niveles sobrerrepresentados para reemplazar
                    sobrerep = []
                    for n, p in dist_sint_experiencia.items():
                        if p > dist_real_experiencia.get(n, 0) and n != nivel:
                            sobrerep.append(n)

                    if sobrerep:
                        # Seleccionar filas para cambiar
                        n_cambiar = min(
                            n_deseado - n_actual,
                            sum(df_sintetico["Experiencia_R1"].isin(sobrerep)),
                        )
                        if n_cambiar > 0:
                            mask_cambiar = df_sintetico["Experiencia_R1"].isin(sobrerep)
                            indices_cambiar = (
                                df_sintetico[mask_cambiar].sample(n=n_cambiar).index
                            )
                            df_sintetico.loc[indices_cambiar, "Experiencia_R1"] = nivel

        # Verificar correlación final
        corr_final = (
            df_sintetico_temp[["Experiencia_R1", "Tipo_Tarea_cod"]].corr().iloc[0, 1]
        )
        print(f"Correlación final Experiencia_R1-Tipo_Tarea: {corr_final:.4f}")

    # Aplicar el mismo enfoque mejorado para Complejidad-Fase_Tarea
    if "Complejidad-Fase_Tarea" in correlaciones_criticas:
        corr_objetivo = correlaciones_criticas["Complejidad-Fase_Tarea"]
        # Codificar Fase_Tarea para correlación
        le = LabelEncoder()
        df_sintetico_temp = df_sintetico.copy()

        # Convertir todas las fases a strings para asegurar compatibilidad
        fases_unicas = [str(fase) for fase in df_sintetico["Fase_Tarea"].unique()]
        le.fit(fases_unicas)

        # Convertir a string antes de transformar
        df_sintetico_temp["Fase_Tarea_cod"] = (
            df_sintetico["Fase_Tarea"].astype(str).map(lambda x: le.transform([x])[0])
        )

        # Identificar pares de registros que al intercambiar Fase_Tarea mejoren la correlación
        corr_actual = (
            df_sintetico_temp[["Complejidad", "Fase_Tarea_cod"]].corr().iloc[0, 1]
        )

        # Realizar intercambios para mejorar correlación
        n_intercambios = min(
            int(len(df_sintetico) * 0.05), 200
        )  # Máximo 5% o 200 filas
        for _ in range(n_intercambios):
            # Seleccionar aleatoriamente dos filas
            idx1, idx2 = df_sintetico.sample(n=2).index

            # Realizar intercambio temporal
            fase_temp = df_sintetico.loc[idx1, "Fase_Tarea"]
            df_sintetico.loc[idx1, "Fase_Tarea"] = df_sintetico.loc[idx2, "Fase_Tarea"]
            df_sintetico.loc[idx2, "Fase_Tarea"] = fase_temp

            # Actualizar codificación - convertir a string antes de transformar
            df_sintetico_temp.loc[idx1, "Fase_Tarea_cod"] = le.transform(
                [str(df_sintetico.loc[idx1, "Fase_Tarea"])]
            )[0]
            df_sintetico_temp.loc[idx2, "Fase_Tarea_cod"] = le.transform(
                [str(df_sintetico.loc[idx2, "Fase_Tarea"])]
            )[0]

            # Calcular nueva correlación
            nueva_corr = (
                df_sintetico_temp[["Complejidad", "Fase_Tarea_cod"]].corr().iloc[0, 1]
            )

            # Si la nueva correlación es peor (más lejos del objetivo), deshacer el intercambio
            if abs(nueva_corr - corr_objetivo) > abs(corr_actual - corr_objetivo):
                # Deshacer intercambio
                fase_temp = df_sintetico.loc[idx1, "Fase_Tarea"]
                df_sintetico.loc[idx1, "Fase_Tarea"] = df_sintetico.loc[
                    idx2, "Fase_Tarea"
                ]
                df_sintetico.loc[idx2, "Fase_Tarea"] = fase_temp

                # Revertir codificación - convertir a string antes de transformar
                df_sintetico_temp.loc[idx1, "Fase_Tarea_cod"] = le.transform(
                    [str(df_sintetico.loc[idx1, "Fase_Tarea"])]
                )[0]
                df_sintetico_temp.loc[idx2, "Fase_Tarea_cod"] = le.transform(
                    [str(df_sintetico.loc[idx2, "Fase_Tarea"])]
                )[0]
            else:
                corr_actual = nueva_corr

    # Mejorar la correlación entre Tiempo_Ejecucion y Cantidad_Recursos
    if "Tiempo_Ejecucion-Cantidad_Recursos" in correlaciones_criticas:
        corr_objetivo = correlaciones_criticas["Tiempo_Ejecucion-Cantidad_Recursos"]
        corr_actual = (
            df_sintetico[["Tiempo_Ejecucion", "Cantidad_Recursos"]].corr().iloc[0, 1]
        )

        print(
            f"\nCorrelación inicial Tiempo_Ejecucion-Cantidad_Recursos: {corr_actual:.4f} (objetivo: {corr_objetivo:.4f})"
        )

        # Si la correlación ya está sobreajustada, corregir en dirección opuesta
        if (corr_objetivo > 0 and corr_actual > corr_objetivo * 1.5) or (
            corr_objetivo < 0 and corr_actual < corr_objetivo * 1.5
        ):
            print(
                "ADVERTENCIA: Correlación Tiempo-Recursos sobreajustada. Aplicando corrección inversa."
            )

            # Aplicar un enfoque más directo basado en factores fijos
            factores_tiempo = {
                1: 0.75,  # Para recursos=1, reducir tiempo
                2: 1.0,  # Para recursos=2, mantener tiempo base
                3: 1.25,  # Para recursos=3, aumentar tiempo
            }

            # Aplicar estos factores a una gran proporción de los datos
            for cant, factor in factores_tiempo.items():
                mask = df_sintetico["Cantidad_Recursos"] == cant
                indices = df_sintetico[mask].index

                if len(indices) > 10:  # Solo si hay suficientes datos
                    # Aplicar a una gran proporción
                    indices_ajustar = np.random.choice(
                        indices, size=int(len(indices) * 0.8), replace=False
                    )

                    for idx in indices_ajustar:
                        tiempo_original = df_sintetico.loc[idx, "Tiempo_Ejecucion"]
                        # Aplicar factor con un pequeño ruido para mantener variabilidad
                        ruido = np.random.uniform(0.9, 1.1)
                        df_sintetico.loc[idx, "Tiempo_Ejecucion"] = (
                            tiempo_original * factor * ruido
                        )
        else:
            # Enfoque para ajustar la correlación: reescalamiento selectivo con factor reducido
            for cantidad in df_sintetico["Cantidad_Recursos"].unique():
                mask = df_sintetico["Cantidad_Recursos"] == cantidad
                if sum(mask) < 10:  # Saltar si hay pocos datos
                    continue

                # Ajustar factor según dirección de correlación objetivo
                if corr_objetivo > 0:
                    # Si la correlación debe ser positiva: más recursos => más tiempo
                    factor_ajuste = (
                        1.0 + (cantidad - 2) * 0.05
                    )  # Reducido significativamente (era 0.15)
                else:
                    # Si la correlación debe ser negativa: más recursos => menos tiempo
                    factor_ajuste = (
                        1.0 - (cantidad - 2) * 0.05
                    )  # Reducido significativamente

                # Aplicar ajuste a una proporción más pequeña
                indices = (
                    df_sintetico.loc[mask].sample(frac=0.4).index
                )  # Reducido (era 0.7)
                for idx in indices:
                    tiempo_original = df_sintetico.loc[idx, "Tiempo_Ejecucion"]
                    df_sintetico.loc[idx, "Tiempo_Ejecucion"] = (
                        tiempo_original * factor_ajuste
                    )

        # Comprobar correlación después del ajuste
        corr_final = (
            df_sintetico[["Tiempo_Ejecucion", "Cantidad_Recursos"]].corr().iloc[0, 1]
        )
        print(f"Correlación final Tiempo_Ejecucion-Cantidad_Recursos: {corr_final:.4f}")

    # Nueva mejora: correlación entre Tamaño_Tarea y Carga_Trabajo_R1
    if "Tamaño_Tarea-Carga_Trabajo_R1" in correlaciones_criticas:
        corr_objetivo = correlaciones_criticas["Tamaño_Tarea-Carga_Trabajo_R1"]
        corr_actual = (
            df_sintetico[["Tamaño_Tarea", "Carga_Trabajo_R1"]].corr().iloc[0, 1]
        )

        print(
            f"\nCorrelación inicial Tamaño_Tarea-Carga_Trabajo_R1: {corr_actual:.4f} (objetivo: {corr_objetivo:.4f})"
        )

        # Si la correlación está muy lejos del objetivo
        if abs(corr_actual - corr_objetivo) > 0.08:
            # Crear un modelo simple para ajustar la relación
            X = df_real[["Tamaño_Tarea"]].values
            y = df_real["Carga_Trabajo_R1"].values
            modelo_simple = LinearRegression().fit(X, y)

            # Ajustar selectivamente
            # Primero identificar registros que más contribuirían a mejorar la correlación
            tamaños_grandes = (
                df_sintetico["Tamaño_Tarea"] > df_sintetico["Tamaño_Tarea"].median()
            )

            if corr_objetivo > 0:
                # Si queremos correlación positiva:
                # Para tamaños grandes, aumentar carga
                indices_grandes = df_sintetico[tamaños_grandes].sample(frac=0.4).index
                for idx in indices_grandes:
                    tamano = df_sintetico.loc[idx, "Tamaño_Tarea"]
                    carga_estimada = max(
                        1, min(3, round(modelo_simple.predict([[tamano]])[0]))
                    )
                    # Aplicar a algunos casos para no sobreajustar
                    if np.random.random() < 0.7:
                        df_sintetico.loc[idx, "Carga_Trabajo_R1"] = carga_estimada

                # Para tamaños pequeños, reducir carga
                indices_pequeños = df_sintetico[~tamaños_grandes].sample(frac=0.3).index
                for idx in indices_pequeños:
                    if (
                        df_sintetico.loc[idx, "Carga_Trabajo_R1"] > 1
                        and np.random.random() < 0.6
                    ):
                        df_sintetico.loc[idx, "Carga_Trabajo_R1"] -= 1
            else:
                # Si queremos correlación negativa (caso raro, pero por completitud)
                # Lógica inversa
                indices_grandes = df_sintetico[tamaños_grandes].sample(frac=0.4).index
                for idx in indices_grandes:
                    if (
                        df_sintetico.loc[idx, "Carga_Trabajo_R1"] > 1
                        and np.random.random() < 0.6
                    ):
                        df_sintetico.loc[idx, "Carga_Trabajo_R1"] -= 1

                indices_pequeños = df_sintetico[~tamaños_grandes].sample(frac=0.3).index
                for idx in indices_pequeños:
                    if (
                        df_sintetico.loc[idx, "Carga_Trabajo_R1"] < 3
                        and np.random.random() < 0.6
                    ):
                        df_sintetico.loc[idx, "Carga_Trabajo_R1"] += 1

        # Comprobar correlación después del ajuste
        corr_final = (
            df_sintetico[["Tamaño_Tarea", "Carga_Trabajo_R1"]].corr().iloc[0, 1]
        )
        print(f"Correlación final Tamaño_Tarea-Carga_Trabajo_R1: {corr_final:.4f}")

    # Nueva mejora: correlación entre Carga_Trabajo_R1 y Experiencia_Equipo
    if "Carga_Trabajo_R1-Experiencia_Equipo" in correlaciones_criticas:
        corr_objetivo = correlaciones_criticas["Carga_Trabajo_R1-Experiencia_Equipo"]
        corr_actual = (
            df_sintetico[["Carga_Trabajo_R1", "Experiencia_Equipo"]].corr().iloc[0, 1]
        )

        print(
            f"\nCorrelación inicial Carga_Trabajo_R1-Experiencia_Equipo: {corr_actual:.4f} (objetivo: {corr_objetivo:.4f})"
        )

        if abs(corr_actual - corr_objetivo) > 0.08:
            # Enfoque similar: crear modelo basado en datos reales
            X = df_real[["Experiencia_Equipo"]].values
            y = df_real["Carga_Trabajo_R1"].values
            modelo_carga_exp = LinearRegression().fit(X, y)

            # Identificar registros para ajustar
            exp_alta = df_sintetico["Experiencia_Equipo"] >= 4
            exp_baja = df_sintetico["Experiencia_Equipo"] <= 2

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
                        df_sintetico.loc[idx, "Carga_Trabajo_R1"] = min(
                            3, carga_actual + 1
                        )

                # Para experiencia baja, ajustar carga hacia abajo
                indices_exp_baja = df_sintetico[exp_baja].sample(frac=0.4).index
                for idx in indices_exp_baja:
                    experiencia = df_sintetico.loc[idx, "Experiencia_Equipo"]
                    carga_estimada = modelo_carga_exp.predict([[experiencia]])[0]
                    carga_ajustada = max(1, min(3, round(carga_estimada)))

                    carga_actual = df_sintetico.loc[idx, "Carga_Trabajo_R1"]
                    if carga_ajustada < carga_actual:
                        df_sintetico.loc[idx, "Carga_Trabajo_R1"] = max(
                            1, carga_actual - 1
                        )
            else:
                # Correlación negativa: mayor experiencia, menor carga
                # Implementar lógica inversa si fuera necesario
                pass

        # Aumentar la dispersión de Carga_Trabajo_R1 para que coincida con los datos reales
        std_real = df_real["Carga_Trabajo_R1"].std()
        std_sint = df_sintetico["Carga_Trabajo_R1"].std()

        if std_sint < std_real:
            factor_ajuste = std_real / std_sint
            # Seleccionar un subconjunto aleatorio para aplicar perturbaciones
            indices_ajuste = df_sintetico.sample(frac=0.4).index

            for idx in indices_ajuste:
                carga_actual = df_sintetico.loc[idx, "Carga_Trabajo_R1"]
                # Añadir perturbación aleatoria proporcional
                perturbacion = np.random.choice([-1, 0, 1])
                nueva_carga = max(1, min(3, carga_actual + perturbacion))
                if nueva_carga != carga_actual:  # Solo aplicar si cambia el valor
                    df_sintetico.loc[idx, "Carga_Trabajo_R1"] = nueva_carga

        # Comprobar correlación después del ajuste
        corr_final = (
            df_sintetico[["Carga_Trabajo_R1", "Experiencia_Equipo"]].corr().iloc[0, 1]
        )
        print(
            f"Correlación final Carga_Trabajo_R1-Experiencia_Equipo: {corr_final:.4f}"
        )

    return df_sintetico


def validar_datos_sinteticos(
    df_real, df_sintetico, columnas_numericas, columnas_categoricas
):
    """Valida los datos sintéticos con pruebas estadísticas rigurosas"""
    print("\n=== VALIDACIÓN DE DATOS SINTÉTICOS ===")

    # Validar variables numéricas con KS test
    print("\n--- Prueba Kolmogorov-Smirnov para variables numéricas ---")
    ks_results = {}
    for col in columnas_numericas:
        if col in df_real.columns and col in df_sintetico.columns:
            try:
                ks_stat, p_value = ks_2samp(
                    df_real[col].dropna(), df_sintetico[col].dropna()
                )
                ks_results[col] = {"statistic": ks_stat, "p-value": p_value}

                print(f"{col}: KS statistic={ks_stat:.4f}, p-value={p_value:.4f}")
                print(
                    f"  Real - Media: {df_real[col].mean():.2f}, Std: {df_real[col].std():.2f}"
                )
                print(
                    f"  Sint - Media: {df_sintetico[col].mean():.2f}, Std: {df_sintetico[col].std():.2f}"
                )
            except Exception as e:
                print(f"Error en prueba KS para {col}: {e}")

    # Validar variables categóricas con Chi-cuadrado
    print("\n--- Prueba Chi-cuadrado para variables categóricas ---")
    chi2_results = {}
    for col in columnas_categoricas:
        if col in df_real.columns and col in df_sintetico.columns:
            try:
                # Obtener todas las categorías posibles
                all_categories = sorted(
                    set(df_real[col].dropna()) | set(df_sintetico[col].dropna())
                )

                # Calcular frecuencias
                real_freq = pd.Series([0] * len(all_categories), index=all_categories)
                sint_freq = pd.Series([0] * len(all_categories), index=all_categories)

                for cat, count in df_real[col].value_counts().items():
                    if cat in real_freq.index:
                        real_freq[cat] = count

                for cat, count in df_sintetico[col].value_counts().items():
                    if cat in sint_freq.index:
                        sint_freq[cat] = count

                # Tabla de contingencia
                obs = np.vstack([real_freq.values, sint_freq.values])

                # Prueba Chi-cuadrado
                chi2, p, dof, expected = chi2_contingency(obs)
                chi2_results[col] = {"statistic": chi2, "p-value": p}

                print(f"{col}: Chi2 statistic={chi2:.4f}, p-value={p:.4f}, df={dof}")

                print("Distribuciones:")
                for cat in all_categories:
                    real_pct = (
                        real_freq[cat] / real_freq.sum() * 100
                        if real_freq.sum() > 0
                        else 0
                    )
                    sint_pct = (
                        sint_freq[cat] / sint_freq.sum() * 100
                        if sint_freq.sum() > 0
                        else 0
                    )
                    print(f"  {cat}: Real={real_pct:.1f}%, Sint={sint_pct:.1f}%")
            except Exception as e:
                print(f"Error en prueba Chi2 para {col}: {e}")

    # Evaluar preservación de correlaciones
    print("\n--- Evaluación de correlaciones ---")
    try:
        # Preparar datos para correlación
        df_real_corr = df_real.copy()
        df_sint_corr = df_sintetico.copy()

        for col in columnas_categoricas:
            if col != "Cantidad_Recursos" and col in df_real.columns:
                le = LabelEncoder()
                # Combinar categorías para asegurar el mismo encoding
                unique_vals = pd.Series(
                    list(set(df_real[col].dropna()) | set(df_sintetico[col].dropna()))
                )
                le.fit(unique_vals)

                # Transformar, manteniendo NaN
                df_real_corr[col] = df_real[col].map(
                    lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan
                )
                df_sint_corr[col] = df_sintetico[col].map(
                    lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan
                )

        # Columnas para correlación (numéricas y categóricas codificadas)
        all_cols = [
            col
            for col in columnas_numericas + columnas_categoricas
            if col in df_real_corr.columns and col in df_sint_corr.columns
        ]

        # Calcular matrices de correlación
        real_corr = df_real_corr[all_cols].corr(method='spearman').fillna(0)
        sint_corr = df_sint_corr[all_cols].corr(method='spearman').fillna(0)

        # Calcular error medio absoluto
        mae = np.abs(real_corr - sint_corr).mean().mean()
        print(f"Error Absoluto Medio de correlaciones: {mae:.4f}")

        # Identificar las correlaciones con mayor discrepancia
        diff_matrix = np.abs(real_corr - sint_corr)
        threshold = np.percentile(diff_matrix.values.flatten(), 90)  # 10% peores

        print("\nCorrelaciones con mayor discrepancia (>90%):")
        for i in range(len(all_cols)):
            for j in range(i + 1, len(all_cols)):
                if diff_matrix.iloc[i, j] > threshold:
                    print(
                        f"  {all_cols[i]} - {all_cols[j]}: "
                        f"Real={real_corr.iloc[i, j]:.2f}, "
                        f"Sint={sint_corr.iloc[i, j]:.2f}, "
                        f"Diff={diff_matrix.iloc[i, j]:.2f}"
                    )
    except Exception as e:
        print(f"Error en evaluación de correlaciones: {e}")


from scipy.stats import norm


def generar_graficos_comparativos(
    df_real, df_sintetico, columnas_numericas, columnas_categoricas
):
    """Genera gráficos comparativos mejorados entre datos reales y sintéticos"""

    # Gráficos para variables numéricas
    n_cols = min(3, len(columnas_numericas))
    n_rows = (len(columnas_numericas) + n_cols - 1) // n_cols

    plt.figure(figsize=(15, n_rows * 4))

    for i, col in enumerate(columnas_numericas):
        if col in df_real.columns and col in df_sintetico.columns:
            plt.subplot(n_rows, n_cols, i + 1)

            # Histograma para datos reales
            plt.hist(
                df_real[col].dropna(), bins=20, alpha=0.5, label='Real', density=True
            )

            # Histograma para datos sintéticos
            plt.hist(
                df_sintetico[col].dropna(),
                bins=20,
                alpha=0.5,
                label='Sintético',
                density=True,
            )

            plt.title(f'Distribución de {col}')
            plt.legend()

    plt.tight_layout()
    plt.savefig('comparacion_distribuciones_numericas.png')
    print(
        "Gráficos comparativos de variables numéricas guardados como 'comparacion_distribuciones_numericas.png'"
    )

    # Gráficos para variables categóricas
    n_cols = min(2, len(columnas_categoricas))
    n_rows = (len(columnas_categoricas) + n_cols - 1) // n_cols

    plt.figure(figsize=(15, n_rows * 5))

    for i, col in enumerate(columnas_categoricas):
        if col in df_real.columns and col in df_sintetico.columns:
            plt.subplot(n_rows, n_cols, i + 1)

            # Convertir categorías a strings para evitar problemas de comparación
            real_cats = [str(x) for x in df_real[col].dropna().unique()]
            sint_cats = [str(x) for x in df_sintetico[col].dropna().unique()]

            # Obtener todas las categorías únicas
            all_cats = sorted(set(real_cats) | set(sint_cats))

            # Contar frecuencias
            real_counts = pd.Series([0] * len(all_cats), index=all_cats)
            sint_counts = pd.Series([0] * len(all_cats), index=all_cats)

            # Llenar frecuencias para datos reales
            for cat, count in df_real[col].value_counts(normalize=True).items():
                real_counts[str(cat)] = count

            # Llenar frecuencias para datos sintéticos
            for cat, count in df_sintetico[col].value_counts(normalize=True).items():
                sint_counts[str(cat)] = count

            x = np.arange(len(all_cats))
            width = 0.35

            # Crear gráfico de barras
            plt.bar(x - width / 2, real_counts, width, label='Real')
            plt.bar(x + width / 2, sint_counts, width, label='Sintético')

            plt.xlabel('Categoría')
            plt.ylabel('Frecuencia relativa')
            plt.title(f'Distribución de {col}')
            plt.xticks(x, all_cats, rotation=45, ha='right')
            plt.legend()

    plt.tight_layout()
    plt.savefig('comparacion_distribuciones_categoricas.png')
    print(
        "Gráficos comparativos de variables categóricas guardados como 'comparacion_distribuciones_categoricas.png'"
    )

    # Matriz de correlación
    plt.figure(figsize=(12, 10))

    # Combinar variables para análisis de correlación
    all_cols = columnas_numericas + [
        c for c in columnas_categoricas if c != "Cantidad_Recursos"
    ]

    # Convertir categorías para correlación
    df_real_corr = df_real.copy()
    df_sint_corr = df_sintetico.copy()

    for col in columnas_categoricas:
        if col != "Cantidad_Recursos":
            le = LabelEncoder()
            # Convertir a strings primero para asegurar compatibilidad
            unique_vals = list(
                set([str(x) for x in df_real[col].dropna()])
                | set([str(x) for x in df_sintetico[col].dropna()])
            )
            le.fit(unique_vals)

            # Convertir valores a strings antes de transformar
            df_real_corr[col] = le.transform([str(x) for x in df_real[col].dropna()])
            df_sint_corr[col] = le.transform(
                [str(x) for x in df_sintetico[col].dropna()]
            )

    # Calcular y graficar matrices de correlación
    try:
        plt.subplot(1, 2, 1)
        corr_real = df_real_corr[all_cols].corr()
        sns.heatmap(corr_real, annot=True, cmap='coolwarm', fmt='.2f', square=True)
        plt.title('Correlaciones - Datos Reales')

        plt.subplot(1, 2, 2)
        corr_sint = df_sint_corr[all_cols].corr()
        sns.heatmap(corr_sint, annot=True, cmap='coolwarm', fmt='.2f', square=True)
        plt.title('Correlaciones - Datos Sintéticos')

        plt.tight_layout()
        plt.savefig('comparacion_correlaciones.png')
        print(
            "Comparación de matrices de correlación guardada como 'comparacion_correlaciones.png'"
        )
    except Exception as e:
        print(f"Error al generar matriz de correlación: {e}")
        print("Continuando con la ejecución...")


def validar_correlaciones_criticas(df_real, df_sintetico, variables_criticas):
    """Valida específicamente las correlaciones entre variables críticas"""
    # Preparar datos
    df_real_sub = df_real[variables_criticas].copy()
    df_sint_sub = df_sintetico[variables_criticas].copy()

    # Calcular correlaciones
    corr_real = df_real_sub.corr(method='spearman')
    corr_sint = df_sint_sub.corr(method='spearman')

    print("\nCorrelaciones de variables críticas:")
    print("\nDatos reales:")
    print(corr_real)
    print("\nDatos sintéticos:")
    print(corr_sint)

    # Calcular diferencia absoluta
    diff = np.abs(corr_real - corr_sint)

    print("\nDiferencia absoluta en correlaciones:")
    print(diff)

    # Comprobar distribuciones de variables críticas
    for var in variables_criticas:
        print(f"\nDistribución de {var}:")
        print(f"Real - Media: {df_real[var].mean():.2f}, Std: {df_real[var].std():.2f}")
        print(
            f"Sint - Media: {df_sintetico[var].mean():.2f}, Std: {df_sintetico[var].std():.2f}"
        )

        # Mostrar valores únicos y frecuencias para variables categóricas/discretas
        if (
            var in ["Cantidad_Recursos", "Complejidad", "Experiencia_R1"]
            or df_real[var].nunique() < 20
        ):
            print(
                "Frecuencias reales:",
                df_real[var].value_counts(normalize=True).sort_index().to_dict(),
            )
            print(
                "Frecuencias sintéticas:",
                df_sintetico[var].value_counts(normalize=True).sort_index().to_dict(),
            )

    # Validar específicamente las correlaciones mencionadas como críticas
    correlaciones_especificas = [
        ("Complejidad", "Fase_Tarea"),
        ("Carga_Trabajo_R1", "Cantidad_Recursos"),
        ("Experiencia_R1", "Tipo_Tarea"),
        ("Experiencia_Equipo", "Cantidad_Recursos"),
    ]

    print("\n=== Correlaciones específicas identificadas como críticas ===")
    for var1, var2 in correlaciones_especificas:
        # Codificar variables categóricas si es necesario
        df_real_temp = df_real.copy()
        df_sint_temp = df_sintetico.copy()

        for var in [var1, var2]:
            if var in ["Fase_Tarea", "Tipo_Tarea"]:
                le = LabelEncoder()
                # Asegurar que todos son strings
                combined_vals = [
                    str(x)
                    for x in list(
                        set(df_real[var].dropna()) | set(df_sintetico[var].dropna())
                    )
                ]
                le.fit(combined_vals)

                # Convertir a string antes de transformar
                df_real_temp[var] = (
                    df_real[var]
                    .astype(str)
                    .map(lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan)
                )
                df_sint_temp[var] = (
                    df_sintetico[var]
                    .astype(str)
                    .map(lambda x: le.transform([x])[0] if pd.notnull(x) else np.nan)
                )

        # Calcular correlaciones
        try:
            corr_real = df_real_temp[[var1, var2]].corr(method='spearman').iloc[0, 1]
            corr_sint = df_sint_temp[[var1, var2]].corr(method='spearman').iloc[0, 1]
            diff = abs(corr_real - corr_sint)

            print(
                f"{var1} - {var2}: Real={corr_real:.2f}, Sint={corr_sint:.2f}, Diff={diff:.2f}"
            )
        except Exception as e:
            print(f"Error al calcular correlación entre {var1} y {var2}: {e}")


def validar_distribucion_conjunta(df_real, df_sintetico, pares_variables):
    """Valida la distribución conjunta entre pares de variables para verificar
    que las relaciones se mantienen en los datos sintéticos."""

    for var1, var2 in pares_variables:
        print(f"\n=== Distribución conjunta de {var1} y {var2} ===")

        # Verificar si ambas variables son numéricas
        if (
            var1 in df_real.select_dtypes(include=[np.number]).columns
            and var2 in df_real.select_dtypes(include=[np.number]).columns
        ):

            # Crear tablas de contingencia para análisis
            # Discretizar variables si es necesario
            df_real_temp = df_real[[var1, var2]].copy()
            df_sint_temp = df_sintetico[[var1, var2]].copy()

            # Contar ocurrencias conjuntas
            table_real = pd.crosstab(
                df_real_temp[var1], df_real_temp[var2], normalize=True
            )
            table_sint = pd.crosstab(
                df_sint_temp[var1], df_sint_temp[var2], normalize=True
            )

            print("\nDistribución conjunta real:")
            print(table_real)
            print("\nDistribución conjunta sintética:")
            print(table_sint)

            # Calcular diferencias
            try:
                # Alinear índices y columnas
                all_idx = sorted(set(table_real.index) | set(table_sint.index))
                all_cols = sorted(set(table_real.columns) | set(table_sint.columns))

                table_real_full = pd.DataFrame(0, index=all_idx, columns=all_cols)
                table_sint_full = pd.DataFrame(0, index=all_idx, columns=all_cols)

                for idx in table_real.index:
                    for col in table_real.columns:
                        table_real_full.loc[idx, col] = table_real.loc[idx, col]

                for idx in table_sint.index:
                    for col in table_sint.columns:
                        table_sint_full.loc[idx, col] = table_sint.loc[idx, col]

                # Calcular diferencia absoluta media
                diff = np.abs(table_real_full - table_sint_full).mean().mean()
                print(
                    f"\nDiferencia absoluta media en distribución conjunta: {diff:.4f}"
                )
            except Exception as e:
                print(f"Error al calcular diferencias: {e}")

        # Si una de las variables es categórica
        elif (
            var1 in df_real.select_dtypes(exclude=[np.number]).columns
            or var2 in df_real.select_dtypes(exclude=[np.number]).columns
        ):

            # Preparar datos
            df_real_temp = df_real[[var1, var2]].copy()
            df_sint_temp = df_sintetico[[var1, var2]].copy()

            # Asegurar que las variables categóricas son strings
            if var1 in df_real.select_dtypes(exclude=[np.number]).columns:
                df_real_temp[var1] = df_real_temp[var1].astype(str)
                df_sint_temp[var1] = df_sint_temp[var1].astype(str)

            if var2 in df_real.select_dtypes(exclude=[np.number]).columns:
                df_real_temp[var2] = df_real_temp[var2].astype(str)
                df_sint_temp[var2] = df_sint_temp[var2].astype(str)

            # Mostrar frecuencias conjuntas
            try:
                table_real = pd.crosstab(
                    df_real_temp[var1], df_real_temp[var2], normalize=True
                )
                table_sint = pd.crosstab(
                    df_sint_temp[var1], df_sint_temp[var2], normalize=True
                )

                print("\nDistribución conjunta real (top 5 filas):")
                print(table_real.head())
                print("\nDistribución conjunta sintética (top 5 filas):")
                print(table_sint.head())

                # Prueba chi-cuadrado para comparar distribuciones
                # Aplanar las tablas para la prueba
                real_flat = []
                sint_flat = []

                # Obtener todas las combinaciones de índices y columnas
                all_idx = sorted(set(table_real.index) | set(table_sint.index))
                all_cols = sorted(set(table_real.columns) | set(table_sint.columns))

                for idx in all_idx:
                    for col in all_cols:
                        real_val = (
                            table_real.loc[idx, col]
                            if idx in table_real.index and col in table_real.columns
                            else 0
                        )
                        sint_val = (
                            table_sint.loc[idx, col]
                            if idx in table_sint.index and col in table_sint.columns
                            else 0
                        )

                        real_flat.append(
                            real_val * 100
                        )  # Multiplicamos por 100 para evitar valores muy pequeños
                        sint_flat.append(sint_val * 100)

                # Prueba de chi-cuadrado
                if (
                    len(real_flat) > 0
                    and len(sint_flat) > 0
                    and np.sum(real_flat) > 0
                    and np.sum(sint_flat) > 0
                ):
                    chi2, p, _, _ = chi2_contingency([real_flat, sint_flat])
                    print(f"\nPrueba Chi-cuadrado: chi2={chi2:.4f}, p-value={p:.4f}")

                    if p < 0.05:
                        print(
                            "Las distribuciones conjuntas son significativamente diferentes"
                        )
                    else:
                        print(
                            "No hay diferencias significativas entre las distribuciones conjuntas"
                        )
            except Exception as e:
                print(f"Error al analizar distribución conjunta: {e}")


# Ejemplo de uso
if __name__ == "__main__":
    generar_datos_monte_carlo(
        "estimacion_tiempos_generado.csv", 20000, "datos_sinteticos_mejorados.csv"
    )
