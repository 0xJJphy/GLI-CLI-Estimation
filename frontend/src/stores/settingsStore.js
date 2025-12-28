/**
 * Settings Store
 * Manages theme (darkMode), language, and translations.
 */
import { writable, derived } from 'svelte/store';

// Theme state
export const darkMode = writable(false);

// Language state (default: English)
export const language = writable('en');

// Translations dictionary
const translations = {
    en: {
        gli: "Sum of global central bank balance sheets in USD. ↑ Expansion = Liquidity injection (bullish) | ↓ Contraction = QT (bearish)",
        gli_cb: "Individual central bank assets in USD. Larger = more weight in global liquidity.",
        btc_fair: "BTC fair value derived from macro liquidity factors. Price above = overvalued, below = undervalued.",
        btc_bands: "±1σ/2σ bands show historical deviation range. Mean-reverts over time.",
        net_liq: "Fed Balance Sheet minus TGA and RRP. Key driver of US dollar liquidity.",
        rrp: "Reverse Repo drains liquidity from the system. ↓ RRP = Liquidity release (bullish)",
        tga: "Treasury General Account. ↓ TGA = Treasury spending = Liquidity injection",
        m2_global: "Global money supply in USD. Leading indicator for asset prices (45-90 day lag).",
        m2_country: "Country M2 money supply in local currency converted to USD.",
        cli: "Aggregates credit conditions, volatility, and lending. ↑ CLI = Easier credit (bullish) | ↓ Contraction = Tighter (bearish)",
        hy_spread: "High Yield bond spreads vs Treasuries. ↓ Spread = Risk-on (bullish) | ↑ Spread = Risk-off",
        ig_spread: "Investment Grade spreads. ↓ Spread = Credit easing | ↑ Spread = Credit stress",
        nfci_credit: "Fed's NFCI Credit subindex. ↓ Below 0 = Loose conditions | ↑ Above 0 = Tight",
        nfci_risk: "Fed's NFCI Risk subindex. ↓ Below 0 = Low fear | ↑ Above 0 = Elevated fear",
        lending: "Senior Loan Officer Survey. ↑ Tightening = Banks restrict credit | ↓ Easing = Free lending",
        vix: "Implied volatility (fear gauge). Z>2 = Panic | Z<-1 = Complacency. Mean-reverts.",
        tips: "Breakeven (amber): Inflation expectations. Real Rate (blue): True cost of money. 5Y5Y (green): Long-term anchor.",
        bank_reserves: "Total reserves maintained by depository institutions at Federal Reserve Banks. When reserves fall, liquidity stress increases.",
        repo_stress: "Comparison between SOFR (market rate) and IORB (Fed floor). If SOFR stays above IORB, it indicates systemic liquidity shortage.",
        // Navigation
        nav_dashboard: "Dashboard",
        nav_gli: "Global Flows CB",
        nav_m2: "Global M2",
        nav_us_system: "US System",
        nav_risk_model: "Risk Model",
        nav_btc_analysis: "BTC Analysis",
        nav_btc_quant: "BTC Quant v2",
        // Header & Global
        header_desc: "Real-time macro liquidity and credit monitoring across 5 major central banks",
        system_live: "System Live",
        refresh_data: "Refresh Data",
        light_mode: "Light Mode",
        dark_mode: "Dark Mode",
        switch_lang: "Switch Language",
        conn_error: "Connection Error:",
        // Stats Cards
        stat_gli: "Global Liquidity (GLI)",
        stat_us_net: "US Net Liquidity",
        stat_cli: "Credit Index (CLI)",
        stat_vix: "Volatility Index",
        // Common Table Labels
        bank: "Bank",
        weight: "Wgt",
        economy: "Economy",
        account: "Account",
        impact_1m: "1M Global Impact",
        impact_3m: "3M Global Impact",
        impact_1y: "1Y Global Impact",
        impact_us: "Impact on Net Liq",
        impact_note_gli: "* Impact = % contribution of bank's 1M move to total Global Liquidity.",
        impact_note_us: "* Imp = Contribution to US Net Liquidity change. RRP/TGA have an inverse effect.",
        last_data: "Last Data:",
        last: "Last:",
        // Chart Headers
        chart_gli_aggregate: "Global Liquidity Index (Aggregate)",
        chart_us_net_liq: "US Net Liquidity Trends",
        chart_fed_assets: "Fed Assets (USD Trillion)",
        chart_us_credit: "US Credit Conditions",
        chart_rrp: "Fed RRP Facility",
        chart_tga: "Treasury General Account (TGA)",
        chart_m2_aggregate: "Global M2 Money Supply (Aggregate)",
        chart_inflation_exp: "Inflation Expectations (TIPS Market)",
        chart_gli_comp: "GLI Composition & Performance",
        chart_m2_comp: "M2 Composition & Performance",
        chart_us_comp: "US System Components Impact",
        chart_bank_reserves: "Bank Reserves vs Net Liquidity",
        chart_repo_stress: "Repo Market Stress (SOFR vs IORB)",
        // Reserves Metrics
        reserves_velocity: "Reserves Velocity",
        roc_3m: "3M ROC",
        spread_zscore: "Spread Z-Score",
        momentum: "Momentum",
        lcr: "LCR",
        reserves_high_stress: "High Stress",
        reserves_normal: "Normal",
        reserves_low_stress: "Low Stress",
        reserves_bullish: "Bullish",
        reserves_bearish: "Bearish",
        reserves_neutral: "Neutral",
        // US System Metrics
        liquidity_score: "Liquidity Score",
        rrp_drain: "RRP Drain",
        weeks_to_empty: "Weeks to Empty",
        tga_deviation: "TGA Deviation",
        fed_momentum_label: "Fed Momentum",
        netliq_roc: "Net Liq ROC",
        liquid_env: "Liquid",
        dry_env: "Dry",
        regime_qe: "QE Mode",
        regime_qt: "QT Mode",
        // Flow/Impulse Metrics
        flow_impulse: "Liquidity Impulse",
        flow_accel: "Acceleration",
        flow_zscore: "Impulse Z-Score",
        flow_desc: "Impulse tracks the rate of change in liquidity flows. Acceleration captures regime shifts.",
        gli_impulse: "GLI Impulse (13W)",
        m2_impulse: "M2 Impulse (13W)",
        cb_contribution: "CB Contribution to ΔGLI",
        // Formatting
        spot_usd: "Spot USD",
        const_fx: "Const FX",
        // BTC Analysis tab
        btc_analysis_title: "BTC Fair Value Model",
        btc_analysis_desc: "Bitcoin fair value derived from global liquidity, M2, and credit conditions. Price above line = overvalued, below = undervalued.",
        current_valuation: "Current Valuation",
        btc_price: "BTC Price",
        fair_value: "Fair Value",
        deviation: "Deviation",
        zscore: "Z-Score",
        lag_analysis: "Predictive Signals: CLI → BTC Lag Analysis",
        roc_window: "ROC Window",
        optimal_lag: "Optimal Lag",
        max_correlation: "Max Correlation",
        interpretation: "Interpretation",
        // BTC Quant v2 tab
        quant_v2_title: "Quant v2: Enhanced Bitcoin Fair Value Model",
        quant_v2_desc: "This model addresses econometric issues in the legacy model:",
        quant_v2_weekly: "Weekly frequency (W-FRI) instead of daily to avoid FRI autocorrelation",
        quant_v2_log: "Δlog(BTC) returns instead of log levels (avoids spurious regression)",
        quant_v2_elastic: "ElasticNet with 1-8 week lags for automatic feature selection",
        quant_v2_pca: "PCA GLI factor instead of raw sum (handles colinearity)",
        quant_v2_vol: "Rolling 52-week volatility for adaptive bands",
        oos_metrics: "Out-of-Sample Metrics",
        model_params: "Model Parameters",
        quant_chart_desc: "Cumulative model drift may cause divergence over time.",
        interp_regression: "Regression using:",
        interp_gli_lag: "GLI (45-day lag)",
        interp_cli_lag: "CLI (14-day lag)",
        interp_vix_coin: "VIX (coincident)",
        interp_netliq_lag: "US Net Liq (30-day lag)",
        interp_zones: "Deviation Zones",
        interp_extreme: "±2σ: Extreme over/undervaluation",
        interp_moderate: "±1σ: Moderate deviation",
        interp_fair_range: "Within ±1σ: Fair value range",
        interp_signals: "Trading Signals",
        interp_profittaking: "Z > +2: Consider profit-taking",
        interp_accumulation: "Z < -2: Potential accumulation",
        interp_divergence: "ROC divergence: Momentum shifts",
        // Data Health & Pulse
        data_health: "Data Health & Coverage",
        series: "Series",
        freshness: "Freshness",
        real_date: "Real Date",
        coverage: "Coverage",
        active_cbs: "Active CBs",
        impulse_analysis: "Liquidity Impulse Analysis",
        chart_impulse_desc: "Comparing the momentum of GLI, Net Liquidity, and Credit conditions (Normalized Z-Scores). Divergences often lead BTC price action.",
        btc_roc_overlay: "BTC ROC Overlay",
        period: "Period",
        lag_days: "Lag (Days)",
        // Macro Regimes
        regime_bullish: "Bullish Macro",
        regime_bearish: "Bearish Macro",
        regime_global_inj: "Global Injection",
        regime_us_inj: "US Injection",
        regime_early_warning: "Early Warning",
        regime_losing_steam: "Losing Steam",
        regime_neutral: "Neutral / Transition",
        regime_signal: "Macro Pulse & Regime",
        regime_chart_desc: "Log-scale BTC Price overlaid on Macro Regime. Background tracks combined Global (GLI) and US (NetLiq) liquidity momentum. Green: Dual Expansion (Bullish). Red: Dual Contraction (Bearish). Grey: Mixed/Neutral.",
        regime_formula_title: "Regime Formula",
        regime_formula_desc: "Score = 50 + 15 × Total_Z | Liquidity (35% GLI + 35% NetLiq + 20% M2 ± CB breadth) + Credit (60% CLI + 40% CLI momentum) - Brakes (real rates + repo stress + reserve scarcity)",
        regime_score_bullish: "Score > 50: Bullish bias (green) → Liquidity expanding, credit easing",
        regime_score_bearish: "Score < 50: Bearish bias (red) → Liquidity contracting, credit tightening",
        // Signal Reasons - HY Spread
        signal_hy_bullish: "HY spread contracted: risk appetite, easy credit.",
        signal_hy_bearish: "HY spread widened: risk aversion, credit stress.",
        signal_hy_neutral: "HY spread in normal range, no extreme signal.",
        // Signal Reasons - IG Spread
        signal_ig_bullish: "IG spread low: solid credit conditions.",
        signal_ig_bearish: "IG spread elevated: credit market tension.",
        signal_ig_neutral: "IG spread stable, normal conditions.",
        // Signal Reasons - NFCI Credit
        signal_nfci_credit_bullish: "NFCI Credit negative: loose credit conditions.",
        signal_nfci_credit_bearish: "NFCI Credit positive: restrictive credit conditions.",
        signal_nfci_credit_neutral: "NFCI Credit neutral, no extreme pressure.",
        // Signal Reasons - NFCI Risk
        signal_nfci_risk_bullish: "NFCI Risk low: systemic risk contained.",
        signal_nfci_risk_bearish: "NFCI Risk elevated: higher perceived systemic risk.",
        signal_nfci_risk_neutral: "NFCI Risk at normal levels.",
        // Signal Reasons - Lending
        signal_lending_bullish: "Credit standards relaxed: credit expansion.",
        signal_lending_bearish: "Restrictive standards: credit contraction.",
        signal_lending_neutral: "Lending standards unchanged.",
        // Signal Reasons - VIX
        signal_vix_bullish: "VIX low: market complacency/confidence.",
        signal_vix_bearish: "VIX elevated: fear and market volatility.",
        signal_vix_neutral: "VIX in normal range, moderate volatility.",
        // Signal Reasons - CLI
        signal_cli_bullish: "CLI indicates credit expansion and risk appetite.",
        signal_cli_bearish: "CLI indicates credit contraction and risk aversion.",
        signal_cli_neutral: "CLI neutral, balanced liquidity conditions.",
        // Signal Reasons - Repo
        signal_repo_bullish: "SOFR ≈ IORB: adequate interbank liquidity.",
        signal_repo_bearish: "SOFR >> IORB: repo liquidity stress.",
        signal_repo_neutral: "Repo spread in normal range.",
        signal_repo_warning: "SOFR << IORB: excess liquidity (unusual).",
        // Signal Reasons - TIPS
        signal_tips_bullish: "Reflation: High BE + Low RR. Fed dovish, economic expansion.",
        signal_tips_bearish: "Tightening: High RR + Low BE. Fed hawkish, monetary restriction.",
        signal_tips_neutral: "Goldilocks: BE & RR in normal range, macro equilibrium.",
        signal_tips_warning: "Stagflation: High inflation + Fed hawkish. Adverse conditions.",
        signal_tips_disinflation: "Disinflation: Low BE & RR. Possible slowdown or deflation.",
    },
    es: {
        gli: "Suma de balances de bancos centrales en USD. ↑ Expansión = Inyección de liquidez (alcista) | ↓ Contracción = QT (bajista)",
        gli_cb: "Activos individuales de bancos centrales en USD. Mayor = más peso en liquidez global.",
        btc_fair: "Valor justo de BTC derivado de factores macro. Precio arriba = sobrevalorado, abajo = infravalorado.",
        btc_bands: "Bandas ±1σ/2σ muestran rango de desviación histórica. Revierte a la media.",
        net_liq: "Balance de la Fed menos TGA y RRP. Motor clave de liquidez del dólar.",
        rrp: "Repo Inverso drena liquidez del sistema. ↓ RRP = Liberación de liquidez (alcista)",
        tga: "Cuenta General del Tesoro. ↓ TGA = Gasto del Tesoro = Inyección de liquidez",
        m2_global: "Oferta monetaria global en USD. Indicador adelantado de precios (45-90 días de retardo).",
        m2_country: "M2 del país en moneda local convertida a USD.",
        cli: "Agrega condiciones crediticias, volatilidad y préstamos. ↑ CLI = Crédito fácil (alcista) | ↓ CLI = Más estricto",
        hy_spread: "Spreads de bonos High Yield vs Treasuries. ↓ Spread = Risk-on (alcista) | ↑ = Risk-off",
        ig_spread: "Spreads de grado de inversión. ↓ Spread = Crédito relajado | ↑ = Estrés crediticio",
        nfci_credit: "Subíndice de crédito NFCI de la Fed. ↓ Bajo 0 = Condiciones laxas | ↑ Sobre 0 = Estrictas",
        nfci_risk: "Subíndice de riesgo NFCI. ↓ Bajo 0 = Bajo miedo | ↑ Sobre 0 = Miedo elevado",
        lending: "Encuesta de préstamos bancarios. ↑ Endurecimiento = Restringen crédito | ↓ = Prestan libremente",
        vix: "Volatilidad implícita (indicador de miedo). Z>2 = Pánico | Z<-1 = Complacencia.",
        tips: "Breakeven (ámbar): Expectativas de inflación. Tasa Real (azul): Coste real del dinero. 5Y5Y (verde): Anclaje a largo plazo.",
        bank_reserves: "Reservas totales mantenidas por instituciones depositarias en los Bancos de la Reserva Federal. Cuando las reservas caen, el estrés de liquidez aumenta.",
        repo_stress: "Comparativa entre el SOFR (tipo de mercado) y el IORB (suelo de la Fed). Si el SOFR se mantiene por encima del IORB, indica escasez sistémica de liquidez.",
        // Navigation
        nav_dashboard: "Panel de Control",
        nav_gli: "Flujos Globales CB",
        nav_m2: "M2 Global",
        nav_us_system: "Sistema EE.UU.",
        nav_risk_model: "Modelo de Riesgo",
        nav_btc_analysis: "Análisis BTC",
        nav_btc_quant: "BTC Quant v2",
        // Header & Global
        header_desc: "Monitoreo en tiempo real de liquidez macro y crédito en 5 bancos centrales",
        system_live: "Sistema en Vivo",
        refresh_data: "Actualizar Datos",
        light_mode: "Modo Claro",
        dark_mode: "Modo Oscuro",
        switch_lang: "Cambiar Idioma",
        conn_error: "Error de Conexión:",
        // Stats Cards
        stat_gli: "Liquidez Global (GLI)",
        stat_us_net: "Liquidez Neta EE.UU.",
        stat_cli: "Índice de Crédito (CLI)",
        stat_vix: "Índice de Volatilidad",
        // Common Table Labels
        bank: "Banco",
        weight: "Peso",
        economy: "Economía",
        account: "Cuenta",
        impact_1m: "Impacto Global 1M",
        impact_3m: "Impacto Global 3M",
        impact_1y: "Impacto Global 1Y",
        impact_us: "Impacto en Liq Neta",
        impact_note_gli: "* Impacto = % contribución del movimiento 1M del banco a la Liquidez Global total.",
        impact_note_us: "* Imp = Contribución al cambio de Liquidez Neta de EE.UU. RRP/TGA tienen un efecto inverso.",
        last_data: "Últimos Datos:",
        last: "Último:",
        // Chart Headers
        chart_gli_aggregate: "Índice de Liquidez Global (Agregado)",
        chart_us_net_liq: "Tendencias de Liquidez Neta EE.UU.",
        chart_fed_assets: "Activos de la Fed (Trillones USD)",
        chart_us_credit: "Condiciones Crediticias EE.UU.",
        chart_rrp: "Facilidad RRP de la Fed",
        chart_tga: "Cuenta General del Tesoro (TGA)",
        chart_m2_aggregate: "Oferta Monetaria M2 Global (Agregada)",
        chart_inflation_exp: "Expectativas de Inflación (Mercado TIPS)",
        chart_gli_comp: "Composición y Rendimiento de GLI",
        chart_m2_comp: "Composición y Rendimiento de M2",
        chart_us_comp: "Impacto de Componentes del Sistema EE.UU.",
        chart_bank_reserves: "Reservas Bancarias vs Liquidez Neta",
        chart_repo_stress: "Estrés del Mercado Repo (SOFR vs IORB)",
        // Reserves Metrics
        reserves_velocity: "Velocidad de Reservas",
        roc_3m: "ROC 3M",
        spread_zscore: "Z-Score Spread",
        momentum: "Momentum",
        lcr: "LCR",
        reserves_high_stress: "Alto Estrés",
        reserves_normal: "Normal",
        reserves_low_stress: "Bajo Estrés",
        reserves_bullish: "Alcista",
        reserves_bearish: "Bajista",
        reserves_neutral: "Neutral",
        // US System Metrics
        liquidity_score: "Índice de Liquidez",
        rrp_drain: "Drenaje RRP",
        weeks_to_empty: "Semanas hasta vacío",
        tga_deviation: "Desviación TGA",
        fed_momentum_label: "Momentum Fed",
        netliq_roc: "ROC Liq Neta",
        liquid_env: "Líquido",
        dry_env: "Seco",
        regime_qe: "Modo QE",
        regime_qt: "Modo QT",
        // Flow/Impulse Metrics
        flow_impulse: "Impulso de Liquidez",
        flow_accel: "Aceleración",
        flow_zscore: "Z-Score del Impulso",
        flow_desc: "El impulso rastrea la tasa de cambio en los flujos. La aceleración captura cambios de régimen.",
        gli_impulse: "Impulso GLI (13S)",
        m2_impulse: "Impulso M2 (13S)",
        cb_contribution: "Contribución CB a ΔGLI",
        // Formatting
        spot_usd: "Spot USD",
        const_fx: "FX Const",
        // BTC Analysis tab
        btc_analysis_title: "Modelo de Valor Justo de BTC",
        btc_analysis_desc: "Valor justo de Bitcoin derivado de liquidez global, M2 y condiciones de crédito. Precio arriba = sobrevalorado, abajo = infravalorado.",
        current_valuation: "Valoración Actual",
        btc_price: "Precio BTC",
        fair_value: "Valor Justo",
        deviation: "Desviación",
        zscore: "Z-Score",
        lag_analysis: "Señales Predictivas: CLI → BTC Análisis de Retardo",
        roc_window: "Ventana ROC",
        optimal_lag: "Retardo Óptimo",
        max_correlation: "Correlación Máxima",
        interpretation: "Interpretación",
        // BTC Quant v2 tab
        quant_v2_title: "Quant v2: Modelo Mejorado de Valor Justo de Bitcoin",
        quant_v2_desc: "Este modelo aborda problemas econométricos del modelo anterior:",
        quant_v2_weekly: "Frecuencia semanal (W-VIE) en lugar de diaria para evitar autocorrelación",
        quant_v2_log: "Retornos Δlog(BTC) en lugar de niveles log (evita regresión espuria)",
        quant_v2_elastic: "ElasticNet con retardos de 1-8 semanas para selección automática",
        quant_v2_pca: "Factor PCA GLI en lugar de suma cruda (maneja colinealidad)",
        quant_v2_vol: "Volatilidad rolling de 52 semanas para bandas adaptativas",
        oos_metrics: "Métricas Fuera de Muestra",
        model_params: "Parámetros del Modelo",
        quant_chart_desc: "La deriva acumulativa del modelo puede causar divergencia con el tiempo.",
        interp_regression: "Regresión usando:",
        interp_gli_lag: "GLI (retardo 45d)",
        interp_cli_lag: "CLI (retardo 14d)",
        interp_vix_coin: "VIX (coincidente)",
        interp_netliq_lag: "Liq Neta EE.UU. (retardo 30d)",
        interp_zones: "Zonas de Desviación",
        interp_extreme: "±2σ: Sobre/infravaloración extrema",
        interp_moderate: "±1σ: Desviación moderada",
        interp_fair_range: "Dentro de ±1σ: Rango de valor justo",
        interp_signals: "Señales de Trading",
        interp_profittaking: "Z > +2: Considerar toma de beneficios",
        interp_accumulation: "Z < -2: Acumulación potencial",
        interp_divergence: "Divergencia ROC: Cambios de momentum",
        // Data Health & Pulse
        data_health: "Salud y Cobertura de Datos",
        series: "Serie",
        freshness: "Antigüedad",
        real_date: "Fecha Real",
        coverage: "Cobertura",
        active_cbs: "Bancos Activos",
        impulse_analysis: "Análisis de Impulso de Liquidez",
        chart_impulse_desc: "Comparación del momentum de GLI, Liquidez Neta y condiciones de Crédito (Z-Scores Normalizados). Las divergencias suelen liderar el precio de BTC.",
        btc_roc_overlay: "Superposición ROC BTC",
        period: "Periodo",
        lag_days: "Retardo (Días)",
        // Macro Regimes
        regime_bullish: "Macro Alcista",
        regime_bearish: "Macro Bajista",
        regime_global_inj: "Inyección Global",
        regime_us_inj: "Inyección EE.UU.",
        regime_early_warning: "Aviso Temprano",
        regime_losing_steam: "Perdiendo Fuelle",
        regime_neutral: "Neutral / Transición",
        regime_signal: "Pulso Macro y Régimen",
        regime_chart_desc: "Precio BTC (Log) vs Régimen Macro. El fondo rastrea liquidez Global (GLI) y EE.UU. (NetLiq). Verde: Expansión Dual (Alcista). Rojo: Contracción Dual (Bajista). Gris: Neutral.",
        regime_formula_title: "Fórmula del Régimen",
        regime_formula_desc: "Score = 50 + 15 × Total_Z | Liquidez (35% GLI + 35% NetLiq + 20% M2 ± amplitud CB) + Crédito (60% CLI + 40% momentum CLI) - Frenos (tasas reales + estrés repo + escasez reservas)",
        regime_score_bullish: "Score > 50: Sesgo alcista (verde) → Liquidez expandiéndose, crédito relajándose",
        regime_score_bearish: "Score < 50: Sesgo bajista (rojo) → Liquidez contrayéndose, crédito endureciéndose",
        // Signal Reasons - HY Spread
        signal_hy_bullish: "HY spread contraído: apetito por riesgo, crédito fácil.",
        signal_hy_bearish: "HY spread ampliado: aversión al riesgo, estrés crediticio.",
        signal_hy_neutral: "HY spread en rango normal, sin señal extrema.",
        // Signal Reasons - IG Spread
        signal_ig_bullish: "IG spread bajo: condiciones crediticias sólidas.",
        signal_ig_bearish: "IG spread elevado: tensión en mercado de crédito.",
        signal_ig_neutral: "IG spread estable, condiciones normales.",
        // Signal Reasons - NFCI Credit
        signal_nfci_credit_bullish: "NFCI Credit negativo: condiciones crediticias laxas.",
        signal_nfci_credit_bearish: "NFCI Credit positivo: condiciones crediticias restrictivas.",
        signal_nfci_credit_neutral: "NFCI Credit neutral, sin presión extrema.",
        // Signal Reasons - NFCI Risk
        signal_nfci_risk_bullish: "NFCI Risk bajo: riesgo sistémico contenido.",
        signal_nfci_risk_bearish: "NFCI Risk elevado: mayor riesgo sistémico percibido.",
        signal_nfci_risk_neutral: "NFCI Risk en niveles normales.",
        // Signal Reasons - Lending
        signal_lending_bullish: "Estándares de crédito relajados: expansión crediticia.",
        signal_lending_bearish: "Estándares restrictivos: contracción crediticia.",
        signal_lending_neutral: "Estándares de préstamo sin cambio significativo.",
        // Signal Reasons - VIX
        signal_vix_bullish: "VIX bajo: complacencia/confianza en el mercado.",
        signal_vix_bearish: "VIX elevado: miedo y volatilidad en el mercado.",
        signal_vix_neutral: "VIX en rango normal, volatilidad moderada.",
        // Signal Reasons - CLI
        signal_cli_bullish: "CLI indica expansión crediticia y apetito por riesgo.",
        signal_cli_bearish: "CLI indica contracción crediticia y aversión al riesgo.",
        signal_cli_neutral: "CLI neutral, condiciones de liquidez equilibradas.",
        // Signal Reasons - Repo
        signal_repo_bullish: "SOFR ≈ IORB: liquidez interbancaria adecuada.",
        signal_repo_bearish: "SOFR >> IORB: tensión de liquidez en repo.",
        signal_repo_neutral: "Spread repo en rangos normales.",
        signal_repo_warning: "SOFR << IORB: exceso de liquidez (inusual).",
        // Signal Reasons - TIPS
        signal_tips_bullish: "Reflación: BE alto + RR bajo. Fed dovish, expansión económica.",
        signal_tips_bearish: "Tightening: RR alto + BE bajo. Fed hawkish, restricción monetaria.",
        signal_tips_neutral: "Goldilocks: BE y RR en rango normal, equilibrio macro.",
        signal_tips_warning: "Stagflation: Inflación alta + Fed hawkish. Condiciones adversas.",
        signal_tips_disinflation: "Desinflación: BE y RR bajos. Posible desaceleración o deflación.",
    },
};

// Derived store for current translations based on language
export const currentTranslations = derived(language, ($lang) => translations[$lang] || translations.en);

/**
 * Translation helper function.
 * Use with $currentTranslations in components.
 * @param {object} trans - The $currentTranslations store value
 * @param {string} key - Translation key
 * @returns {string}
 */
export const t = (trans, key) => trans[key] || translations.en[key] || key;

// Theme management functions
export function initSettings() {
    if (typeof localStorage !== 'undefined') {
        const savedTheme = localStorage.getItem('theme');
        const savedLang = localStorage.getItem('language');

        darkMode.set(savedTheme === 'dark');
        language.set(savedLang || 'en');
        applyTheme(savedTheme === 'dark');
    }
}

export function toggleDarkMode() {
    darkMode.update(current => {
        const newValue = !current;
        if (typeof localStorage !== 'undefined') {
            localStorage.setItem('theme', newValue ? 'dark' : 'light');
        }
        applyTheme(newValue);
        return newValue;
    });
}

export function toggleLanguage() {
    language.update(current => {
        const newLang = current === 'en' ? 'es' : 'en';
        if (typeof localStorage !== 'undefined') {
            localStorage.setItem('language', newLang);
        }
        return newLang;
    });
}

function applyTheme(isDark) {
    if (typeof document !== 'undefined') {
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    }
}
