<script>
  import { onMount } from "svelte";
  import {
    fetchData,
    dashboardData,
    latestStats,
    isLoading,
    error,
  } from "./stores/dataStore";
  import StatsCard from "./lib/components/StatsCard.svelte";
  import Chart from "./lib/components/Chart.svelte";
  import LightweightChart from "./lib/components/LightweightChart.svelte";
  import SignalBadge from "./lib/components/SignalBadge.svelte";
  import TimeRangeSelector from "./lib/components/TimeRangeSelector.svelte";

  // Dark mode state
  let darkMode = false;

  // Language state (default: English)
  let language = "en";

  // Translations for chart descriptions
  const translations = {
    en: {
      gli: "Sum of global central bank balance sheets in USD. ↑ Expansion = Liquidity injection (bullish) | ↓ Contraction = QT (bearish)",
      gli_cb:
        "Individual central bank assets in USD. Larger = more weight in global liquidity.",
      btc_fair:
        "BTC fair value derived from macro liquidity factors. Price above = overvalued, below = undervalued.",
      btc_bands:
        "±1σ/2σ bands show historical deviation range. Mean-reverts over time.",
      net_liq:
        "Fed Balance Sheet minus TGA and RRP. Key driver of US dollar liquidity.",
      rrp: "Reverse Repo drains liquidity from the system. ↓ RRP = Liquidity release (bullish)",
      tga: "Treasury General Account. ↓ TGA = Treasury spending = Liquidity injection",
      m2_global:
        "Global money supply in USD. Leading indicator for asset prices (45-90 day lag).",
      m2_country: "Country M2 money supply in local currency converted to USD.",
      cli: "Aggregates credit conditions, volatility, and lending. ↑ CLI = Easier credit (bullish) | ↓ Contraction = Tighter (bearish)",
      hy_spread:
        "High Yield bond spreads vs Treasuries. ↓ Spread = Risk-on (bullish) | ↑ Spread = Risk-off",
      ig_spread:
        "Investment Grade spreads. ↓ Spread = Credit easing | ↑ Spread = Credit stress",
      nfci_credit:
        "Fed's NFCI Credit subindex. ↓ Below 0 = Loose conditions | ↑ Above 0 = Tight",
      nfci_risk:
        "Fed's NFCI Risk subindex. ↓ Below 0 = Low fear | ↑ Above 0 = Elevated fear",
      lending:
        "Senior Loan Officer Survey. ↑ Tightening = Banks restrict credit | ↓ Easing = Free lending",
      vix: "Implied volatility (fear gauge). Z>2 = Panic | Z<-1 = Complacency. Mean-reverts.",
      tips: "Breakeven (amber): Inflation expectations. Real Rate (blue): True cost of money. 5Y5Y (green): Long-term anchor.",
      bank_reserves:
        "Total reserves maintained by depository institutions at Federal Reserve Banks. When reserves fall, liquidity stress increases.",
      repo_stress:
        "Comparison between SOFR (market rate) and IORB (Fed floor). If SOFR stays above IORB, it indicates systemic liquidity shortage.",
      // Navigation
      nav_dashboard: "Dashboard",
      nav_gli: "Global Flows CB",
      nav_m2: "Global M2",
      nav_us_system: "US System",
      nav_risk_model: "Risk Model",
      nav_btc_analysis: "BTC Analysis",
      nav_btc_quant: "BTC Quant v2",
      // Header & Global
      header_desc:
        "Real-time macro liquidity and credit monitoring across 5 major central banks",
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
      impact_note_gli:
        "* Impact = % contribution of bank's 1M move to total Global Liquidity.",
      impact_note_us:
        "* Imp = Contribution to US Net Liquidity change. RRP/TGA have an inverse effect.",
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
      flow_desc:
        "Impulse tracks the rate of change in liquidity flows. Acceleration captures regime shifts.",
      gli_impulse: "GLI Impulse (13W)",
      m2_impulse: "M2 Impulse (13W)",
      cb_contribution: "CB Contribution to ΔGLI",
      // Formatting
      spot_usd: "Spot USD",
      const_fx: "Const FX",
      // BTC Analysis tab
      btc_analysis_title: "BTC Fair Value Model",
      btc_analysis_desc:
        "Bitcoin fair value derived from global liquidity, M2, and credit conditions. Price above line = overvalued, below = undervalued.",
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
      quant_v2_desc:
        "This model addresses econometric issues in the legacy model:",
      quant_v2_weekly:
        "Weekly frequency (W-FRI) instead of daily to avoid FRI autocorrelation",
      quant_v2_log:
        "Δlog(BTC) returns instead of log levels (avoids spurious regression)",
      quant_v2_elastic:
        "ElasticNet with 1-8 week lags for automatic feature selection",
      quant_v2_pca: "PCA GLI factor instead of raw sum (handles colinearity)",
      quant_v2_vol: "Rolling 52-week volatility for adaptive bands",
      oos_metrics: "Out-of-Sample Metrics",
      model_params: "Model Parameters",
      quant_chart_desc:
        "Cumulative model drift may cause divergence over time.",
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
      chart_impulse_desc:
        "Comparing the momentum of GLI, Net Liquidity, and Credit conditions (Normalized Z-Scores). Divergences often lead BTC price action.",
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
      regime_chart_desc:
        "Log-scale BTC Price overlaid on Macro Regime. Background tracks combined Global (GLI) and US (NetLiq) liquidity momentum. Green: Dual Expansion (Bullish). Red: Dual Contraction (Bearish). Grey: Mixed/Neutral.",
    },
    es: {
      gli: "Suma de balances de bancos centrales en USD. ↑ Expansión = Inyección de liquidez (alcista) | ↓ Contracción = QT (bajista)",
      gli_cb:
        "Activos individuales de bancos centrales en USD. Mayor = más peso en liquidez global.",
      btc_fair:
        "Valor justo de BTC derivado de factores macro. Precio arriba = sobrevalorado, abajo = infravalorado.",
      btc_bands:
        "Bandas ±1σ/2σ muestran rango de desviación histórica. Revierte a la media.",
      net_liq:
        "Balance de la Fed menos TGA y RRP. Motor clave de liquidez del dólar.",
      rrp: "Repo Inverso drena liquidez del sistema. ↓ RRP = Liberación de liquidez (alcista)",
      tga: "Cuenta General del Tesoro. ↓ TGA = Gasto del Tesoro = Inyección de liquidez",
      m2_global:
        "Oferta monetaria global en USD. Indicador adelantado de precios (45-90 días de retardo).",
      m2_country: "M2 del país en moneda local convertida a USD.",
      cli: "Agrega condiciones crediticias, volatilidad y préstamos. ↑ CLI = Crédito fácil (alcista) | ↓ CLI = Más estricto",
      hy_spread:
        "Spreads de bonos High Yield vs Treasuries. ↓ Spread = Risk-on (alcista) | ↑ = Risk-off",
      ig_spread:
        "Spreads de grado de inversión. ↓ Spread = Crédito relajado | ↑ = Estrés crediticio",
      nfci_credit:
        "Subíndice de crédito NFCI de la Fed. ↓ Bajo 0 = Condiciones laxas | ↑ Sobre 0 = Estrictas",
      nfci_risk:
        "Subíndice de riesgo NFCI. ↓ Bajo 0 = Bajo miedo | ↑ Sobre 0 = Miedo elevado",
      lending:
        "Encuesta de préstamos bancarios. ↑ Endurecimiento = Restringen crédito | ↓ = Prestan libremente",
      vix: "Volatilidad implícita (indicador de miedo). Z>2 = Pánico | Z<-1 = Complacencia.",
      tips: "Breakeven (ámbar): Expectativas de inflación. Tasa Real (azul): Coste real del dinero. 5Y5Y (verde): Anclaje a largo plazo.",
      bank_reserves:
        "Reservas totales mantenidas por instituciones depositarias en los Bancos de la Reserva Federal. Cuando las reservas caen, el estrés de liquidez aumenta.",
      repo_stress:
        "Comparativa entre el SOFR (tipo de mercado) y el IORB (suelo de la Fed). Si el SOFR se mantiene por encima del IORB, indica escasez sistémica de liquidez.",
      // Navigation
      nav_dashboard: "Panel de Control",
      nav_gli: "Flujos Globales CB",
      nav_m2: "M2 Global",
      nav_us_system: "Sistema EE.UU.",
      nav_risk_model: "Modelo de Riesgo",
      nav_btc_analysis: "Análisis BTC",
      nav_btc_quant: "BTC Quant v2",
      // Header & Global
      header_desc:
        "Monitoreo en tiempo real de liquidez macro y crédito en 5 bancos centrales",
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
      impact_note_gli:
        "* Impacto = % contribución del movimiento 1M del banco a la Liquidez Global total.",
      impact_note_us:
        "* Imp = Contribución al cambio de Liquidez Neta de EE.UU. RRP/TGA tienen un efecto inverso.",
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
      flow_desc:
        "El impulso rastrea la tasa de cambio en los flujos. La aceleración captura cambios de régimen.",
      gli_impulse: "Impulso GLI (13S)",
      m2_impulse: "Impulso M2 (13S)",
      cb_contribution: "Contribución CB a ΔGLI",
      // Formatting
      spot_usd: "Spot USD",
      const_fx: "FX Const",
      // BTC Analysis tab
      btc_analysis_title: "Modelo de Valor Justo de BTC",
      btc_analysis_desc:
        "Valor justo de Bitcoin derivado de liquidez global, M2 y condiciones de crédito. Precio arriba = sobrevalorado, abajo = infravalorado.",
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
      quant_v2_desc:
        "Este modelo aborda problemas econométricos del modelo anterior:",
      quant_v2_weekly:
        "Frecuencia semanal (W-VIE) en lugar de diaria para evitar autocorrelación",
      quant_v2_log:
        "Retornos Δlog(BTC) en lugar de niveles log (evita regresión espuria)",
      quant_v2_elastic:
        "ElasticNet con retardos de 1-8 semanas para selección automática",
      quant_v2_pca:
        "Factor PCA GLI en lugar de suma cruda (maneja colinealidad)",
      quant_v2_vol: "Volatilidad rolling de 52 semanas para bandas adaptativas",
      oos_metrics: "Métricas Fuera de Muestra",
      model_params: "Parámetros del Modelo",
      quant_chart_desc:
        "La deriva acumulativa del modelo puede causar divergencia con el tiempo.",
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
      chart_impulse_desc:
        "Comparación del momentum de GLI, Liquidez Neta y condiciones de Crédito (Z-Scores Normalizados). Las divergencias suelen liderar el precio de BTC.",
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
      regime_chart_desc:
        "Precio BTC (Log) vs Régimen Macro. El fondo rastrea liquidez Global (GLI) y EE.UU. (NetLiq). Verde: Expansión Dual (Alcista). Rojo: Contracción Dual (Bajista). Gris: Neutral.",
    },
  };

  // Reactive translations - updates when language changes
  $: currentTranslations = translations[language] || translations.en;

  // Helper to get translation (uses reactive currentTranslations)
  const t = (key) => currentTranslations[key] || translations.en[key] || key;

  // Initialize from localStorage on mount
  onMount(() => {
    const savedTheme = localStorage.getItem("theme");
    const savedLang = localStorage.getItem("language");
    darkMode = savedTheme === "dark";
    language = savedLang || "en";
    applyTheme();
  });

  function toggleDarkMode() {
    darkMode = !darkMode;
    localStorage.setItem("theme", darkMode ? "dark" : "light");
    applyTheme();
  }

  function toggleLanguage() {
    language = language === "en" ? "es" : "en";
    localStorage.setItem("language", language);
  }

  function applyTheme() {
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute(
        "data-theme",
        darkMode ? "dark" : "light",
      );
    }
  }

  // Individual time range state for each chart section
  let gliRange = "ALL";
  let fedRange = "ALL";
  let ecbRange = "ALL";
  let bojRange = "ALL";
  let boeRange = "ALL";
  let pbocRange = "ALL";
  let bocRange = "ALL",
    rbaRange = "ALL",
    snbRange = "ALL",
    bokRange = "ALL";
  let rbiRange = "ALL",
    cbrRange = "ALL",
    bcbRange = "ALL",
    rbnzRange = "ALL",
    srRange = "ALL",
    bnmRange = "ALL";
  let netLiqRange = "ALL";
  let cliRange = "ALL";
  let impulseRange = "ALL";
  let inflationRange = "ALL";
  let btcRange = "ALL";
  let m2Range = "ALL";
  let vixRange = "ALL";
  let spreadRange = "ALL";
  let hyRange = "ALL",
    igRange = "ALL",
    nfciRange = "ALL",
    lendingRange = "ALL",
    reservesRange = "ALL",
    repoStressRange = "ALL",
    tgaRange = "ALL",
    rrpRange = "ALL";

  // Individual M2 time ranges
  let usM2Range = "ALL",
    euM2Range = "ALL",
    cnM2Range = "ALL",
    jpM2Range = "ALL",
    ukM2Range = "ALL";
  let caM2Range = "ALL",
    auM2Range = "ALL",
    inM2Range = "ALL",
    chM2Range = "ALL",
    ruM2Range = "ALL";
  let brM2Range = "ALL",
    krM2Range = "ALL",
    mxM2Range = "ALL",
    myM2Range = "ALL";

  // GLI FX mode: false = Spot USD, true = Constant FX (2019-12-31)

  // GLI FX mode: false = Spot USD, true = Constant FX (2019-12-31)
  let gliShowConstantFx = false;

  // Helper to get cutoff date based on range
  const getCutoffDate = (range) => {
    if (range === "ALL") return null;
    const now = new Date();
    switch (range) {
      case "1M":
        return new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
      case "3M":
        return new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
      case "6M":
        return new Date(now.getFullYear(), now.getMonth() - 6, now.getDate());
      case "1Y":
        return new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
      case "3Y":
        return new Date(now.getFullYear() - 3, now.getMonth(), now.getDate());
      case "5Y":
        return new Date(now.getFullYear() - 5, now.getMonth(), now.getDate());
      default:
        return null;
    }
  };

  // Filter dates array and get valid indices for Plotly charts
  const getFilteredIndices = (dates, range) => {
    if (!dates || !Array.isArray(dates) || range === "ALL") {
      return dates ? dates.map((_, i) => i) : [];
    }
    const cutoff = getCutoffDate(range);
    if (!cutoff) return dates.map((_, i) => i);

    return dates.reduce((acc, d, i) => {
      const date = new Date(d);
      if (date >= cutoff) acc.push(i);
      return acc;
    }, []);
  };

  // Helper to filter Plotly trace data
  const filterPlotlyData = (traceArray, dates, range) => {
    if (!traceArray || !dates || !dates.length) return traceArray;

    let indices;
    if (range === "ALL") {
      // Auto-trim: Find the first index where ANY trace has non-zero/non-null data
      let firstValidIdx = -1;
      for (let i = 0; i < dates.length; i++) {
        const hasData = traceArray.some((trace) => {
          const val = trace.y[i];
          return val !== null && val !== undefined && val !== 0;
        });
        if (hasData) {
          firstValidIdx = i;
          break;
        }
      }
      if (firstValidIdx === -1) return traceArray; // No valid data found at all
      indices = dates.slice(firstValidIdx).map((_, i) => i + firstValidIdx);
    } else {
      indices = getFilteredIndices(dates, range);
    }

    return traceArray.map((trace) => ({
      ...trace,
      x: indices.map((i) => trace.x[i]),
      y: indices.map((i) => trace.y[i]),
    }));
  };

  const formatTV = (dates, values) => {
    if (!dates || !values || !Array.isArray(dates)) return [];
    const points = [];
    for (let i = 0; i < dates.length; i++) {
      const val = values[i];
      if (val === null || val === undefined || isNaN(val) || val <= 0) continue;
      const dateStr = dates[i]; // Backend already provides YYYY-MM-DD
      if (!dateStr || typeof dateStr !== "string") continue;
      points.push({ time: dateStr, value: val });
    }
    // High-performance chronological sort
    return points.sort((a, b) => (a.time > b.time ? 1 : -1));
  };

  // Create LightweightChart series config with time range filtering
  const formatLC = (dates, values, range, name, color, type = "line") => {
    if (!dates || !values) return [];

    // Get cutoff date for filtering
    const cutoff = getCutoffDate(range);

    const points = [];
    for (let i = 0; i < dates.length; i++) {
      const val = values[i];
      if (val === null || val === undefined || isNaN(val)) continue;
      const dateStr = dates[i];
      if (!dateStr || typeof dateStr !== "string") continue;

      // Apply time range filter
      if (cutoff) {
        const pointDate = new Date(dateStr);
        if (pointDate < cutoff) continue;
      }

      points.push({ time: dateStr, value: val });
    }

    const sortedPoints = points.sort((a, b) => (a.time > b.time ? 1 : -1));

    return [
      {
        name,
        type,
        color,
        data: sortedPoints,
        width: 2,
      },
    ];
  };

  let currentTab = "Dashboard";
  let selectedBtcModel = "macro"; // "macro" or "adoption"
  let selectedLagWindow = "7d"; // "7d" | "14d" | "30d"

  onMount(() => {
    fetchData();
  });

  const setTab = (tab) => {
    currentTab = tab;
  };

  $: activeBtcModel = $dashboardData.btc?.models?.[selectedBtcModel] || {
    fair_value: [],
    upper_1sd: [],
    lower_1sd: [],
    upper_2sd: [],
    lower_2sd: [],
    deviation_pct: [],
    deviation_zscore: [],
  };

  // --- Chart Data Definitions (filtered by globalTimeRange) ---
  // Use gliDataSource based on toggle (Spot USD vs Constant FX)
  $: gliDataSource = gliShowConstantFx
    ? $dashboardData.gli.constant_fx
    : $dashboardData.gli.total;
  $: gliDataRaw = [
    {
      x: $dashboardData.dates,
      y: gliDataSource,
      name: gliShowConstantFx ? "GLI Constant-FX" : "GLI Total (Spot USD)",
      type: "scatter",
      mode: "lines",
      fill: "tozeroy",
      line: {
        color: gliShowConstantFx ? "#10b981" : "#6366f1",
        width: 3,
        shape: "spline",
      },
      fillcolor: gliShowConstantFx
        ? "rgba(16, 185, 129, 0.05)"
        : "rgba(99, 102, 241, 0.05)",
    },
  ];
  $: gliData = filterPlotlyData(gliDataRaw, $dashboardData.dates, gliRange);

  $: fedDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.fed,
      name: "Fed Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(59, 130, 246, 0.05)",
    },
  ];
  $: fedData = filterPlotlyData(fedDataRaw, $dashboardData.dates, fedRange);

  $: ecbDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.ecb,
      name: "ECB Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#8b5cf6", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(139, 92, 246, 0.05)",
    },
  ];
  $: ecbData = filterPlotlyData(ecbDataRaw, $dashboardData.dates, ecbRange);

  $: bojDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.boj,
      name: "BoJ Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#f43f5e", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(244, 63, 94, 0.05)",
    },
  ];
  $: bojData = filterPlotlyData(bojDataRaw, $dashboardData.dates, bojRange);

  $: boeDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.boe,
      name: "BoE Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(245, 158, 11, 0.05)",
    },
  ];
  $: boeData = filterPlotlyData(boeDataRaw, $dashboardData.dates, boeRange);

  $: pbocDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.pboc,
      name: "PBoC Assets (M2Proxy)",
      type: "scatter",
      mode: "lines",
      line: { color: "#10b981", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(16, 185, 129, 0.05)",
    },
  ];
  $: pbocData = filterPlotlyData(pbocDataRaw, $dashboardData.dates, pbocRange);

  $: bocDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.boc,
      name: "BoC Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#34d399", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(52, 211, 153, 0.05)",
    },
  ];
  $: bocData = filterPlotlyData(bocDataRaw, $dashboardData.dates, bocRange);

  let btcRocPeriod = 21; // Default 1 Month (21 trading days)
  let btcLag = 0; // Default 0 lag
  let regimeLag = 72; // Default 72 days lag for Regime Chart
  let normalizeImpulse = true; // Always Normalized (Z-Score)
  let showComposite = false; // Toggle for Composite Aggregate Signal
  let optimalLagLabel = "N/A"; // Display string for UI

  function calculateCorrelation(xArray, yArray) {
    if (
      !xArray ||
      !yArray ||
      xArray.length !== yArray.length ||
      xArray.length < 2
    )
      return 0;

    let sumX = 0,
      sumY = 0,
      sumXY = 0,
      sumX2 = 0,
      sumY2 = 0,
      n = 0;
    for (let i = 0; i < xArray.length; i++) {
      const x = xArray[i];
      const y = yArray[i];
      if (x !== null && x !== undefined && y !== null && y !== undefined) {
        sumX += x;
        sumY += y;
        sumXY += x * y;
        sumX2 += x * x;
        sumY2 += y * y;
        n++;
      }
    }
    if (n < 2) return 0;

    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt(
      (n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY),
    );
    return denominator === 0 ? 0 : numerator / denominator;
  }

  function findOptimalLag(
    dates,
    signalValues,
    btcRocValues,
    minLag = -15,
    maxLag = 120,
  ) {
    // We want to find shift 'k' for signalValues that maximizes correlation with btcRocValues.
    // btcRocValues stays fixed (associated with 'dates').
    // signalValues[i] is at dates[i].
    // shiftedSignal[i] = signalValues[i - k] ... wait.
    // logic: shiftData(dates, values, k) returns aligned arrays.
    // We can use shiftData inside loop.

    let bestLag = 0;
    let maxCorr = -1;

    // Optimization: btcRoc is sparse? No, it's mapped to dates.
    // But btcRoc might have nulls at start.

    // Create a Map for BTC ROC to speed up? array access is O(1).
    // Dates align by index i.

    for (let k = minLag; k <= maxLag; k += 3) {
      // Step 3 days for speed
      // Simplified shift logic for correlation only (no need for dates array construction)
      // Shift +k: signal[i] moves to dates[i+k].
      // So we compare signal[i] vs btcRoc[i+k].

      const x = [];
      const y = [];

      for (let i = 0; i < signalValues.length; i++) {
        let j = i + k; // shifted index
        if (j >= 0 && j < btcRocValues.length) {
          const sig = signalValues[i];
          const roc = btcRocValues[j];
          if (sig != null && roc != null) {
            x.push(sig);
            y.push(roc);
          }
        }
      }

      const r = calculateCorrelation(x, y);
      if (r > maxCorr) {
        maxCorr = r;
        bestLag = k;
      }
    }
    return { lag: bestLag, corr: maxCorr };
  }

  function calculateZScore(values) {
    if (!values || values.length === 0) return [];
    const valid = values.filter((v) => v !== null && v !== undefined);
    if (valid.length < 2) return values;

    const mean = valid.reduce((a, b) => a + b, 0) / valid.length;
    const variance =
      valid.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / valid.length;
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return values.map(() => 0);

    return values.map((v) =>
      v === null || v === undefined ? null : (v - mean) / stdDev,
    );
  }

  function calculateBtcRoc(prices, dates, period, lag = 0) {
    if (!prices || !dates || prices.length !== dates.length) return [];

    // Valid period check
    if (period <= 0) return [];

    const rocData = [];

    // Lag: if lag > 0, we behave as if the ROC happened 'lag' days later/earlier?
    // In this specific implementation for generic use:
    // If we want to align price with lagged signal, we might need lag.
    // However, the caller currently uses lag=0.
    // We will just return the raw ROC aligned with dates[i].

    for (let i = period; i < prices.length; i++) {
      const current = prices[i];
      const past = prices[i - period];

      if (past && past !== 0) {
        const roc = ((current - past) / past) * 100;

        // Align with Date[i]
        // If we supported shifting here, we'd adjust the date index.
        // For now, strict calendar alignment.
        rocData.push({ x: dates[i], y: roc });
      }
    }
    return rocData;
  }

  function calculateHistoricalRegimes(dates, gli, netliq) {
    if (!dates || !gli || !netliq) return [];

    const shapes = [];
    let currentRegime = null;
    let startIdx = 0;

    for (let i = 0; i < dates.length; i++) {
      const g = gli[i];
      const n = netliq[i];
      let r = "neutral";

      if (g > 0 && n > 0) r = "bullish";
      else if (g < 0 && n < 0) r = "bearish";

      if (r !== currentRegime) {
        if (currentRegime !== null) {
          shapes.push({
            type: "rect",
            xref: "x",
            yref: "paper",
            x0: dates[startIdx],
            x1: dates[i],
            y0: 0,
            y1: 1,
            fillcolor:
              currentRegime === "bullish"
                ? "rgba(16, 185, 129, 0.08)"
                : currentRegime === "bearish"
                  ? "rgba(239, 68, 68, 0.08)"
                  : "rgba(148, 163, 184, 0.03)",
            line: { width: 0 },
            layer: "below",
          });
        }
        currentRegime = r;
        startIdx = i;
      }
    }
    // Final shape
    if (currentRegime !== null) {
      shapes.push({
        type: "rect",
        xref: "x",
        yref: "paper",
        x0: dates[startIdx],
        x1: dates[dates.length - 1],
        y0: 0,
        y1: 1,
        fillcolor:
          currentRegime === "bullish"
            ? "rgba(16, 185, 129, 0.08)"
            : currentRegime === "bearish"
              ? "rgba(239, 68, 68, 0.08)"
              : "rgba(148, 163, 184, 0.03)",
        line: { width: 0 },
        layer: "below",
      });
    }
    return shapes;
  }

  $: regimeLCData = (() => {
    if (
      !$dashboardData.dates ||
      !$dashboardData.btc ||
      !$dashboardData.btc.price
    )
      return [];

    const dates = $dashboardData.dates;
    const prices = $dashboardData.btc.price;
    const gli = $dashboardData.flow_metrics?.gli_impulse_13w || [];
    const netliq = $dashboardData.flow_metrics?.net_liquidity_impulse_13w || [];

    const bgData = [];
    const btcData = [];

    // Helper to add days to YYYY-MM-DD
    const addDays = (dateStr, days) => {
      const d = new Date(dateStr);
      d.setDate(d.getDate() + days);
      return d.toISOString().split("T")[0];
    };

    const lastDate = dates[dates.length - 1];

    // BTC Price Data (Normal loop)
    for (let i = 0; i < dates.length; i++) {
      if (prices[i] !== undefined && prices[i] !== null) {
        btcData.push({ time: dates[i], value: prices[i] });
      }
    }

    // Regime Background Data (Extended loop)
    // We iterate through all AVAILABLE signals.
    // Signal at index 'i' determines Regime at 'i + regimeLag'.
    // So we loop 'i' from 0 to dates.length.
    // The target date is dates[i + regimeLag] (or projected if out of bounds).

    for (let i = 0; i < dates.length; i++) {
      if (gli[i] !== undefined && netliq[i] !== undefined) {
        const g = gli[i];
        const n = netliq[i];
        let color = "rgba(148, 163, 184, 0.08)"; // Neutral
        if (g > 0 && n > 0)
          color = "rgba(16, 185, 129, 0.15)"; // Bullish Green
        else if (g < 0 && n < 0) color = "rgba(239, 68, 68, 0.15)"; // Bearish Red

        // Calculate Target Date
        let targetDate;
        const targetIdx = i + regimeLag;

        if (targetIdx < dates.length) {
          targetDate = dates[targetIdx];
        } else {
          // Future projection
          if (lastDate) {
            const daysToAdd = targetIdx - (dates.length - 1);
            targetDate = addDays(lastDate, daysToAdd);
          }
        }

        if (targetDate) {
          bgData.push({ time: targetDate, value: 1, color });
        }
      }
    }

    return [
      {
        name: "Regime",
        type: "histogram",
        data: bgData,
        color: "transparent",
        options: {
          priceScaleId: "left",
          priceFormat: { type: "custom", formatter: () => "" },
          scaleMargins: { top: 0, bottom: 0 },
        },
      },
      {
        name: "BTC Price",
        type: "area",
        data: btcData,
        color: "#94a3b8",
        topColor: "rgba(148, 163, 184, 0.4)",
        bottomColor: "rgba(148, 163, 184, 0.01)",
        width: 2,
      },
    ];
  })();

  // --- Signal Lagging Logic ---
  // We want to shift GLI, NetLiq, and CLI traces by 'btcLag' (renamed conceptually to 'signalOffset') days.
  // If Lag > 0, we shift signals FORWARD (Right) to see if they lead Price.
  // Ideally, if Signal(t) predicts Price(t+lag), we shift Signal(t) to t+lag.

  function shiftData(dates, values, lagDays) {
    if (!dates || !values || dates.length !== values.length)
      return { x: dates || [], y: values || [] };
    if (lagDays === 0) return { x: dates, y: values };

    // Since dates are strings YYYY-MM-DD, we assume index shifting is sufficient if data is daily.
    // 1 index approx 1 day (trading day).
    // Shift Right (Positive Lag): Prepend nulls/cut start, or simply shift the x-axis?
    // Easiest is to keep Y values and SHIFT X array.
    // If we shift signal to the right, Signal[i] happens at Date[i+lag].

    // Actually, easier way for Plotly:
    // If we want to move line to the RIGHT (+), we add days to the date object.
    // But we have a discrete date list.
    // Let's use index shifting.

    const shiftedX = [];
    const shiftedY = [];

    for (let i = 0; i < values.length; i++) {
      const targetIdx = i + lagDays;
      if (targetIdx >= 0 && targetIdx < dates.length) {
        shiftedX.push(dates[targetIdx]);
        shiftedY.push(values[i]);
      }
    }
    return { x: shiftedX, y: shiftedY };
  }

  // --- Impulse Chart Data (Signals + BTC ROC) ---
  $: btcRocTrace = (() => {
    if (!$dashboardData.btc || !$dashboardData.btc.price) return null;
    const prices = $dashboardData.btc.price || [];
    const dates = $dashboardData.dates;
    if (!prices.length) return null;

    // Fixed BTC ROC (No Lag on BTC itself, it is the anchor)
    const computed = calculateBtcRoc(prices, dates, btcRocPeriod, 0);
    const yRaw = computed.map((p) => p.y);
    // Force Z-Score if Composite is ON (to match scale) or if Normalized is ON
    const useZ = normalizeImpulse || showComposite;
    const yFinal = useZ ? calculateZScore(yRaw) : yRaw;

    return {
      x: computed.map((p) => p.x),
      y: yFinal,
      name: `BTC ROC (${btcRocPeriod}d)${useZ ? " [Z]" : ""}`,
      type: "scatter",
      mode: "lines",
      line: { color: "#94a3b8", width: 2, dash: "solid" },
      yaxis: useZ ? "y" : "y2",
      opacity: 0.8,
    };
  })();

  // Composite Signal Calculation & Lag Finder
  $: compositeData = (() => {
    if (!showComposite || !$dashboardData.flow_metrics) return null;

    // Get Z-Scores of components
    const g = calculateZScore(
      $dashboardData.flow_metrics.gli_impulse_13w || [],
    );
    const n = calculateZScore(
      $dashboardData.flow_metrics.net_liquidity_impulse_13w || [],
    );
    const c = calculateZScore(
      $dashboardData.flow_metrics.cli_momentum_4w || [],
    );

    if (!g.length) return null;

    // Average Z-Score
    const comp = g.map((val, i) => {
      if (val == null || n[i] == null || c[i] == null) return null;
      return (val + n[i] + c[i]) / 3;
    });

    // Run Correlation Analysis
    const prices = $dashboardData.btc?.price || [];
    const fullRoc = prices.map((curr, i) => {
      if (i < btcRocPeriod) return null;
      const past = prices[i - btcRocPeriod];
      if (!past) return null;
      return ((curr - past) / past) * 100;
    });

    const best = findOptimalLag($dashboardData.dates, comp, fullRoc, 0, 120); // Scan 0 to 120 days positive lag
    optimalLagLabel = `Best Offset: +${best.lag}d (Corr: ${best.corr.toFixed(2)})`;

    return comp;
  })();

  $: compositeShifted = showComposite
    ? shiftData($dashboardData.dates, compositeData, btcLag)
    : null;

  $: gliImpulseShifted = shiftData(
    $dashboardData.dates,
    $dashboardData.flow_metrics?.gli_impulse_13w,
    btcLag,
  );
  $: netLiqImpulseShifted = shiftData(
    $dashboardData.dates,
    $dashboardData.flow_metrics?.net_liquidity_impulse_13w,
    btcLag,
  );
  $: cliMomentumShifted = shiftData(
    $dashboardData.dates,
    $dashboardData.flow_metrics?.cli_momentum_4w,
    btcLag,
  );

  $: gliY = normalizeImpulse
    ? calculateZScore(gliImpulseShifted.y)
    : gliImpulseShifted.y;
  $: netLiqY = normalizeImpulse
    ? calculateZScore(netLiqImpulseShifted.y)
    : netLiqImpulseShifted.y;
  $: cliY = normalizeImpulse
    ? calculateZScore(cliMomentumShifted.y)
    : cliMomentumShifted.y;

  $: impulseDataRaw = showComposite
    ? [
        {
          x: compositeShifted?.x || [],
          y: compositeShifted?.y || [],
          name:
            "Composite Liquidity (Z)" + (btcLag !== 0 ? ` [${btcLag}d]` : ""),
          type: "scatter",
          mode: "lines",
          line: { color: "#8b5cf6", width: 3, shape: "spline" }, // Violet
        },
        ...(btcRocTrace ? [btcRocTrace] : []),
      ]
    : [
        {
          x: gliImpulseShifted.x,
          y: gliY,
          name:
            "GLI Impulse (13W)" +
            (btcLag !== 0 ? ` [${btcLag > 0 ? "+" : ""}${btcLag}d]` : ""),
          type: "scatter",
          mode: "lines",
          line: { color: "#3b82f6", width: 2, shape: "spline" },
        },
        {
          x: netLiqImpulseShifted.x,
          y: netLiqY,
          name: "NetLiq Impulse (13W)",
          type: "scatter",
          mode: "lines",
          line: { color: "#10b981", width: 2, shape: "spline" },
        },
        {
          x: cliMomentumShifted.x,
          y: cliY,
          name: "CLI Momentum (4W)",
          type: "scatter",
          mode: "lines",
          line: { color: "#f59e0b", width: 2, shape: "spline" },
        },
        ...(btcRocTrace ? [btcRocTrace] : []),
      ];

  $: impulseData = filterPlotlyData(
    impulseDataRaw,
    $dashboardData.dates,
    impulseRange,
  );

  $: impulseLayout = {
    yaxis: {
      title:
        normalizeImpulse || showComposite
          ? "Z-Score (σ)"
          : "Impulse ($ Trillion)",
      gridcolor: darkMode ? "#334155" : "#e2e8f0",
    },
    yaxis2: {
      title: "BTC ROC (%)",
      overlaying: "y",
      side: "right",
      showgrid: false,
      visible: !(normalizeImpulse || showComposite),
    },
    margin: { t: 30, b: 30, l: 50, r: 50 },
    legend: { orientation: "h", y: 1.1 },
  };

  // Liquidity Score Logic (0-100)
  $: liquidityScore = (() => {
    const metrics = $dashboardData.flow_metrics;
    if (!metrics) return 50;

    let score = 50;
    // GLI Impulse (Global)
    const gli = getLatestValue(metrics.gli_impulse_13w) || 0;
    score += gli > 0 ? 15 : -15;

    // US Net Liquidity
    const netliq = getLatestValue(metrics.net_liquidity_impulse_13w) || 0;
    score += netliq > 0 ? 15 : -15;

    // CLI Momentum (Credit)
    const cli = getLatestValue(metrics.cli_momentum_4w) || 0;
    score += cli > 0 ? 10 : -10;

    // Acceleration (Derivative)
    const accel = getLatestValue(metrics.gli_accel) || 0;
    score += accel > 0 ? 10 : -10;

    return Math.max(0, Math.min(100, score));
  })();

  // Simplified Macro Regime Logic
  $: currentRegimeId = (() => {
    const gli = $dashboardData.flow_metrics?.gli_impulse_13w;
    const netliq = $dashboardData.flow_metrics?.net_liquidity_impulse_13w;

    if (!gli || !netliq || gli.length === 0) return "neutral";

    const lastGli = gli[gli.length - 1] || 0;
    const lastNetliq = netliq[netliq.length - 1] || 0;

    // Simplified Logic:
    // Bullish: Global AND US are expanding
    if (lastGli > 0 && lastNetliq > 0) return "bullish";
    // Bearish: Global AND US are contracting
    if (lastGli < 0 && lastNetliq < 0) return "bearish";

    // Everything else is Neutral/Mixed
    return "neutral";
  })();

  $: currentRegime = (() => {
    const isEs = language === "es";
    switch (currentRegimeId) {
      case "bullish":
        return {
          name: currentTranslations.regime_bullish,
          emoji: "🐂",
          color: "bullish",
          desc: isEs
            ? "Expansión Sincronizada: Tanto la liquidez Global como la de EE.UU. están expandiéndose."
            : "Synchronized Expansion: Both Global and US liquidity are expanding.",
          details: isEs
            ? "Entorno favorable para activos de riesgo."
            : "Favorable environment for risk assets.",
        };
      case "bearish":
        return {
          name: currentTranslations.regime_bearish,
          emoji: "🐻",
          color: "bearish",
          desc: isEs
            ? "Contracción Sincronizada: Tanto la liquidez Global como la de EE.UU. se están contrayendo."
            : "Synchronized Contraction: Both Global and US liquidity are contracting.",
          details: isEs
            ? "Entorno defensivo/adverso para activos de riesgo."
            : "Defensive/Headwind environment for risk assets.",
        };
      case "neutral":
      default:
        return {
          name: currentTranslations.regime_neutral,
          emoji: "⚖️",
          color: "neutral",
          desc: isEs
            ? "Régimen Mixto/Divergente: Señales contradictorias entre liquidez Global y doméstica."
            : "Mixed/Divergent Regime: Conflicting signals between Global and domestic liquidity.",
          details: isEs
            ? "Comportamiento lateral o errático esperado."
            : "Choppy or sideways price action expected.",
        };
    }
  })();

  $: rbaDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.rba,
      name: "RBA Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#fbbf24", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(251, 191, 36, 0.05)",
    },
  ];
  $: rbaData = filterPlotlyData(rbaDataRaw, $dashboardData.dates, rbaRange);

  $: snbDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.snb,
      name: "SNB Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#f87171", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(248, 113, 113, 0.05)",
    },
  ];
  $: snbData = filterPlotlyData(snbDataRaw, $dashboardData.dates, snbRange);

  $: bokDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.bok,
      name: "BoK Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#60a5fa", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(96, 165, 250, 0.05)",
    },
  ];
  $: bokData = filterPlotlyData(bokDataRaw, $dashboardData.dates, bokRange);

  $: rbiDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.rbi,
      name: "RBI Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#a78bfa", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(167, 139, 250, 0.05)",
    },
  ];
  $: rbiData = filterPlotlyData(rbiDataRaw, $dashboardData.dates, rbiRange);

  $: cbrDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.cbr,
      name: "CBR Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#fb7185", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(251, 113, 133, 0.05)",
    },
  ];
  $: cbrData = filterPlotlyData(cbrDataRaw, $dashboardData.dates, cbrRange);

  $: bcbDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.bcb,
      name: "BCB Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#4ade80", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(74, 222, 128, 0.05)",
    },
  ];
  $: bcbData = filterPlotlyData(bcbDataRaw, $dashboardData.dates, bcbRange);

  $: rbnzDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.rbnz,
      name: "RBNZ Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#22d3ee", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(34, 211, 238, 0.05)",
    },
  ];
  $: rbnzData = filterPlotlyData(rbnzDataRaw, $dashboardData.dates, rbnzRange);

  $: srDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.sr,
      name: "Riksbank Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#818cf8", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(129, 140, 248, 0.05)",
    },
  ];
  $: srData = filterPlotlyData(srDataRaw, $dashboardData.dates, srRange);

  $: bnmDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.bnm,
      name: "BNM Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#fb923c", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(251, 146, 60, 0.05)",
    },
  ];
  $: bnmData = filterPlotlyData(bnmDataRaw, $dashboardData.dates, bnmRange);

  $: netLiqDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.us_net_liq,
      name: "US Net Liquidity",
      type: "scatter",
      mode: "lines",
      fill: "tozeroy",
      line: { color: "#10b981", width: 3, shape: "spline" },
      fillcolor: "rgba(16, 185, 129, 0.05)",
    },
  ];
  $: netLiqData = filterPlotlyData(
    netLiqDataRaw,
    $dashboardData.dates,
    netLiqRange,
  );

  $: cliDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli,
      name: "CLI",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 3, shape: "spline" },
    },
  ];
  $: cliData = filterPlotlyData(cliDataRaw, $dashboardData.dates, cliRange);

  // TIPS / Inflation Expectations Data
  let tipsRange = "5Y";
  $: tipsDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.tips_breakeven,
      name: "10Y Breakeven Inflation",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 2, shape: "spline" },
      yaxis: "y",
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.tips_real_rate,
      name: "10Y Real Rate (TIPS Yield)",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 2, shape: "spline" },
      yaxis: "y2",
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.tips_5y5y_forward,
      name: "5Y5Y Forward Inflation",
      type: "scatter",
      mode: "lines",
      line: { color: "#10b981", width: 2, dash: "dash", shape: "spline" },
      yaxis: "y",
    },
  ];
  $: tipsData = filterPlotlyData(tipsDataRaw, $dashboardData.dates, tipsRange);
  $: tipsLayout = {
    yaxis: { title: "Inflation (%)", side: "left", showgrid: false },
    yaxis2: {
      title: "Real Rate (%)",
      overlaying: "y",
      side: "right",
      showgrid: false,
    },
    legend: { orientation: "h", y: 1.1 },
    margin: { t: 40, r: 60 },
  };

  // Bank Reserves Chart Data
  $: bankReservesDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.us_net_liq_reserves,
      name: "Bank Reserves (T)",
      type: "scatter",
      mode: "lines",
      line: { color: "#22c55e", width: 2, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(34, 197, 94, 0.05)",
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.us_net_liq,
      name: "Net Liquidity (T)",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 2, dash: "dot", shape: "spline" },
      yaxis: "y2",
    },
  ];
  $: bankReservesData = filterPlotlyData(
    bankReservesDataRaw,
    $dashboardData.dates,
    reservesRange,
  );
  $: bankReservesLayout = {
    yaxis: { title: "Reserves (T)", side: "left", showgrid: false },
    yaxis2: {
      title: "Net Liq (T)",
      overlaying: "y",
      side: "right",
      showgrid: false,
    },
    legend: { orientation: "h", y: 1.1 },
  };

  // Repo Stress Chart Data (SOFR vs IORB)
  $: repoStressDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.repo_stress?.sofr,
      name: "SOFR (%)",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 2, shape: "spline" },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.repo_stress?.iorb,
      name: "IORB (%)",
      type: "scatter",
      mode: "lines",
      line: { color: "#8b5cf6", width: 2, dash: "dash", shape: "spline" },
    },
  ];
  $: repoStressData = filterPlotlyData(
    repoStressDataRaw,
    $dashboardData.dates,
    repoStressRange,
  );

  // RRP (Reverse Repo) Chart Data
  $: rrpDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.us_net_liq_rrp,
      name: "Fed RRP (T)",
      type: "scatter",
      mode: "lines",
      line: { color: "#ef4444", width: 2, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(239, 68, 68, 0.05)",
    },
  ];
  $: rrpData = filterPlotlyData(rrpDataRaw, $dashboardData.dates, rrpRange);

  // TGA (Treasury General Account) Chart Data
  $: tgaDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.us_net_liq_tga,
      name: "TGA (T)",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 2, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(245, 158, 11, 0.05)",
    },
  ];
  $: tgaData = filterPlotlyData(tgaDataRaw, $dashboardData.dates, tgaRange);

  // GLI Metrics Helpers
  $: gliWeights = Object.entries($dashboardData.gli_weights || {})
    .map(([id, weight]) => {
      const rocs = $dashboardData.bank_rocs?.[id] || {};
      return {
        id,
        name: id.toUpperCase(),
        weight,
        isLiability: false,
        m1: rocs["1M"]?.[rocs["1M"].length - 1] || 0,
        m3: rocs["3M"]?.[rocs["3M"].length - 1] || 0,
        m6: rocs["6M"]?.[rocs["6M"].length - 1] || 0,
        y1: rocs["1Y"]?.[rocs["1Y"].length - 1] || 0,
        imp1: rocs["impact_1m"]?.[rocs["impact_1m"].length - 1] || 0,
        imp3: rocs["impact_3m"]?.[rocs["impact_3m"].length - 1] || 0,
        imp1y: rocs["impact_1y"]?.[rocs["impact_1y"].length - 1] || 0,
      };
    })
    .sort((a, b) => b.weight - a.weight);

  // M2 Metrics Helpers
  $: m2Weights = Object.entries($dashboardData.m2_weights || {})
    .map(([id, weight]) => {
      const rocs = $dashboardData.m2_bank_rocs?.[id] || {};
      return {
        id,
        name: id.toUpperCase(),
        weight,
        isLiability: false,
        m1: rocs["1M"]?.[rocs["1M"].length - 1] || 0,
        m3: rocs["3M"]?.[rocs["3M"].length - 1] || 0,
        m6: rocs["6M"]?.[rocs["6M"].length - 1] || 0,
        y1: rocs["1Y"]?.[rocs["1Y"].length - 1] || 0,
        imp1: rocs["impact_1m"]?.[rocs["impact_1m"].length - 1] || 0,
        imp3: rocs["impact_3m"]?.[rocs["impact_3m"].length - 1] || 0,
        imp1y: rocs["impact_1y"]?.[rocs["impact_1y"].length - 1] || 0,
      };
    })
    .sort((a, b) => b.weight - a.weight);

  // US System Metrics Helpers
  $: usSystemMetrics = $dashboardData.us_system_rocs
    ? Object.entries($dashboardData.us_system_rocs).map(([id, data]) => {
        const labels = {
          fed: "Fed Assets",
          rrp: "Fed RRP",
          tga: "Treasury TGA",
        };
        return {
          id,
          name: labels[id] || id.toUpperCase(),
          isLiability: id !== "fed",
          m1: data["1M"]?.[data["1M"].length - 1] || 0,
          m3: data["3M"]?.[data["3M"].length - 1] || 0,
          y1: data["1Y"]?.[data["1Y"].length - 1] || 0,
          imp1: data["impact_1m"]?.[data["impact_1m"].length - 1] || 0,
          imp3: data["impact_3m"]?.[data["impact_3m"].length - 1] || 0,
          imp1y: data["impact_1y"]?.[data["impact_1y"].length - 1] || 0,
          delta1: data["delta_1m"]?.[data["delta_1m"].length - 1] || 0,
          delta3: data["delta_3m"]?.[data["delta_3m"].length - 1] || 0,
          delta1y: data["delta_1y"]?.[data["delta_1y"].length - 1] || 0,
        };
      })
    : [];

  $: usSystemTotal = usSystemMetrics.reduce(
    (acc, item) => {
      return {
        delta1: acc.delta1 + item.delta1,
        imp1: acc.imp1 + item.imp1,
        delta3: acc.delta3 + item.delta3,
        imp3: acc.imp3 + item.imp3,
        delta1y: acc.delta1y + item.delta1y,
        imp1y: acc.imp1y + item.imp1y,
      };
    },
    { delta1: 0, imp1: 0, delta3: 0, imp3: 0, delta1y: 0, imp1y: 0 },
  );

  $: gliMovers = $dashboardData.bank_rocs
    ? Object.entries($dashboardData.bank_rocs)
        .map(([id, rocs]) => ({
          id,
          name: id.toUpperCase(),
          isLiability: false,
          m1: rocs["1M"]?.[rocs["1M"].length - 1] || 0,
          m3: rocs["3M"]?.[rocs["3M"].length - 1] || 0,
          m6: rocs["6M"]?.[rocs["6M"].length - 1] || 0,
          y1: rocs["1Y"]?.[rocs["1Y"].length - 1] || 0,
          impact: rocs["impact_1m"]?.[rocs["impact_1m"].length - 1] || 0,
        }))
        .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
        .slice(0, 5)
    : [];

  // --- CLI Component Breakdown (Stacked Contribution) ---
  // Weights matching backend: HY (0.25), IG (0.15), NFCI_CREDIT (0.20), NFCI_RISK (0.20), LENDING (0.10), VIX (0.10)
  $: cliComponentDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.hy_z.map((v) => v * 0.25),
      name: "HY Spread Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(239, 68, 68, 0.4)", // red
      line: { color: "#ef4444", width: 1 },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.ig_z.map((v) => v * 0.15),
      name: "IG Spread Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(249, 115, 22, 0.4)", // orange
      line: { color: "#f97316", width: 1 },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.nfci_credit_z.map((v) => v * 0.2),
      name: "NFCI Credit Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(234, 179, 8, 0.4)", // yellow
      line: { color: "#eab308", width: 1 },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.nfci_risk_z.map((v) => v * 0.2),
      name: "NFCI Risk Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(168, 85, 247, 0.4)", // purple
      line: { color: "#a855f7", width: 1 },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.lending_z.map((v) => v * 0.1),
      name: "Lending Standards Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(59, 130, 246, 0.4)", // blue
      line: { color: "#3b82f6", width: 1 },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.vix_z.map((v) => v * 0.1),
      name: "VIX Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(107, 114, 128, 0.4)", // gray
      line: { color: "#6b7280", width: 1 },
    },
  ];
  $: cliComponentData = filterPlotlyData(
    cliComponentDataRaw,
    $dashboardData.dates,
    cliRange,
  );

  $: vixDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.vix,
      name: "VIX",
      type: "scatter",
      mode: "lines",
      line: { color: "#dc2626", width: 3, shape: "spline" },
    },
  ];
  $: vixData = filterPlotlyData(vixDataRaw, $dashboardData.dates, vixRange);

  $: spreadDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.hy_spread,
      name: "HY Spread",
      type: "scatter",
      mode: "lines",
      line: { color: "#7c3aed", width: 3, shape: "spline" },
    },
  ];
  $: spreadData = filterPlotlyData(
    spreadDataRaw,
    $dashboardData.dates,
    spreadRange,
  );

  // --- Individual CLI Components (Z-Scores) ---
  $: hyZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.hy_z,
      name: "HY Spread Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#ef4444", width: 2 },
    },
  ];
  $: hyZData = filterPlotlyData(hyZDataRaw, $dashboardData.dates, hyRange);

  $: igZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.ig_z,
      name: "IG Spread Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#f97316", width: 2 },
    },
  ];
  $: igZData = filterPlotlyData(igZDataRaw, $dashboardData.dates, igRange);

  $: nfciCreditZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.nfci_credit_z,
      name: "NFCI Credit Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#eab308", width: 2 },
    },
  ];
  $: nfciCreditZData = filterPlotlyData(
    nfciCreditZDataRaw,
    $dashboardData.dates,
    nfciRange,
  );

  $: nfciRiskZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.nfci_risk_z,
      name: "NFCI Risk Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#a855f7", width: 2 },
    },
  ];
  $: nfciRiskZData = filterPlotlyData(
    nfciRiskZDataRaw,
    $dashboardData.dates,
    nfciRange,
  );

  $: lendingZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.lending_z,
      name: "Lending Standards Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 2 },
    },
  ];
  $: lendingZData = filterPlotlyData(
    lendingZDataRaw,
    $dashboardData.dates,
    lendingRange,
  );

  $: vixZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.vix_z,
      name: "VIX Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#6b7280", width: 2 },
    },
  ];
  $: vixZData = filterPlotlyData(vixZDataRaw, $dashboardData.dates, vixRange);

  // --- M2 Money Supply Chart Data ---
  $: m2TotalDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.total,
      name: "Global M2 Total",
      type: "scatter",
      mode: "lines",
      fill: "tozeroy",
      line: { color: "#6366f1", width: 3, shape: "spline" },
      fillcolor: "rgba(99, 102, 241, 0.05)",
    },
  ];
  $: m2TotalData = filterPlotlyData(
    m2TotalDataRaw,
    $dashboardData.dates,
    m2Range,
  );

  $: usM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.us,
      name: "US M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(59, 130, 246, 0.05)",
    },
  ];
  $: usM2Data = filterPlotlyData(usM2DataRaw, $dashboardData.dates, usM2Range);

  $: euM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.eu,
      name: "EU M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#8b5cf6", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(139, 92, 246, 0.05)",
    },
  ];
  $: euM2Data = filterPlotlyData(euM2DataRaw, $dashboardData.dates, euM2Range);

  $: cnM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.cn,
      name: "China M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#10b981", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(16, 185, 129, 0.05)",
    },
  ];
  $: cnM2Data = filterPlotlyData(cnM2DataRaw, $dashboardData.dates, cnM2Range);

  $: jpM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.jp,
      name: "Japan M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#f43f5e", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(244, 63, 94, 0.05)",
    },
  ];
  $: jpM2Data = filterPlotlyData(jpM2DataRaw, $dashboardData.dates, jpM2Range);

  $: ukM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.uk,
      name: "UK M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(245, 158, 11, 0.05)",
    },
  ];
  $: ukM2Data = filterPlotlyData(ukM2DataRaw, $dashboardData.dates, ukM2Range);

  $: caM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.ca,
      name: "Canada M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#ef4444", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(239, 68, 68, 0.05)",
    },
  ];
  $: caM2Data = filterPlotlyData(caM2DataRaw, $dashboardData.dates, caM2Range);

  $: auM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.au,
      name: "Australia M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(59, 130, 246, 0.05)",
    },
  ];
  $: auM2Data = filterPlotlyData(auM2DataRaw, $dashboardData.dates, auM2Range);

  $: inM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.in,
      name: "India M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#6366f1", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(99, 102, 241, 0.05)",
    },
  ];
  $: inM2Data = filterPlotlyData(inM2DataRaw, $dashboardData.dates, inM2Range);

  $: chM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.ch,
      name: "Switzerland M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#0ea5e9", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(14, 165, 233, 0.05)",
    },
  ];
  $: chM2Data = filterPlotlyData(chM2DataRaw, $dashboardData.dates, chM2Range);

  $: ruM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.ru,
      name: "Russia M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#dc2626", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(220, 38, 38, 0.05)",
    },
  ];
  $: ruM2Data = filterPlotlyData(ruM2DataRaw, $dashboardData.dates, ruM2Range);

  $: brM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.br,
      name: "Brazil M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#10b981", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(16, 185, 129, 0.05)",
    },
  ];
  $: brM2Data = filterPlotlyData(brM2DataRaw, $dashboardData.dates, brM2Range);

  $: krM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.kr,
      name: "South Korea M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#8b5cf6", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(139, 92, 246, 0.05)",
    },
  ];
  $: krM2Data = filterPlotlyData(krM2DataRaw, $dashboardData.dates, krM2Range);

  $: mxM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.mx,
      name: "Mexico M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(245, 158, 11, 0.05)",
    },
  ];
  $: mxM2Data = filterPlotlyData(mxM2DataRaw, $dashboardData.dates, mxM2Range);

  $: myM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.my,
      name: "Malaysia M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#f43f5e", width: 3, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(244, 63, 94, 0.05)",
    },
  ];
  $: myM2Data = filterPlotlyData(myM2DataRaw, $dashboardData.dates, myM2Range);

  $: gliSignal = $latestStats?.gli?.change > 0 ? "bullish" : "bearish";
  $: liqSignal = $latestStats?.us_net_liq?.change > 0 ? "bullish" : "bearish";

  // Bitcoin data
  $: btcFairValueData = [
    {
      name: "BTC Price",
      type: "area",
      color: "#f7931a",
      topColor: "rgba(247, 147, 26, 0.1)",
      bottomColor: "rgba(247, 147, 26, 0)",
      data: formatTV($dashboardData.dates, $dashboardData.btc?.price),
      width: 3,
    },
    {
      name: "Fair Value",
      type: "line",
      color: "#10b981",
      data: formatTV($dashboardData.dates, activeBtcModel.fair_value),
      width: 2,
    },
    {
      name: "+2σ",
      type: "line",
      color: "#ef4444",
      data: formatTV($dashboardData.dates, activeBtcModel.upper_2sd),
      width: 1,
      options: { lineStyle: 2 },
    },
    {
      name: "+1σ",
      type: "line",
      color: "#f59e0b",
      data: formatTV($dashboardData.dates, activeBtcModel.upper_1sd),
      width: 1,
      options: { lineStyle: 2 },
    },
    {
      name: "-1σ",
      type: "line",
      color: "#f59e0b",
      data: formatTV($dashboardData.dates, activeBtcModel.lower_1sd),
      width: 1,
      options: { lineStyle: 2 },
    },
    {
      name: "-2σ",
      type: "line",
      color: "#ef4444",
      data: formatTV($dashboardData.dates, activeBtcModel.lower_2sd),
      width: 1,
      options: { lineStyle: 2 },
    },
  ];

  $: btcDeviationData = [
    {
      x: $dashboardData.dates,
      y: activeBtcModel.deviation_zscore || [],
      name: "Price Deviation (Z-Score)",
      type: "scatter",
      mode: "lines",
      line: { color: "#6366f1", width: 2 },
    },
  ];

  $: btcLayout = {
    xaxis: {
      range: (() => {
        const prices = $dashboardData.btc?.price || [];
        const firstIdx = prices.findIndex((p) => p !== null);
        if (firstIdx !== -1) {
          return [
            $dashboardData.dates[firstIdx],
            $dashboardData.dates[prices.length - 1],
          ];
        }
        return undefined;
      })(),
    },
  };

  $: correlationData = (() => {
    const corrs = $dashboardData.correlations || {};
    return [
      {
        x: Object.keys(corrs["gli_btc"] || {}).map(Number),
        y: Object.values(corrs["gli_btc"] || {}),
        name: "GLI vs BTC",
        type: "scatter",
        mode: "lines",
        line: { color: "#6366f1", width: 2 },
      },
      {
        x: Object.keys(corrs["cli_btc"] || {}).map(Number),
        y: Object.values(corrs["cli_btc"] || {}),
        name: "CLI vs BTC",
        type: "scatter",
        mode: "lines",
        line: { color: "#f59e0b", width: 2 },
      },
      {
        x: Object.keys(corrs["vix_btc"] || {}).map(Number),
        y: Object.values(corrs["vix_btc"] || {}),
        name: "VIX vs BTC",
        type: "scatter",
        mode: "lines",
        line: { color: "#dc2626", width: 2 },
      },
      {
        x: Object.keys(corrs["netliq_btc"] || {}).map(Number),
        y: Object.values(corrs["netliq_btc"] || {}),
        name: "Net Liq vs BTC",
        type: "scatter",
        mode: "lines",
        line: { color: "#10b981", width: 2 },
      },
    ];
  })();

  $: lagCorrelationChartData = (() => {
    const lagData =
      $dashboardData.predictive?.lag_correlations?.[selectedLagWindow];
    if (!lagData || !lagData.lags || !lagData.correlations) return [];

    const optimalLag = lagData.optimal_lag || 0;
    const colors = lagData.lags.map((lag) =>
      lag === optimalLag ? "#10b981" : "#6366f1",
    );

    return [
      {
        x: lagData.lags,
        y: lagData.correlations.map((c) => (c !== null ? c * 100 : null)), // Convert to percentage
        name: `${selectedLagWindow.toUpperCase()} ROC Lag Correlation`,
        type: "bar",
        marker: { color: colors },
      },
    ];
  })();

  $: quantV2ChartData = (() => {
    const v2 = $dashboardData.btc?.models?.quant_v2;
    if (!v2 || !v2.dates || v2.dates.length === 0) return [];

    return [
      {
        name: "BTC Price",
        type: "area",
        color: "#f7931a",
        topColor: "rgba(247, 147, 26, 0.1)",
        bottomColor: "rgba(247, 147, 26, 0)",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.btc_price[i],
          }))
          .filter((p) => p.value !== null),
        width: 3,
      },
      {
        name: "Fair Value",
        type: "line",
        color: "#10b981",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.fair_value[i],
          }))
          .filter((p) => p.value !== null),
        width: 2,
      },
      {
        name: "+2σ",
        type: "line",
        color: "#ef4444",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.upper_2sd[i],
          }))
          .filter((p) => p.value !== null),
        width: 1,
        options: { lineStyle: 2 },
      },
      {
        name: "+1σ",
        type: "line",
        color: "#f59e0b",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.upper_1sd[i],
          }))
          .filter((p) => p.value !== null),
        width: 1,
        options: { lineStyle: 2 },
      },
      {
        name: "-1σ",
        type: "line",
        color: "#f59e0b",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.lower_1sd[i],
          }))
          .filter((p) => p.value !== null),
        width: 1,
        options: { lineStyle: 2 },
      },
      {
        name: "-2σ",
        type: "line",
        color: "#ef4444",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.lower_2sd[i],
          }))
          .filter((p) => p.value !== null),
        width: 1,
        options: { lineStyle: 2 },
      },
    ];
  })();

  // Returns comparison chart data (Plotly bar chart)
  $: quantV2ReturnsData = (() => {
    const v2 = $dashboardData.btc?.models?.quant_v2;
    if (!v2 || !v2.returns || !v2.returns.dates) return [];

    return [
      {
        x: v2.returns.dates,
        y: v2.returns.actual,
        name: "Actual Returns (%)",
        type: "bar",
        marker: { color: "#f7931a", opacity: 0.7 },
      },
      {
        x: v2.returns.dates,
        y: v2.returns.predicted,
        name: "Predicted Returns (%)",
        type: "scatter",
        mode: "lines",
        line: { color: "#10b981", width: 2 },
      },
    ];
  })();

  // Rebalanced Fair Value chart data (LightweightChart)
  $: quantV2RebalancedData = (() => {
    const v2 = $dashboardData.btc?.models?.quant_v2;
    if (!v2 || !v2.dates || v2.dates.length === 0 || !v2.rebalanced_fv)
      return [];

    return [
      {
        name: "BTC Price",
        type: "area",
        color: "#f7931a",
        topColor: "rgba(247, 147, 26, 0.1)",
        bottomColor: "rgba(247, 147, 26, 0)",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.btc_price[i],
          }))
          .filter((p) => p.value !== null),
        width: 3,
      },
      {
        name: "Rebalanced FV",
        type: "line",
        color: "#8b5cf6",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.rebalanced_fv[i],
          }))
          .filter((p) => p.value !== null),
        width: 2,
      },
    ];
  })();

  const getLastDate = (seriesKey) => {
    if (!$dashboardData.last_dates) return "N/A";
    const key = seriesKey.toUpperCase();
    return (
      $dashboardData.last_dates[key] ||
      $dashboardData.last_dates[key + "_USD"] ||
      $dashboardData.last_dates[seriesKey] ||
      "N/A"
    );
  };

  const getLatestROC = (rocsObj, window) => {
    if (!rocsObj || !rocsObj[window] || !Array.isArray(rocsObj[window]))
      return 0;
    const series = rocsObj[window];
    return series.length > 0 ? series[series.length - 1] : 0;
  };

  const getLatestValue = (series) => {
    if (!series || !Array.isArray(series) || series.length === 0) return null;
    for (let i = series.length - 1; i >= 0; i--) {
      if (series[i] !== null && series[i] !== undefined) return series[i];
    }
    return null;
  };
</script>

<div class="app-container">
  <aside class="sidebar">
    <svg style="position: absolute; width: 0; height: 0;" aria-hidden="true">
      <filter id="remove-white">
        <feColorMatrix
          type="matrix"
          values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 -3 -3 -3 1 8.5"
        />
      </filter>
    </svg>

    <div class="brand">
      <div
        class="logo-box"
        style="background: transparent; padding: 0; overflow: visible;"
      >
        <img
          src="logo-isometric.jpg"
          alt="Quant Terminal"
          style="width: 100%; height: 100%; object-fit: contain; filter: url(#remove-white);"
        />
      </div>
      <div class="brand-text">
        <h2>Quant Terminal</h2>
        <span>Liquidity Engine</span>
      </div>
    </div>

    <nav>
      <div
        class="nav-item"
        class:active={currentTab === "Dashboard"}
        on:click={() => setTab("Dashboard")}
        on:keydown={(e) => e.key === "Enter" && setTab("Dashboard")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">📊</span>
        {currentTranslations.nav_dashboard}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "Global Flows CB"}
        on:click={() => setTab("Global Flows CB")}
        on:keydown={(e) => e.key === "Enter" && setTab("Global Flows CB")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">🏦</span>
        {currentTranslations.nav_gli}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "Global M2"}
        on:click={() => setTab("Global M2")}
        on:keydown={(e) => e.key === "Enter" && setTab("Global M2")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">💰</span>
        {currentTranslations.nav_m2}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "US System"}
        on:click={() => setTab("US System")}
        on:keydown={(e) => e.key === "Enter" && setTab("US System")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">🇺🇸</span>
        {currentTranslations.nav_us_system}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "Risk Model"}
        on:click={() => setTab("Risk Model")}
        on:keydown={(e) => e.key === "Enter" && setTab("Risk Model")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">⚠️</span>
        {currentTranslations.nav_risk_model}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "BTC Analysis"}
        on:click={() => setTab("BTC Analysis")}
        on:keydown={(e) => e.key === "Enter" && setTab("BTC Analysis")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">₿</span>
        {currentTranslations.nav_btc_analysis}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "BTC Quant v2"}
        on:click={() => setTab("BTC Quant v2")}
        on:keydown={(e) => e.key === "Enter" && setTab("BTC Quant v2")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">🧪</span>
        {currentTranslations.nav_btc_quant}
      </div>
    </nav>

    <div class="sidebar-footer"></div>
  </aside>

  <main class="content">
    <header>
      <div class="content-header">
        <h1>
          {currentTab}
          {currentTranslations.nav_dashboard === "Dashboard"
            ? "Overview"
            : "Resumen"}
        </h1>
        <p>
          {currentTranslations.header_desc}
        </p>
      </div>
      <div class="header-actions">
        <div class="status-indicator">
          <div class="pulse"></div>
          {currentTranslations.system_live}
        </div>
        <button
          class="header-toggle"
          on:click={toggleLanguage}
          title={currentTranslations.switch_lang}
        >
          <span class="toggle-icon">🌐</span>
          <span class="toggle-label">{language === "en" ? "EN" : "ES"}</span>
        </button>
        <button
          class="header-toggle"
          on:click={toggleDarkMode}
          title={darkMode
            ? currentTranslations.light_mode
            : currentTranslations.dark_mode}
        >
          <span class="toggle-icon">{darkMode ? "☀️" : "🌙"}</span>
          <span class="toggle-label"
            >{darkMode
              ? currentTranslations.light_mode.split(" ")[0]
              : currentTranslations.dark_mode.split(" ")[0]}</span
          >
        </button>
        {#if $isLoading}
          <div class="loader"></div>
        {:else}
          <button class="refresh-btn" on:click={fetchData}
            >{currentTranslations.refresh_data}</button
          >
        {/if}
      </div>
    </header>

    {#if $error}
      <div class="error-banner">
        <strong>Connection Error:</strong>
        {$error}
      </div>
    {/if}

    <div class="dashboard-grid">
      {#if currentTab === "Dashboard"}
        {#if $latestStats}
          <div class="stats-grid">
            <StatsCard
              title={currentTranslations.stat_gli}
              value={$latestStats.gli.value}
              change={$latestStats.gli.change}
              suffix="T"
              icon="🌍"
            />
            <StatsCard
              title={currentTranslations.stat_us_net}
              value={$latestStats.us_net_liq.value}
              change={$latestStats.us_net_liq.change}
              suffix="T"
              icon="🇺🇸"
            />
            <StatsCard
              title={currentTranslations.stat_cli}
              value={$latestStats.cli.value}
              change={$latestStats.cli.change}
              suffix="Z"
              icon="💳"
              precision={3}
            />
            <StatsCard
              title={currentTranslations.stat_vix}
              value={$latestStats.vix.value}
              change={$latestStats.vix.change}
              icon="🌪️"
            />
          </div>
        {/if}

        <div class="main-charts">
          <div class="chart-card wide">
            <div class="gli-layout">
              <div class="chart-main">
                <div class="chart-header">
                  <div class="label-group">
                    <h3>
                      {currentTranslations.stat_gli} ({$dashboardData.gli
                        .cb_count || 15}
                      {currentTranslations.nav_dashboard === "Dashboard"
                        ? "Banks"
                        : "Bancos"})
                    </h3>
                    <SignalBadge type={gliSignal} text={gliSignal} />
                  </div>
                  <div class="header-controls">
                    <div class="fx-toggle">
                      <button
                        class="fx-btn"
                        class:active={!gliShowConstantFx}
                        on:click={() => (gliShowConstantFx = false)}
                        >{currentTranslations.spot_usd}</button
                      >
                      <button
                        class="fx-btn"
                        class:active={gliShowConstantFx}
                        on:click={() => (gliShowConstantFx = true)}
                        >{currentTranslations.const_fx}</button
                      >
                    </div>
                    <TimeRangeSelector
                      selectedRange={gliRange}
                      onRangeChange={(r) => (gliRange = r)}
                    />
                    <span class="last-date"
                      >{currentTranslations.last}
                      {getLastDate("GLI_TOTAL")}</span
                    >
                  </div>
                </div>
                <p class="chart-description">{currentTranslations.gli}</p>
                <div class="chart-content">
                  <Chart {darkMode} data={gliData} />
                </div>
              </div>

              <div class="metrics-sidebar">
                <!-- Data Health Panel -->
                <div class="metrics-section data-health-section">
                  <h4 style="display: flex; align-items: center; gap: 8px;">
                    <span class="health-dot"></span>
                    {currentTranslations.data_health}
                  </h4>
                  <table class="metrics-table health-table">
                    <thead>
                      <tr>
                        <th>{currentTranslations.series}</th>
                        <th>{currentTranslations.real_date}</th>
                        <th>{currentTranslations.freshness}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each Object.entries($dashboardData.series_metadata || {}) as [id, meta]}
                        <tr>
                          <td><strong>{id}</strong></td>
                          <td>{meta.last_date || "N/A"}</td>
                          <td>
                            <span
                              class="freshness-tag"
                              class:stale={meta.freshness > 7}
                            >
                              {meta.freshness === 0
                                ? "Today"
                                : (meta.freshness || "?") + "d"}
                            </span>
                          </td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                  {#if $dashboardData.series_metadata?.GLI?.cb_count}
                    <div class="coverage-note">
                      {currentTranslations.active_cbs}:
                      <strong
                        >{$dashboardData.series_metadata.GLI
                          .cb_count}/15</strong
                      >
                    </div>
                  {/if}
                </div>

                <div class="metrics-section">
                  <h4>{currentTranslations.chart_gli_comp}</h4>
                  <table class="metrics-table">
                    <thead>
                      <tr>
                        <th>{currentTranslations.bank}</th>
                        <th>{currentTranslations.weight}</th>
                        <th>1M</th>
                        <th title={currentTranslations.impact_1m}>Imp</th>
                        <th>3M</th>
                        <th title={currentTranslations.impact_3m}>Imp</th>
                        <th>1Y</th>
                        <th title={currentTranslations.impact_1y}>Imp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each gliWeights.slice(0, 10) as bank}
                        <tr>
                          <td>{bank.name}</td>
                          <td>{bank.weight.toFixed(0)}%</td>
                          <td
                            class="roc-val"
                            class:positive={bank.m1 > 0}
                            class:negative={bank.m1 < 0}
                            >{bank.m1.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val impact-cell"
                            class:positive={bank.imp1 > 0}
                            class:negative={bank.imp1 < 0}
                            >{bank.imp1.toFixed(2)}%</td
                          >
                          <td
                            class="roc-val"
                            class:positive={bank.m3 > 0}
                            class:negative={bank.m3 < 0}
                            >{bank.m3.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val impact-cell"
                            class:positive={bank.imp3 > 0}
                            class:negative={bank.imp3 < 0}
                            >{bank.imp3.toFixed(2)}%</td
                          >
                          <td
                            class="roc-val"
                            class:positive={bank.y1 > 0}
                            class:negative={bank.y1 < 0}
                            >{bank.y1.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val impact-cell"
                            class:positive={bank.imp1y > 0}
                            class:negative={bank.imp1y < 0}
                            >{bank.imp1y.toFixed(2)}%</td
                          >
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                  <p style="font-size: 10px; color: #94a3b8; margin-top: 8px;">
                    {currentTranslations.impact_note_gli}
                  </p>
                </div>

                <div class="metrics-section" style="margin-top: 24px;">
                  <h4>⚡ {currentTranslations.flow_impulse}</h4>
                  <p
                    class="section-note"
                    style="font-size: 11px; margin-bottom: 12px; color: var(--text-muted);"
                  >
                    {currentTranslations.flow_desc}
                  </p>
                  <table class="metrics-table">
                    <thead>
                      <tr>
                        <th>{currentTranslations.economy}</th>
                        <th>Impulse (13W)</th>
                        <th>Accel</th>
                        <th>Z-Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each [{ name: "Global Liquidity", key: "gli" }, { name: "Global M2", key: "m2" }] as aggregate}
                        <tr>
                          <td><strong>{aggregate.name}</strong></td>
                          <td
                            class="roc-val"
                            class:positive={getLatestValue(
                              $dashboardData.flow_metrics?.[
                                `${aggregate.key}_impulse_13w`
                              ],
                            ) > 0}
                            class:negative={getLatestValue(
                              $dashboardData.flow_metrics?.[
                                `${aggregate.key}_impulse_13w`
                              ],
                            ) < 0}
                          >
                            {getLatestValue(
                              $dashboardData.flow_metrics?.[
                                `${aggregate.key}_impulse_13w`
                              ],
                            )?.toFixed(2)}T
                          </td>
                          <td
                            class="roc-val"
                            class:positive={getLatestValue(
                              $dashboardData.flow_metrics?.[
                                `${aggregate.key}_accel`
                              ],
                            ) > 0}
                            class:negative={getLatestValue(
                              $dashboardData.flow_metrics?.[
                                `${aggregate.key}_accel`
                              ],
                            ) < 0}
                          >
                            {getLatestValue(
                              $dashboardData.flow_metrics?.[
                                `${aggregate.key}_accel`
                              ],
                            )?.toFixed(2)}T
                          </td>
                          <td
                            class="signal-cell"
                            class:plus={getLatestValue(
                              $dashboardData.flow_metrics?.[
                                `${aggregate.key}_impulse_zscore`
                              ],
                            ) > 1}
                            class:minus={getLatestValue(
                              $dashboardData.flow_metrics?.[
                                `${aggregate.key}_impulse_zscore`
                              ],
                            ) < -1}
                          >
                            {getLatestValue(
                              $dashboardData.flow_metrics?.[
                                `${aggregate.key}_impulse_zscore`
                              ],
                            )?.toFixed(2)}σ
                          </td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>

                <div class="metrics-section" style="margin-top: 24px;">
                  <h4>🏦 {currentTranslations.cb_contribution}</h4>
                  <table class="metrics-table">
                    <thead>
                      <tr>
                        <th>CB</th>
                        <th>Contrib Δ13W</th>
                        <th>Signal</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each [{ name: "Fed", key: "fed" }, { name: "ECB", key: "ecb" }, { name: "BoJ", key: "boj" }, { name: "PBoC", key: "pboc" }, { name: "BoE", key: "boe" }] as cb}
                        {#if getLatestValue($dashboardData.flow_metrics?.[`${cb.key}_contrib_13w`]) !== undefined}
                          <tr>
                            <td>{cb.name}</td>
                            <td
                              class="roc-val"
                              class:positive={getLatestValue(
                                $dashboardData.flow_metrics?.[
                                  `${cb.key}_contrib_13w`
                                ],
                              ) > 0}
                              class:negative={getLatestValue(
                                $dashboardData.flow_metrics?.[
                                  `${cb.key}_contrib_13w`
                                ],
                              ) < 0}
                            >
                              {getLatestValue(
                                $dashboardData.flow_metrics?.[
                                  `${cb.key}_contrib_13w`
                                ],
                              )?.toFixed(1)}%
                            </td>
                            <td
                              class="signal-cell"
                              class:plus={getLatestValue(
                                $dashboardData.flow_metrics?.[
                                  `${cb.key}_contrib_13w`
                                ],
                              ) > 20}
                              class:minus={getLatestValue(
                                $dashboardData.flow_metrics?.[
                                  `${cb.key}_contrib_13w`
                                ],
                              ) < -5}
                            >
                              {getLatestValue(
                                $dashboardData.flow_metrics?.[
                                  `${cb.key}_contrib_13w`
                                ],
                              ) > 20
                                ? "Driver"
                                : getLatestValue(
                                      $dashboardData.flow_metrics?.[
                                        `${cb.key}_contrib_13w`
                                      ],
                                    ) < -5
                                  ? "QT"
                                  : "—"}
                            </td>
                          </tr>
                        {/if}
                      {/each}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <div class="chart-card wide">
            <div class="gli-layout">
              <div class="chart-main">
                <div class="chart-header">
                  <div class="label-group">
                    <h3>{currentTranslations.chart_us_net_liq}</h3>
                    <SignalBadge type={liqSignal} text={liqSignal} />
                  </div>
                  <div class="header-controls">
                    <TimeRangeSelector
                      selectedRange={netLiqRange}
                      onRangeChange={(r) => (netLiqRange = r)}
                    />
                    <span class="last-date"
                      >{currentTranslations.last_data}
                      {getLastDate("FED")}</span
                    >
                  </div>
                </div>
                <p class="chart-description">{currentTranslations.net_liq}</p>
                <div class="chart-content">
                  <Chart {darkMode} data={netLiqData} />
                </div>
              </div>

              <div class="metrics-sidebar">
                <div class="metrics-section">
                  <h4>{currentTranslations.chart_us_comp}</h4>
                  <table class="metrics-table">
                    <thead>
                      <tr>
                        <th>{currentTranslations.account}</th>
                        <th>1M</th>
                        <th title="Absolute change in Billions USD">$ Δ1M</th>
                        <th title={currentTranslations.impact_us}>Imp</th>
                        <th>3M</th>
                        <th title={currentTranslations.impact_us}>Imp</th>
                        <th>1Y</th>
                        <th title={currentTranslations.impact_us}>Imp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each usSystemMetrics as item}
                        <tr>
                          <td>{item.name}</td>
                          <td
                            class="roc-val"
                            class:positive={(!item.isLiability &&
                              item.m1 > 0) ||
                              (item.isLiability && item.m1 < 0)}
                            class:negative={(!item.isLiability &&
                              item.m1 < 0) ||
                              (item.isLiability && item.m1 > 0)}
                            >{item.m1.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val"
                            class:positive={(!item.isLiability &&
                              item.delta1 > 0) ||
                              (item.isLiability && item.delta1 < 0)}
                            class:negative={(!item.isLiability &&
                              item.delta1 < 0) ||
                              (item.isLiability && item.delta1 > 0)}
                          >
                            {item.delta1 > 0 ? "+" : ""}{item.delta1.toFixed(
                              0,
                            )}B
                          </td>
                          <td
                            class="roc-val impact-cell"
                            class:positive={item.imp1 > 0}
                            class:negative={item.imp1 < 0}
                            >{item.imp1.toFixed(2)}%</td
                          >
                          <td
                            class="roc-val"
                            class:positive={(!item.isLiability &&
                              item.m3 > 0) ||
                              (item.isLiability && item.m3 < 0)}
                            class:negative={(!item.isLiability &&
                              item.m3 < 0) ||
                              (item.isLiability && item.m3 > 0)}
                            >{item.m3.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val impact-cell"
                            class:positive={item.imp3 > 0}
                            class:negative={item.imp3 < 0}
                            >{item.imp3.toFixed(2)}%</td
                          >
                          <td
                            class="roc-val"
                            class:positive={(!item.isLiability &&
                              item.y1 > 0) ||
                              (item.isLiability && item.y1 < 0)}
                            class:negative={(!item.isLiability &&
                              item.y1 < 0) ||
                              (item.isLiability && item.y1 > 0)}
                            >{item.y1.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val impact-cell"
                            class:positive={item.imp1y > 0}
                            class:negative={item.imp1y < 0}
                            >{item.imp1y.toFixed(2)}%</td
                          >
                        </tr>
                      {/each}
                      <tr class="total-row">
                        <td><strong>TOTAL</strong></td>
                        <td>-</td>
                        <td
                          class="roc-val"
                          class:positive={usSystemTotal.delta1 > 0}
                          class:negative={usSystemTotal.delta1 < 0}
                        >
                          {usSystemTotal.delta1 > 0
                            ? "+"
                            : ""}{usSystemTotal.delta1.toFixed(0)}B
                        </td>
                        <td
                          class="roc-val impact-cell"
                          class:positive={usSystemTotal.imp1 > 0}
                          class:negative={usSystemTotal.imp1 < 0}
                        >
                          {usSystemTotal.imp1.toFixed(2)}%
                        </td>
                        <td>-</td>
                        <td
                          class="roc-val impact-cell"
                          class:positive={usSystemTotal.imp3 > 0}
                          class:negative={usSystemTotal.imp3 < 0}
                        >
                          {usSystemTotal.imp3.toFixed(2)}%
                        </td>
                        <td>-</td>
                        <td
                          class="roc-val impact-cell"
                          class:positive={usSystemTotal.imp1y > 0}
                          class:negative={usSystemTotal.imp1y < 0}
                        >
                          {usSystemTotal.imp1y.toFixed(2)}%
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <div class="chart-card wide">
            <div class="chart-header">
              <div class="label-group">
                <h3>Credit Liquidity Index (CLI)</h3>
              </div>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={cliRange}
                  onRangeChange={(r) => (cliRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("NFCI")}</span>
              </div>
            </div>
            <p class="chart-description">{currentTranslations.cli}</p>
            <div class="chart-content">
              <Chart {darkMode} data={cliData} />
            </div>
          </div>

          <div class="chart-card wide">
            <div class="chart-header">
              <div class="label-group">
                <h3>CLI Component Contributions</h3>
              </div>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={cliRange}
                  onRangeChange={(r) => (cliRange = r)}
                />
              </div>
            </div>
            <div class="chart-content">
              <Chart {darkMode} data={cliComponentData} />
            </div>
          </div>

          <div class="regime-card wide">
            <div class="regime-header">
              <span class="regime-title"
                >{currentTranslations.regime_signal}</span
              >
              <div class="regime-badge bg-{currentRegime.color}">
                <span>{currentRegime.emoji}</span>
                <span>{currentRegime.name}</span>
              </div>

              <div
                class="control-group"
                style="display: flex; align-items: center; gap: 8px; margin-left: auto; margin-right: 16px;"
              >
                <span
                  style="font-size: 11px; color: var(--text-muted); opacity: 0.7;"
                  >Offset (Days):</span
                >
                <input
                  type="range"
                  min="0"
                  max="120"
                  step="1"
                  bind:value={regimeLag}
                  style="width: 80px;"
                  title="{regimeLag} days"
                />
                <span
                  style="font-size: 11px; min-width: 25px; text-align: right; color: var(--text-primary); font-family: monospace;"
                  >{regimeLag}</span
                >
              </div>

              <div class="liquidity-score">
                <span class="score-label">Score:</span>
                <span
                  class="score-val"
                  class:high={liquidityScore >= 70}
                  class:low={liquidityScore <= 30}
                  >{liquidityScore.toFixed(0)}</span
                >
              </div>
            </div>
            <div class="regime-body">
              <p class="regime-description">{currentRegime.desc}</p>
              <p class="regime-details">{currentRegime.details}</p>
            </div>

            <div
              class="regime-chart-container"
              style="margin-top: 16px; border-top: 1px solid var(--border-color); padding-top:10px; height: 450px; display: flex; flex-direction: column;"
            >
              <p
                style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px; line-height: 1.4;"
              >
                {currentTranslations.regime_chart_desc}
              </p>
              <div style="flex: 1; min-height: 0;">
                <LightweightChart
                  {darkMode}
                  data={regimeLCData}
                  logScale={true}
                />
              </div>
            </div>

            <div class="regime-glow glow-{currentRegime.color}"></div>
          </div>

          <div class="chart-card wide">
            <div class="chart-header">
              <div class="label-group">
                <h3>{currentTranslations.impulse_analysis}</h3>
              </div>
              <div class="header-controls">
                <div
                  class="control-group"
                  style="display: flex; align-items: center; gap: 8px;"
                >
                  <span style="font-size: 11px; color: var(--text-muted);"
                    >{currentTranslations.period}:</span
                  >
                  <select
                    bind:value={btcRocPeriod}
                    style="background: var(--bg-tertiary); border: 1px solid var(--border-color); color: var(--text-primary); padding: 4px; border-radius: 4px; font-size: 11px;"
                  >
                    <option value={21}>1M</option>
                    <option value={63}>3M</option>
                    <option value={126}>6M</option>
                    <option value={252}>1Y</option>
                  </select>
                </div>

                <div
                  class="control-group"
                  style="display: flex; align-items: center; gap: 8px;"
                >
                  <span style="font-size: 11px; color: var(--text-muted);"
                    >{currentTranslations.lag_days}:</span
                  >
                  <input
                    type="range"
                    min="-60"
                    max="60"
                    step="1"
                    bind:value={btcLag}
                    style="width: 80px;"
                    title="{btcLag} days"
                  />
                  <span
                    style="font-size: 11px; width: 25px; text-align: right; color: var(--text-primary);"
                    >{btcLag}</span
                  >
                </div>

                <div
                  class="control-group"
                  style="display: flex; align-items: center; gap: 4px;"
                >
                  <label
                    style="font-size: 11px; color: var(--text-primary); display: flex; align-items: center; gap: 4px; cursor: pointer;"
                  >
                    <input type="checkbox" bind:checked={showComposite} />
                    Composite
                  </label>
                </div>

                {#if showComposite}
                  <span
                    style="font-size: 11px; color: #8b5cf6; font-weight: 500; border: 1px solid #8b5cf6; padding: 2px 6px; border-radius: 4px;"
                  >
                    {optimalLagLabel}
                  </span>
                {/if}

                <TimeRangeSelector
                  selectedRange={impulseRange}
                  onRangeChange={(r) => (impulseRange = r)}
                />
              </div>
            </div>
            <p class="chart-description">
              {currentTranslations.chart_impulse_desc}
            </p>
            <div class="chart-content">
              <Chart {darkMode} data={impulseData} layout={impulseLayout} />
            </div>
          </div>
        </div>
      {:else if currentTab === "Global Flows CB"}
        <div class="dashboard-grid no-margin">
          {#each [{ name: "Federal Reserve (Fed)", data: fedData, range: fedRange, setRange: (r) => (fedRange = r), bank: "FED" }, { name: "European Central Bank (ECB)", data: ecbData, range: ecbRange, setRange: (r) => (ecbRange = r), bank: "ECB" }, { name: "Bank of Japan (BoJ)", data: bojData, range: bojRange, setRange: (r) => (bojRange = r), bank: "BOJ" }, { name: "Bank of England (BoE)", data: boeData, range: boeRange, setRange: (r) => (boeRange = r), bank: "BOE" }, { name: "People's Bank of China (PBoC)", data: pbocData, range: pbocRange, setRange: (r) => (pbocRange = r), bank: "PBOC" }, { name: "Bank of Canada (BoC)", data: bocData, range: bocRange, setRange: (r) => (bocRange = r), bank: "BOC" }, { name: "Reserve Bank of Australia (RBA)", data: rbaData, range: rbaRange, setRange: (r) => (rbaRange = r), bank: "RBA" }, { name: "Swiss National Bank (SNB)", data: snbData, range: snbRange, setRange: (r) => (snbRange = r), bank: "SNB" }, { name: "Bank of Korea (BoK)", data: bokData, range: bokRange, setRange: (r) => (bokRange = r), bank: "BOK" }, { name: "Reserve Bank of India (RBI)", data: rbiData, range: rbiRange, setRange: (r) => (rbiRange = r), bank: "RBI" }, { name: "Central Bank of Russia (CBR)", data: cbrData, range: cbrRange, setRange: (r) => (cbrRange = r), bank: "CBR" }, { name: "Central Bank of Brazil (BCB)", data: bcbData, range: bcbRange, setRange: (r) => (bcbRange = r), bank: "BCB" }, { name: "Reserve Bank of New Zealand (RBNZ)", data: rbnzData, range: rbnzRange, setRange: (r) => (rbnzRange = r), bank: "RBNZ" }, { name: "Sveriges Riksbank (SR)", data: srData, range: srRange, setRange: (r) => (srRange = r), bank: "SR" }, { name: "Bank Negara Malaysia (BNM)", data: bnmData, range: bnmRange, setRange: (r) => (bnmRange = r), bank: "BNM" }] as item}
            <div class="chart-card">
              <div class="chart-header">
                <h3>{item.name}</h3>
                <div class="header-controls">
                  <TimeRangeSelector
                    selectedRange={item.range}
                    onRangeChange={item.setRange}
                  />
                  <span class="last-date"
                    >{currentTranslations.last_data}
                    {getLastDate(item.bank)}</span
                  >
                </div>
              </div>
              <p class="chart-description">{currentTranslations.gli_cb}</p>
              <div class="chart-content">
                <Chart {darkMode} data={item.data} />
              </div>
            </div>
          {/each}
        </div>
      {:else if currentTab === "Global M2"}
        <div class="main-charts">
          <div class="chart-card wide">
            <div class="gli-layout">
              <div class="chart-main">
                <div class="chart-header">
                  <h3>{currentTranslations.chart_m2_aggregate}</h3>
                  <div class="header-controls">
                    <TimeRangeSelector
                      selectedRange={m2Range}
                      onRangeChange={(r) => (m2Range = r)}
                    />
                    <span class="last-date"
                      >{currentTranslations.last}: {getLastDate(
                        "M2_TOTAL",
                      )}</span
                    >
                  </div>
                </div>
                <p class="chart-description">{currentTranslations.m2_global}</p>
                <div class="chart-content">
                  <Chart {darkMode} data={m2TotalData} />
                </div>
              </div>

              <div class="metrics-sidebar">
                <div class="metrics-section">
                  <h4>{currentTranslations.chart_m2_comp}</h4>
                  <table class="metrics-table">
                    <thead>
                      <tr>
                        <th>{currentTranslations.economy}</th>
                        <th>{currentTranslations.weight}</th>
                        <th>1M</th>
                        <th title={currentTranslations.impact_1m}>Imp</th>
                        <th>3M</th>
                        <th title={currentTranslations.impact_3m}>Imp</th>
                        <th>1Y</th>
                        <th title={currentTranslations.impact_1y}>Imp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each m2Weights.slice(0, 10) as item}
                        <tr>
                          <td>{item.name}</td>
                          <td>{item.weight.toFixed(0)}%</td>
                          <td
                            class="roc-val"
                            class:positive={(!item.isLiability &&
                              item.m1 > 0) ||
                              (item.isLiability && item.m1 < 0)}
                            class:negative={(!item.isLiability &&
                              item.m1 < 0) ||
                              (item.isLiability && item.m1 > 0)}
                            >{item.m1.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val impact-cell"
                            class:positive={item.imp1 > 0}
                            class:negative={item.imp1 < 0}
                            >{item.imp1.toFixed(2)}%</td
                          >
                          <td
                            class="roc-val"
                            class:positive={(!item.isLiability &&
                              item.m3 > 0) ||
                              (item.isLiability && item.m3 < 0)}
                            class:negative={(!item.isLiability &&
                              item.m3 < 0) ||
                              (item.isLiability && item.m3 > 0)}
                            >{item.m3.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val impact-cell"
                            class:positive={item.imp3 > 0}
                            class:negative={item.imp3 < 0}
                            >{item.imp3.toFixed(2)}%</td
                          >
                          <td
                            class="roc-val"
                            class:positive={(!item.isLiability &&
                              item.y1 > 0) ||
                              (item.isLiability && item.y1 < 0)}
                            class:negative={(!item.isLiability &&
                              item.y1 < 0) ||
                              (item.isLiability && item.y1 > 0)}
                            >{item.y1.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val impact-cell"
                            class:positive={item.imp1y > 0}
                            class:negative={item.imp1y < 0}
                            >{item.imp1y.toFixed(2)}%</td
                          >
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                  <p style="font-size: 10px; color: #94a3b8; margin-top: 8px;">
                    * Impact = % contribution of local M2 1M move to total
                    Global M2.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {#each [{ id: "us", name: "US M2", data: usM2Data, range: usM2Range, setRange: (r) => (usM2Range = r), bank: "FED" }, { id: "eu", name: "EU M2", data: euM2Data, range: euM2Range, setRange: (r) => (euM2Range = r), bank: "ECB" }, { id: "cn", name: "China M2", data: cnM2Data, range: cnM2Range, setRange: (r) => (cnM2Range = r), bank: "PBOC" }, { id: "jp", name: "Japan M2", data: jpM2Data, range: jpM2Range, setRange: (r) => (jpM2Range = r), bank: "BOJ" }, { id: "uk", name: "UK M2", data: ukM2Data, range: ukM2Range, setRange: (r) => (ukM2Range = r), bank: "BOE" }, { id: "ca", name: "Canada M2", data: caM2Data, range: caM2Range, setRange: (r) => (caM2Range = r), bank: "BOC" }, { id: "au", name: "Australia M2", data: auM2Data, range: auM2Range, setRange: (r) => (auM2Range = r), bank: "RBA" }, { id: "in", name: "India M2", data: inM2Data, range: inM2Range, setRange: (r) => (inM2Range = r), bank: "RBI" }, { id: "ch", name: "Switzerland M2", data: chM2Data, range: chM2Range, setRange: (r) => (chM2Range = r), bank: "SNB" }, { id: "ru", name: "Russia M2", data: ruM2Data, range: ruM2Range, setRange: (r) => (ruM2Range = r), bank: "CBR" }, { id: "br", name: "Brazil M2", data: brM2Data, range: brM2Range, setRange: (r) => (brM2Range = r), bank: "BCB" }, { id: "kr", name: "South Korea M2", data: krM2Data, range: krM2Range, setRange: (r) => (krM2Range = r), bank: "BOK" }, { id: "mx", name: "Mexico M2", data: mxM2Data, range: mxM2Range, setRange: (r) => (mxM2Range = r), bank: "MX" }, { id: "my", name: "Malaysia M2", data: myM2Data, range: myM2Range, setRange: (r) => (myM2Range = r), bank: "BNM" }] as item}
            <div class="chart-card">
              <div class="chart-header">
                <h3>{item.name}</h3>
                <div class="header-controls">
                  <TimeRangeSelector
                    selectedRange={item.range}
                    onRangeChange={item.setRange}
                  />
                  <span class="last-date">Last: {getLastDate(item.bank)}</span>
                </div>
              </div>
              <p class="chart-description">{currentTranslations.m2_country}</p>
              <div class="chart-content">
                <Chart {darkMode} data={item.data} />
              </div>
            </div>
          {/each}
        </div>
      {:else if currentTab === "US System"}
        <div class="main-charts">
          <div class="chart-card wide">
            <div class="gli-layout">
              <div class="chart-main">
                <div class="chart-header">
                  <h3>{currentTranslations.chart_us_net_liq}</h3>
                  <div class="header-controls">
                    <TimeRangeSelector
                      selectedRange={netLiqRange}
                      onRangeChange={(r) => (netLiqRange = r)}
                    />
                    <span class="last-date"
                      >{currentTranslations.last_data}
                      {getLastDate("FED")}</span
                    >
                  </div>
                </div>
                <p class="chart-description">{currentTranslations.net_liq}</p>
                <div class="chart-content">
                  <Chart {darkMode} data={netLiqData} />
                </div>
              </div>

              <div class="metrics-sidebar">
                <div class="metrics-section">
                  <h4>{currentTranslations.chart_us_comp}</h4>
                  <table class="metrics-table">
                    <thead>
                      <tr>
                        <th>{currentTranslations.account}</th>
                        <th>1M</th>
                        <th title="Absolute change in Billions USD">$ Δ1M</th>
                        <th title={currentTranslations.impact_us}>Imp</th>
                        <th>3M</th>
                        <th title={currentTranslations.impact_us}>Imp</th>
                        <th>1Y</th>
                        <th title={currentTranslations.impact_us}>Imp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each usSystemMetrics as item}
                        <tr>
                          <td>{item.name}</td>
                          <td
                            class="roc-val"
                            class:positive={(!item.isLiability &&
                              item.m1 > 0) ||
                              (item.isLiability && item.m1 < 0)}
                            class:negative={(!item.isLiability &&
                              item.m1 < 0) ||
                              (item.isLiability && item.m1 > 0)}
                            >{item.m1.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val"
                            class:positive={(!item.isLiability &&
                              item.delta1 > 0) ||
                              (item.isLiability && item.delta1 < 0)}
                            class:negative={(!item.isLiability &&
                              item.delta1 < 0) ||
                              (item.isLiability && item.delta1 > 0)}
                          >
                            {item.delta1 > 0 ? "+" : ""}{item.delta1.toFixed(
                              0,
                            )}B
                          </td>
                          <td
                            class="roc-val impact-cell"
                            class:positive={item.imp1 > 0}
                            class:negative={item.imp1 < 0}
                            >{item.imp1.toFixed(2)}%</td
                          >
                          <td
                            class="roc-val"
                            class:positive={(!item.isLiability &&
                              item.m3 > 0) ||
                              (item.isLiability && item.m3 < 0)}
                            class:negative={(!item.isLiability &&
                              item.m3 < 0) ||
                              (item.isLiability && item.m3 > 0)}
                            >{item.m3.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val impact-cell"
                            class:positive={item.imp3 > 0}
                            class:negative={item.imp3 < 0}
                            >{item.imp3.toFixed(2)}%</td
                          >
                          <td
                            class="roc-val"
                            class:positive={(!item.isLiability &&
                              item.y1 > 0) ||
                              (item.isLiability && item.y1 < 0)}
                            class:negative={(!item.isLiability &&
                              item.y1 < 0) ||
                              (item.isLiability && item.y1 > 0)}
                            >{item.y1.toFixed(1)}%</td
                          >
                          <td
                            class="roc-val impact-cell"
                            class:positive={item.imp1y > 0}
                            class:negative={item.imp1y < 0}
                            >{item.imp1y.toFixed(2)}%</td
                          >
                        </tr>
                      {/each}
                      <tr class="total-row">
                        <td><strong>TOTAL</strong></td>
                        <td>-</td>
                        <td
                          class="roc-val"
                          class:positive={usSystemTotal.delta1 > 0}
                          class:negative={usSystemTotal.delta1 < 0}
                        >
                          {usSystemTotal.delta1 > 0
                            ? "+"
                            : ""}{usSystemTotal.delta1.toFixed(0)}B
                        </td>
                        <td
                          class="roc-val impact-cell"
                          class:positive={usSystemTotal.imp1 > 0}
                          class:negative={usSystemTotal.imp1 < 0}
                        >
                          {usSystemTotal.imp1.toFixed(2)}%
                        </td>
                        <td>-</td>
                        <td
                          class="roc-val impact-cell"
                          class:positive={usSystemTotal.imp3 > 0}
                          class:negative={usSystemTotal.imp3 < 0}
                        >
                          {usSystemTotal.imp3.toFixed(2)}%
                        </td>
                        <td>-</td>
                        <td
                          class="roc-val impact-cell"
                          class:positive={usSystemTotal.imp1y > 0}
                          class:negative={usSystemTotal.imp1y < 0}
                        >
                          {usSystemTotal.imp1y.toFixed(2)}%
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <p style="font-size: 10px; color: #94a3b8; margin-top: 8px;">
                    {currentTranslations.impact_note_us}
                  </p>
                </div>

                <!-- Composite Liquidity Metrics -->
                <div
                  class="metrics-section"
                  style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(148, 163, 184, 0.2);"
                >
                  <h4>{currentTranslations.liquidity_score}</h4>
                  <table class="metrics-table compact">
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Signal</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>{currentTranslations.liquidity_score}</td>
                        <td
                          class="roc-val"
                          class:positive={getLatestValue(
                            $dashboardData.us_system_metrics?.liquidity_score,
                          ) > 0}
                          class:negative={getLatestValue(
                            $dashboardData.us_system_metrics?.liquidity_score,
                          ) < 0}
                          >{(
                            getLatestValue(
                              $dashboardData.us_system_metrics?.liquidity_score,
                            ) ?? 0
                          ).toFixed(2)}</td
                        >
                        <td
                          class="signal-cell"
                          class:plus={getLatestValue(
                            $dashboardData.us_system_metrics?.liquidity_score,
                          ) > 1}
                          class:minus={getLatestValue(
                            $dashboardData.us_system_metrics?.liquidity_score,
                          ) < -1}
                          >{getLatestValue(
                            $dashboardData.us_system_metrics?.liquidity_score,
                          ) > 1
                            ? currentTranslations.liquid_env
                            : getLatestValue(
                                  $dashboardData.us_system_metrics
                                    ?.liquidity_score,
                                ) < -1
                              ? currentTranslations.dry_env
                              : "—"}</td
                        >
                      </tr>
                      <tr>
                        <td>{currentTranslations.netliq_roc}</td>
                        <td
                          class="roc-val"
                          class:positive={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_roc_20d,
                          ) > 0}
                          class:negative={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_roc_20d,
                          ) < 0}
                          >{(
                            getLatestValue(
                              $dashboardData.us_system_metrics?.netliq_roc_20d,
                            ) ?? 0
                          ).toFixed(2)}%</td
                        >
                        <td
                          class="signal-cell"
                          class:plus={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_roc_20d,
                          ) > 2}
                          class:minus={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_roc_20d,
                          ) < -2}
                          >{getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_roc_20d,
                          ) > 2
                            ? "Risk-ON"
                            : getLatestValue(
                                  $dashboardData.us_system_metrics
                                    ?.netliq_roc_20d,
                                ) < -2
                              ? "Risk-OFF"
                              : "—"}</td
                        >
                      </tr>
                      <tr>
                        <td>Δ4W NetLiq</td>
                        <td
                          class="roc-val"
                          class:positive={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_delta_4w,
                          ) > 0}
                          class:negative={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_delta_4w,
                          ) < 0}
                          >{(
                            (getLatestValue(
                              $dashboardData.us_system_metrics?.netliq_delta_4w,
                            ) ?? 0) * 1000
                          ).toFixed(0)}B</td
                        >
                        <td
                          class="signal-cell"
                          class:plus={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_delta_4w,
                          ) > 0.1}
                          class:minus={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_delta_4w,
                          ) < -0.1}
                          >{getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_delta_4w,
                          ) > 0.1
                            ? "Bullish"
                            : getLatestValue(
                                  $dashboardData.us_system_metrics
                                    ?.netliq_delta_4w,
                                ) < -0.1
                              ? "Bearish"
                              : "—"}</td
                        >
                      </tr>
                      <tr>
                        <td>Δ13W NetLiq</td>
                        <td
                          class="roc-val"
                          class:positive={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_delta_13w,
                          ) > 0}
                          class:negative={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_delta_13w,
                          ) < 0}
                          >{(
                            (getLatestValue(
                              $dashboardData.us_system_metrics
                                ?.netliq_delta_13w,
                            ) ?? 0) * 1000
                          ).toFixed(0)}B</td
                        >
                        <td
                          class="signal-cell"
                          class:plus={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_delta_13w,
                          ) > 0.2}
                          class:minus={getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_delta_13w,
                          ) < -0.2}
                          >{getLatestValue(
                            $dashboardData.us_system_metrics?.netliq_delta_13w,
                          ) > 0.2
                            ? "Bullish Q"
                            : getLatestValue(
                                  $dashboardData.us_system_metrics
                                    ?.netliq_delta_13w,
                                ) < -0.2
                              ? "Bearish Q"
                              : "—"}</td
                        >
                      </tr>
                      <tr>
                        <td>{currentTranslations.fed_momentum_label}</td>
                        <td
                          class="roc-val"
                          class:positive={getLatestValue(
                            $dashboardData.us_system_metrics?.fed_momentum,
                          ) > 0}
                          class:negative={getLatestValue(
                            $dashboardData.us_system_metrics?.fed_momentum,
                          ) < 0}
                          >{(
                            getLatestValue(
                              $dashboardData.us_system_metrics?.fed_momentum,
                            ) ?? 0
                          ).toFixed(3)}T</td
                        >
                        <td
                          class="signal-cell"
                          class:plus={getLatestValue(
                            $dashboardData.us_system_metrics?.fed_momentum,
                          ) > 0}
                          class:minus={getLatestValue(
                            $dashboardData.us_system_metrics?.fed_momentum,
                          ) < 0}
                          >{getLatestValue(
                            $dashboardData.us_system_metrics?.fed_momentum,
                          ) > 0
                            ? currentTranslations.regime_qe
                            : currentTranslations.regime_qt}</td
                        >
                      </tr>
                      <tr>
                        <td>{currentTranslations.tga_deviation}</td>
                        <td
                          class="roc-val"
                          class:positive={getLatestValue(
                            $dashboardData.us_system_metrics?.tga_zscore,
                          ) < 0}
                          class:negative={getLatestValue(
                            $dashboardData.us_system_metrics?.tga_zscore,
                          ) > 1}
                          >{(
                            getLatestValue(
                              $dashboardData.us_system_metrics?.tga_zscore,
                            ) ?? 0
                          ).toFixed(2)}</td
                        >
                        <td
                          class="signal-cell"
                          class:plus={getLatestValue(
                            $dashboardData.us_system_metrics?.tga_zscore,
                          ) < -1}
                          class:minus={getLatestValue(
                            $dashboardData.us_system_metrics?.tga_zscore,
                          ) > 1}
                          >{getLatestValue(
                            $dashboardData.us_system_metrics?.tga_zscore,
                          ) > 1
                            ? "Drain"
                            : getLatestValue(
                                  $dashboardData.us_system_metrics?.tga_zscore,
                                ) < -1
                              ? "Inject"
                              : "—"}</td
                        >
                      </tr>
                    </tbody>
                  </table>
                  <p style="font-size: 10px; color: #94a3b8; margin-top: 6px;">
                    * Score &gt;+1: {language === "en"
                      ? "Liquid env (bullish)"
                      : "Entorno líquido (alcista)"}<br />
                    * Score &lt;-1: {language === "en"
                      ? "Dry env (bearish)"
                      : "Entorno seco (bajista)"}
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div class="chart-card wide">
            <div class="gli-layout">
              <div class="chart-main">
                <div class="chart-header">
                  <h3>{currentTranslations.chart_bank_reserves}</h3>
                  <div class="header-controls">
                    <TimeRangeSelector
                      selectedRange={reservesRange}
                      onRangeChange={(r) => (reservesRange = r)}
                    />
                    <span class="last-date"
                      >{currentTranslations.last_data}
                      {getLastDate("RESBALNS")}</span
                    >
                  </div>
                </div>
                <p class="chart-description">
                  {currentTranslations.bank_reserves}
                </p>
                <div class="chart-content">
                  <Chart
                    {darkMode}
                    data={bankReservesData}
                    layout={bankReservesLayout}
                  />
                </div>
              </div>

              <div class="metrics-sidebar">
                <div class="metrics-section">
                  <h4>{currentTranslations.reserves_velocity}</h4>
                  <table class="metrics-table compact">
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Signal</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>{currentTranslations.roc_3m} (Res)</td>
                        <td
                          class="roc-val"
                          class:positive={getLatestValue(
                            $dashboardData.reserves_metrics?.reserves_roc_3m,
                          ) > 0}
                          class:negative={getLatestValue(
                            $dashboardData.reserves_metrics?.reserves_roc_3m,
                          ) < 0}
                          >{(
                            getLatestValue(
                              $dashboardData.reserves_metrics?.reserves_roc_3m,
                            ) ?? 0
                          ).toFixed(2)}%</td
                        >
                        <td
                          class="signal-cell"
                          class:plus={getLatestValue(
                            $dashboardData.reserves_metrics?.reserves_roc_3m,
                          ) > 0}
                          class:minus={getLatestValue(
                            $dashboardData.reserves_metrics?.reserves_roc_3m,
                          ) < 0}
                          >{getLatestValue(
                            $dashboardData.reserves_metrics?.reserves_roc_3m,
                          ) > 0
                            ? "QE"
                            : "QT"}</td
                        >
                      </tr>
                      <tr>
                        <td>{currentTranslations.roc_3m} (NL)</td>
                        <td
                          class="roc-val"
                          class:positive={getLatestValue(
                            $dashboardData.reserves_metrics?.netliq_roc_3m,
                          ) > 0}
                          class:negative={getLatestValue(
                            $dashboardData.reserves_metrics?.netliq_roc_3m,
                          ) < 0}
                          >{(
                            getLatestValue(
                              $dashboardData.reserves_metrics?.netliq_roc_3m,
                            ) ?? 0
                          ).toFixed(2)}%</td
                        >
                        <td
                          class="signal-cell"
                          class:plus={getLatestValue(
                            $dashboardData.reserves_metrics?.netliq_roc_3m,
                          ) > 0}
                          class:minus={getLatestValue(
                            $dashboardData.reserves_metrics?.netliq_roc_3m,
                          ) < 0}
                          >{getLatestValue(
                            $dashboardData.reserves_metrics?.netliq_roc_3m,
                          ) > 0
                            ? "↑"
                            : "↓"}</td
                        >
                      </tr>
                      <tr>
                        <td>{currentTranslations.spread_zscore}</td>
                        <td
                          class="roc-val"
                          class:positive={getLatestValue(
                            $dashboardData.reserves_metrics?.spread_zscore,
                          ) < -1}
                          class:negative={getLatestValue(
                            $dashboardData.reserves_metrics?.spread_zscore,
                          ) > 2}
                          >{(
                            getLatestValue(
                              $dashboardData.reserves_metrics?.spread_zscore,
                            ) ?? 0
                          ).toFixed(2)}</td
                        >
                        <td
                          class="signal-cell"
                          class:minus={getLatestValue(
                            $dashboardData.reserves_metrics?.spread_zscore,
                          ) > 2}
                          class:plus={getLatestValue(
                            $dashboardData.reserves_metrics?.spread_zscore,
                          ) < -1}
                          >{getLatestValue(
                            $dashboardData.reserves_metrics?.spread_zscore,
                          ) > 2
                            ? currentTranslations.reserves_high_stress
                            : getLatestValue(
                                  $dashboardData.reserves_metrics
                                    ?.spread_zscore,
                                ) < -1
                              ? currentTranslations.reserves_low_stress
                              : currentTranslations.reserves_normal}</td
                        >
                      </tr>
                      <tr>
                        <td>{currentTranslations.momentum}</td>
                        <td
                          class="roc-val"
                          class:positive={getLatestValue(
                            $dashboardData.reserves_metrics?.momentum,
                          ) > 0}
                          class:negative={getLatestValue(
                            $dashboardData.reserves_metrics?.momentum,
                          ) < 0}
                          >{(
                            getLatestValue(
                              $dashboardData.reserves_metrics?.momentum,
                            ) ?? 0
                          ).toFixed(4)}T</td
                        >
                        <td
                          class="signal-cell"
                          class:plus={getLatestValue(
                            $dashboardData.reserves_metrics?.momentum,
                          ) > 0}
                          class:minus={getLatestValue(
                            $dashboardData.reserves_metrics?.momentum,
                          ) < 0}
                          >{getLatestValue(
                            $dashboardData.reserves_metrics?.momentum,
                          ) > 0
                            ? currentTranslations.reserves_bullish
                            : getLatestValue(
                                  $dashboardData.reserves_metrics?.momentum,
                                ) < 0
                              ? currentTranslations.reserves_bearish
                              : currentTranslations.reserves_neutral}</td
                        >
                      </tr>
                      <tr>
                        <td>{currentTranslations.lcr}</td>
                        <td class="roc-val"
                          >{(
                            getLatestValue(
                              $dashboardData.reserves_metrics?.lcr,
                            ) ?? 0
                          ).toFixed(2)}%</td
                        >
                        <td class="signal-cell"
                          >{getLatestValue(
                            $dashboardData.reserves_metrics?.lcr,
                          ) < 30
                            ? "⚠️"
                            : "✓"}</td
                        >
                      </tr>
                    </tbody>
                  </table>
                  <p style="font-size: 10px; color: #94a3b8; margin-top: 8px;">
                    * Z&gt;2 = Liquidity blocked | Z&lt;-1 = Excess liquidity
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div class="chart-card">
            <div class="chart-header">
              <h3>{currentTranslations.chart_fed_assets}</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={fedRange}
                  onRangeChange={(r) => (fedRange = r)}
                />
                <span class="last-date"
                  >{currentTranslations.last_data} {getLastDate("FED")}</span
                >
              </div>
            </div>
            <p class="chart-description">{currentTranslations.gli_cb}</p>
            <div class="chart-content">
              <Chart {darkMode} data={fedData} />
            </div>
            <!-- ROC Metrics -->
            <div
              class="roc-inline"
              style="display: flex; gap: 12px; margin-top: 8px; font-size: 11px;"
            >
              <span>ROC:</span>
              <span
                class:positive={getLatestValue(
                  $dashboardData.us_system_rocs?.fed?.["1M"],
                ) > 0}
                class:negative={getLatestValue(
                  $dashboardData.us_system_rocs?.fed?.["1M"],
                ) < 0}
                >1M: {(
                  getLatestValue($dashboardData.us_system_rocs?.fed?.["1M"]) ??
                  0
                ).toFixed(1)}%</span
              >
              <span
                class:positive={getLatestValue(
                  $dashboardData.us_system_rocs?.fed?.["3M"],
                ) > 0}
                class:negative={getLatestValue(
                  $dashboardData.us_system_rocs?.fed?.["3M"],
                ) < 0}
                >3M: {(
                  getLatestValue($dashboardData.us_system_rocs?.fed?.["3M"]) ??
                  0
                ).toFixed(1)}%</span
              >
              <span
                class:positive={getLatestValue(
                  $dashboardData.us_system_rocs?.fed?.["1Y"],
                ) > 0}
                class:negative={getLatestValue(
                  $dashboardData.us_system_rocs?.fed?.["1Y"],
                ) < 0}
                >1Y: {(
                  getLatestValue($dashboardData.us_system_rocs?.fed?.["1Y"]) ??
                  0
                ).toFixed(1)}%</span
              >
              <span style="margin-left: auto; color: #94a3b8;">
                {getLatestValue($dashboardData.us_system_rocs?.fed?.["1M"]) > 0
                  ? language === "en"
                    ? "↑ Expansion"
                    : "↑ Expansión"
                  : language === "en"
                    ? "↓ Contraction"
                    : "↓ Contracción"}
              </span>
            </div>
          </div>

          <div class="chart-card">
            <div class="chart-header">
              <h3>{currentTranslations.chart_rrp}</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={rrpRange}
                  onRangeChange={(r) => (rrpRange = r)}
                />
                <span class="last-date"
                  >{currentTranslations.last_data} {getLastDate("RRP")}</span
                >
              </div>
            </div>
            <p class="chart-description">{currentTranslations.rrp}</p>
            <div class="chart-content">
              <Chart {darkMode} data={rrpData} />
            </div>
            <!-- ROC Metrics (inverted: RRP down = bullish) -->
            <div
              class="roc-inline"
              style="display: flex; gap: 12px; margin-top: 8px; font-size: 11px;"
            >
              <span>ROC:</span>
              <span
                class:positive={getLatestValue(
                  $dashboardData.us_system_rocs?.rrp?.["1M"],
                ) < 0}
                class:negative={getLatestValue(
                  $dashboardData.us_system_rocs?.rrp?.["1M"],
                ) > 0}
                >1M: {(
                  getLatestValue($dashboardData.us_system_rocs?.rrp?.["1M"]) ??
                  0
                ).toFixed(1)}%</span
              >
              <span
                class:positive={getLatestValue(
                  $dashboardData.us_system_rocs?.rrp?.["3M"],
                ) < 0}
                class:negative={getLatestValue(
                  $dashboardData.us_system_rocs?.rrp?.["3M"],
                ) > 0}
                >3M: {(
                  getLatestValue($dashboardData.us_system_rocs?.rrp?.["3M"]) ??
                  0
                ).toFixed(1)}%</span
              >
              <span
                class:positive={getLatestValue(
                  $dashboardData.us_system_rocs?.rrp?.["1Y"],
                ) < 0}
                class:negative={getLatestValue(
                  $dashboardData.us_system_rocs?.rrp?.["1Y"],
                ) > 0}
                >1Y: {(
                  getLatestValue($dashboardData.us_system_rocs?.rrp?.["1Y"]) ??
                  0
                ).toFixed(1)}%</span
              >
              <span style="margin-left: auto; color: #94a3b8;">
                {getLatestValue($dashboardData.us_system_rocs?.rrp?.["1M"]) < 0
                  ? language === "en"
                    ? "↓ Draining (bullish)"
                    : "↓ Drenando (alcista)"
                  : language === "en"
                    ? "↑ Filling (bearish)"
                    : "↑ Llenando (bajista)"}
              </span>
            </div>
          </div>

          <div class="chart-card">
            <div class="chart-header">
              <h3>{currentTranslations.chart_tga}</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={tgaRange}
                  onRangeChange={(r) => (tgaRange = r)}
                />
                <span class="last-date"
                  >{currentTranslations.last_data} {getLastDate("TGA")}</span
                >
              </div>
            </div>
            <p class="chart-description">{currentTranslations.tga}</p>
            <div class="chart-content">
              <Chart {darkMode} data={tgaData} />
            </div>
            <!-- ROC Metrics (inverted: TGA down = bullish) -->
            <div
              class="roc-inline"
              style="display: flex; gap: 12px; margin-top: 8px; font-size: 11px;"
            >
              <span>ROC:</span>
              <span
                class:positive={getLatestValue(
                  $dashboardData.us_system_rocs?.tga?.["1M"],
                ) < 0}
                class:negative={getLatestValue(
                  $dashboardData.us_system_rocs?.tga?.["1M"],
                ) > 0}
                >1M: {(
                  getLatestValue($dashboardData.us_system_rocs?.tga?.["1M"]) ??
                  0
                ).toFixed(1)}%</span
              >
              <span
                class:positive={getLatestValue(
                  $dashboardData.us_system_rocs?.tga?.["3M"],
                ) < 0}
                class:negative={getLatestValue(
                  $dashboardData.us_system_rocs?.tga?.["3M"],
                ) > 0}
                >3M: {(
                  getLatestValue($dashboardData.us_system_rocs?.tga?.["3M"]) ??
                  0
                ).toFixed(1)}%</span
              >
              <span
                class:positive={getLatestValue(
                  $dashboardData.us_system_rocs?.tga?.["1Y"],
                ) < 0}
                class:negative={getLatestValue(
                  $dashboardData.us_system_rocs?.tga?.["1Y"],
                ) > 0}
                >1Y: {(
                  getLatestValue($dashboardData.us_system_rocs?.tga?.["1Y"]) ??
                  0
                ).toFixed(1)}%</span
              >
              <span style="margin-left: auto; color: #94a3b8;">
                {getLatestValue($dashboardData.us_system_rocs?.tga?.["1M"]) < 0
                  ? language === "en"
                    ? "↓ Spending (bullish)"
                    : "↓ Gastando (alcista)"
                  : language === "en"
                    ? "↑ Accumulating (bearish)"
                    : "↑ Acumulando (bajista)"}
              </span>
            </div>
          </div>
        </div>
      {:else if currentTab === "Risk Model"}
        <div class="main-charts">
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>Credit Liquidity Index (CLI Aggregate)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={cliRange}
                  onRangeChange={(r) => (cliRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("NFCI")}</span>
              </div>
            </div>
            <p class="chart-description">{currentTranslations.cli}</p>
            <div class="chart-content">
              <Chart {darkMode} data={cliData} />
            </div>
          </div>

          {#each [{ id: "hy", name: "HY Spread Contrast", data: hyZData, range: hyRange, setRange: (r) => (hyRange = r), bank: "HY_SPREAD", descKey: "hy_spread" }, { id: "ig", name: "IG Spread Contrast", data: igZData, range: igRange, setRange: (r) => (igRange = r), bank: "IG_SPREAD", descKey: "ig_spread" }, { id: "nfci_credit", name: "NFCI Credit Contrast", data: nfciCreditZData, range: nfciRange, setRange: (r) => (nfciRange = r), bank: "NFCI", descKey: "nfci_credit" }, { id: "nfci_risk", name: "NFCI Risk Contrast", data: nfciRiskZData, range: nfciRange, setRange: (r) => (nfciRange = r), bank: "NFCI", descKey: "nfci_risk" }, { id: "lending", name: "Lending Standards Contrast", data: lendingZData, range: lendingRange, setRange: (r) => (lendingRange = r), bank: "LENDING_STD", descKey: "lending" }, { id: "vix_z", name: "VIX Contrast (Z-Score)", data: vixZData, range: vixRange, setRange: (r) => (vixRange = r), bank: "VIX", descKey: "vix" }] as item}
            <div class="chart-card">
              <div class="chart-header">
                <h3>{item.name}</h3>
                <div class="header-controls">
                  <TimeRangeSelector
                    selectedRange={item.range}
                    onRangeChange={item.setRange}
                  />
                  <span class="last-date">Last: {getLastDate(item.bank)}</span>
                </div>
              </div>
              <p class="chart-description">
                {currentTranslations[item.descKey]}
              </p>
              <div class="chart-content">
                <Chart {darkMode} data={item.data} />
              </div>
            </div>
          {/each}

          <!-- TIPS / Inflation Expectations Chart -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>{currentTranslations.chart_inflation_exp}</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={tipsRange}
                  onRangeChange={(r) => (tipsRange = r)}
                />
                <span class="last-date"
                  >{currentTranslations.last_data}
                  {getLastDate("TIPS_BREAKEVEN")}</span
                >
              </div>
            </div>
            <p class="chart-description">{currentTranslations.tips}</p>
            <div class="chart-content">
              <Chart {darkMode} data={tipsData} layout={tipsLayout} />
            </div>
          </div>

          <div class="chart-card wide">
            <div class="gli-layout">
              <div class="chart-main">
                <div class="chart-header">
                  <h3>{currentTranslations.chart_repo_stress}</h3>
                  <div class="header-controls">
                    <TimeRangeSelector
                      selectedRange={repoStressRange}
                      onRangeChange={(r) => (repoStressRange = r)}
                    />
                    <span class="last-date"
                      >{currentTranslations.last_data}
                      {getLastDate("SOFR")}</span
                    >
                  </div>
                </div>
                <p class="chart-description">
                  {currentTranslations.repo_stress}
                </p>
                <div class="chart-content">
                  <Chart {darkMode} data={repoStressData} />
                </div>
              </div>

              <div class="metrics-sidebar">
                <div class="metrics-section">
                  <h4>SOFR vs IORB</h4>
                  <table class="metrics-table compact">
                    <thead>
                      <tr>
                        <th>Rate</th>
                        <th>Value</th>
                        <th>Role</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td style="color: #f59e0b; font-weight: 600;">SOFR</td>
                        <td
                          >{(
                            getLatestValue($dashboardData.repo_stress?.sofr) ??
                            0
                          ).toFixed(2)}%</td
                        >
                        <td style="font-size: 10px;"
                          >{language === "en"
                            ? "Market Rate"
                            : "Tasa Mercado"}</td
                        >
                      </tr>
                      <tr>
                        <td style="color: #8b5cf6; font-weight: 600;">IORB</td>
                        <td
                          >{(
                            getLatestValue($dashboardData.repo_stress?.iorb) ??
                            0
                          ).toFixed(2)}%</td
                        >
                        <td style="font-size: 10px;"
                          >{language === "en" ? "Fed Floor" : "Piso Fed"}</td
                        >
                      </tr>
                      <tr>
                        <td>Spread</td>
                        <td
                          class:positive={getLatestValue(
                            $dashboardData.repo_stress?.sofr,
                          ) -
                            getLatestValue($dashboardData.repo_stress?.iorb) >
                            0}
                          class:negative={getLatestValue(
                            $dashboardData.repo_stress?.sofr,
                          ) -
                            getLatestValue($dashboardData.repo_stress?.iorb) <
                            -0.05}
                          >{(
                            (getLatestValue($dashboardData.repo_stress?.sofr) ??
                              0) -
                            (getLatestValue($dashboardData.repo_stress?.iorb) ??
                              0)
                          ).toFixed(2)} bps</td
                        >
                        <td
                          class="signal-cell"
                          class:plus={getLatestValue(
                            $dashboardData.repo_stress?.sofr,
                          ) -
                            getLatestValue($dashboardData.repo_stress?.iorb) >
                            0}
                          class:minus={getLatestValue(
                            $dashboardData.repo_stress?.sofr,
                          ) -
                            getLatestValue($dashboardData.repo_stress?.iorb) <
                            -0.05}
                          >{getLatestValue($dashboardData.repo_stress?.sofr) >
                          getLatestValue($dashboardData.repo_stress?.iorb)
                            ? "OK"
                            : "⚠️"}</td
                        >
                      </tr>
                    </tbody>
                  </table>
                  <div
                    style="margin-top: 10px; font-size: 10px; color: #94a3b8;"
                  >
                    <p>
                      <strong>SOFR</strong>: {language === "en"
                        ? "Secured Overnight Financing Rate - market repo rate"
                        : "Tasa de Financiamiento Garantizado - tasa repo de mercado"}
                    </p>
                    <p>
                      <strong>IORB</strong>: {language === "en"
                        ? "Interest on Reserve Balances - Fed floor rate"
                        : "Interés sobre Reservas - tasa piso de Fed"}
                    </p>
                    <p style="margin-top: 6px; color: #ef4444;">
                      {language === "en"
                        ? "⚠️ SOFR < IORB = Funding stress (like Sep 2019)"
                        : "⚠️ SOFR < IORB = Estrés de financiamiento (como Sep 2019)"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- NEW ROC Section -->
        <div class="roc-section">
          <div class="roc-card">
            <h4>Pulsar Momentum (ROC)</h4>
            <div class="roc-grid">
              <div class="roc-row header">
                <div class="roc-col">Factor</div>
                <div class="roc-col">1M</div>
                <div class="roc-col">3M</div>
                <div class="roc-col">6M</div>
                <div class="roc-col">1Y</div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">Global GLI</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "1M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "1M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "1M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "3M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "3M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "3M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "6M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "6M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "6M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "1Y") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "1Y") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "1Y").toFixed(2)}%
                </div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">US Net Liq</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "1M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "3M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "3M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "3M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "6M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "6M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "6M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1Y",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1Y",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "1Y").toFixed(
                    2,
                  )}%
                </div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">Fed Assets</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.bank_rocs.fed, "1M") >
                    0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.fed,
                    "1M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.fed, "1M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.bank_rocs.fed, "3M") >
                    0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.fed,
                    "3M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.fed, "3M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.bank_rocs.fed, "6M") >
                    0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.fed,
                    "6M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.fed, "6M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.bank_rocs.fed, "1Y") >
                    0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.fed,
                    "1Y",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.fed, "1Y").toFixed(2)}%
                </div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">PBoC Assets</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "1M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "1M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.pboc, "1M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "3M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "3M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.pboc, "3M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "6M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "6M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.pboc, "6M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "1Y",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "1Y",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.pboc, "1Y").toFixed(
                    2,
                  )}%
                </div>
              </div>
            </div>
          </div>
        </div>
      {:else if currentTab === "Global M2"}
        <div class="main-charts">
          <!-- Global M2 Overview -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>💰 Global M2 Money Supply (5 Major Economies)</h3>
              <span class="last-date">USA + EU + China + Japan + UK</span>
            </div>
            <div class="chart-content">
              <Chart
                data={[
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.total,
                    type: "scatter",
                    mode: "lines",
                    fill: "tozeroy",
                    name: "Global M2",
                    line: { color: "#10b981", width: 2 },
                  },
                ]}
              />
            </div>
          </div>

          <!-- M2 Breakdown by Economy -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>📊 M2 by Economy (Trillions USD)</h3>
            </div>
            <div class="chart-content">
              <Chart
                data={[
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.us,
                    type: "scatter",
                    mode: "lines",
                    name: "USA",
                    line: { color: "#3b82f6", width: 2 },
                  },
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.cn,
                    type: "scatter",
                    mode: "lines",
                    name: "China",
                    line: { color: "#ef4444", width: 2 },
                  },
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.eu,
                    type: "scatter",
                    mode: "lines",
                    name: "EU",
                    line: { color: "#f59e0b", width: 2 },
                  },
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.jp,
                    type: "scatter",
                    mode: "lines",
                    name: "Japan",
                    line: { color: "#8b5cf6", width: 2 },
                  },
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.uk,
                    type: "scatter",
                    mode: "lines",
                    name: "UK",
                    line: { color: "#06b6d4", width: 2 },
                  },
                ]}
              />
            </div>
          </div>

          <!-- M2 ROCs -->
          <div class="roc-section">
            <div class="roc-card">
              <h4>M2 Momentum (ROC)</h4>
              <div class="roc-grid">
                <div class="roc-row header">
                  <div class="roc-col">Factor</div>
                  <div class="roc-col">1M</div>
                  <div class="roc-col">3M</div>
                  <div class="roc-col">6M</div>
                  <div class="roc-col">1Y</div>
                </div>
                <div class="roc-row">
                  <div class="roc-col label">Global M2</div>
                  <div
                    class="roc-col"
                    class:plus={getLatestROC($dashboardData.m2?.rocs, "1M") > 0}
                    class:minus={getLatestROC($dashboardData.m2?.rocs, "1M") <
                      0}
                  >
                    {getLatestROC($dashboardData.m2?.rocs, "1M").toFixed(2)}%
                  </div>
                  <div
                    class="roc-col"
                    class:plus={getLatestROC($dashboardData.m2?.rocs, "3M") > 0}
                    class:minus={getLatestROC($dashboardData.m2?.rocs, "3M") <
                      0}
                  >
                    {getLatestROC($dashboardData.m2?.rocs, "3M").toFixed(2)}%
                  </div>
                  <div
                    class="roc-col"
                    class:plus={getLatestROC($dashboardData.m2?.rocs, "6M") > 0}
                    class:minus={getLatestROC($dashboardData.m2?.rocs, "6M") <
                      0}
                  >
                    {getLatestROC($dashboardData.m2?.rocs, "6M").toFixed(2)}%
                  </div>
                  <div
                    class="roc-col"
                    class:plus={getLatestROC($dashboardData.m2?.rocs, "1Y") > 0}
                    class:minus={getLatestROC($dashboardData.m2?.rocs, "1Y") <
                      0}
                  >
                    {getLatestROC($dashboardData.m2?.rocs, "1Y").toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      {:else if currentTab === "BTC Analysis"}
        <div class="main-charts btc-analysis-view">
          <!-- BTC Price vs Fair Value -->
          <div class="analysis-header">
            <h2>{currentTranslations.btc_analysis_title}</h2>
            <p class="description">
              {currentTranslations.btc_analysis_desc}
            </p>
          </div>

          <div class="btc-stats">
            <div class="btc-stat-item">
              <span class="btc-label"
                >{currentTranslations.current_valuation}</span
              >
              <div
                class="btc-value"
                class:overvalued={$latestStats?.btc?.deviation_pct > 0}
              >
                {(($latestStats?.btc?.deviation_pct || 0) > 0 ? "+" : "") +
                  ($latestStats?.btc?.deviation_pct || 0).toFixed(1)}%
              </div>
            </div>
            <div class="btc-stat-item">
              <span class="btc-label">{currentTranslations.btc_price}</span>
              <span class="btc-value"
                >${Math.round(
                  $latestStats?.btc?.price || 0,
                ).toLocaleString()}</span
              >
            </div>
            <div class="btc-stat-item">
              <span class="btc-label">{currentTranslations.fair_value}</span>
              <span class="btc-value"
                >${Math.round(
                  $latestStats?.btc?.fair_value || 0,
                ).toLocaleString()}</span
              >
            </div>
            <div class="btc-stat-item">
              <span class="btc-label">{currentTranslations.zscore}</span>
              <span class="btc-value"
                >{($latestStats?.btc?.deviation_zscore || 0).toFixed(2)}σ</span
              >
            </div>
          </div>

          <div class="chart-card wide">
            <div class="chart-header">
              <h3>{currentTranslations.btc_analysis_title}</h3>
              <div class="header-controls">
                <div class="model-toggle">
                  <button
                    class="toggle-btn"
                    class:active={selectedBtcModel === "macro"}
                    on:click={() => (selectedBtcModel = "macro")}
                    >Macro Liquidity</button
                  >
                  <button
                    class="toggle-btn"
                    class:active={selectedBtcModel === "adoption"}
                    on:click={() => (selectedBtcModel = "adoption")}
                    >Macro + Adoption</button
                  >
                </div>
                <TimeRangeSelector
                  selectedRange={btcRange}
                  onRangeChange={(r) => (btcRange = r)}
                />
              </div>
            </div>
            <p class="chart-description">{currentTranslations.btc_fair}</p>
            <div class="chart-content tv-chart-wrap">
              <LightweightChart
                {darkMode}
                data={btcFairValueData}
                logScale={true}
              />
              <div class="debug-chart-info">
                Points: {btcFairValueData[0]?.data?.length || 0}
              </div>
            </div>
          </div>

          <!-- Deviation Stats -->

          <!-- Predictive Signals (CLI vs BTC Lag Correlation) -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>{currentTranslations.lag_analysis}</h3>
              <div class="header-controls">
                <div class="model-toggle">
                  <button
                    class="toggle-btn"
                    class:active={selectedLagWindow === "7d"}
                    on:click={() => (selectedLagWindow = "7d")}>7-Day</button
                  >
                  <button
                    class="toggle-btn"
                    class:active={selectedLagWindow === "14d"}
                    on:click={() => (selectedLagWindow = "14d")}>14-Day</button
                  >
                  <button
                    class="toggle-btn"
                    class:active={selectedLagWindow === "30d"}
                    on:click={() => (selectedLagWindow = "30d")}>30-Day</button
                  >
                </div>
              </div>
            </div>
            <div class="gli-layout">
              <div class="chart-main">
                <div class="chart-content" style="height: 350px;">
                  <Chart {darkMode} data={lagCorrelationChartData} />
                </div>
              </div>
              <div class="metrics-sidebar">
                <div class="interp-card">
                  <h4>{currentTranslations.interpretation}</h4>
                  <div class="metric-row">
                    <span>{currentTranslations.optimal_lag}</span>
                    <span class="val"
                      >{$dashboardData.predictive?.lag_correlations?.[
                        selectedLagWindow
                      ]?.optimal_lag || 0}W</span
                    >
                  </div>
                  <div class="metric-row">
                    <span>{currentTranslations.max_correlation}</span>
                    <span class="val"
                      >{(
                        ($dashboardData.predictive?.lag_correlations?.[
                          selectedLagWindow
                        ]?.max_correlation || 0) * 100
                      ).toFixed(1)}%</span
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Cross-Correlation Chart -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>Cross-Correlation Analysis (90-Day Window)</h3>
              <span class="last-date"
                >Negative lag = indicator leads BTC | Positive lag = BTC leads
                indicator</span
              >
            </div>
            <div class="chart-content">
              <Chart {darkMode} data={correlationData} />
            </div>
          </div>

          <!-- ROC Comparison -->
          <div class="chart-card wide">
            <h4>Momentum Comparison (ROC %)</h4>
            <div class="roc-grid">
              <div class="roc-row header">
                <div class="roc-col">Asset</div>
                <div class="roc-col">1M</div>
                <div class="roc-col">3M</div>
                <div class="roc-col">6M</div>
                <div class="roc-col">1Y</div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">{currentTranslations.btc_price}</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.btc?.rocs, "1M") > 0}
                  class:minus={getLatestROC($dashboardData.btc?.rocs, "1M") < 0}
                >
                  {getLatestROC($dashboardData.btc?.rocs, "1M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.btc?.rocs, "3M") > 0}
                  class:minus={getLatestROC($dashboardData.btc?.rocs, "3M") < 0}
                >
                  {getLatestROC($dashboardData.btc?.rocs, "3M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.btc?.rocs, "6M") > 0}
                  class:minus={getLatestROC($dashboardData.btc?.rocs, "6M") < 0}
                >
                  {getLatestROC($dashboardData.btc?.rocs, "6M").toFixed(2)}%
                </div>
                <div
                  class:plus={getLatestROC($dashboardData.btc?.rocs, "1Y") > 0}
                  class:minus={getLatestROC($dashboardData.btc?.rocs, "1Y") < 0}
                >
                  {getLatestROC($dashboardData.btc?.rocs, "1Y").toFixed(2)}%
                </div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">Global GLI</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "1M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "1M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "1M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "3M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "3M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "3M").toFixed(2)}%
                </div>
                <div
                  class:plus={getLatestROC($dashboardData.gli.rocs, "6M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "6M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "6M").toFixed(2)}%
                </div>
                <div
                  class:plus={getLatestROC($dashboardData.gli.rocs, "1Y") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "1Y") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "1Y").toFixed(2)}%
                </div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">
                  US {currentTranslations.stat_us_net}
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "1M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "3M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "3M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "3M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "6M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "6M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "6M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1Y",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1Y",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "1Y").toFixed(
                    2,
                  )}%
                </div>
              </div>
            </div>
          </div>

          <!-- Interpretation Panel -->
          <div class="chart-card wide interpretation-panel">
            <h4>📊 {currentTranslations.interpretation}</h4>
            <div class="interpretation-grid">
              <div class="interp-card">
                <h5>{currentTranslations.fair_value} Model</h5>
                <p>
                  {currentTranslations.interp_regression}<br />
                  • {currentTranslations.interp_gli_lag}<br />
                  • {currentTranslations.interp_cli_lag}<br />
                  • {currentTranslations.interp_vix_coin}<br />
                  • {currentTranslations.interp_netliq_lag}
                </p>
              </div>
              <div class="interp-card">
                <h5>{currentTranslations.interp_zones}</h5>
                <p>
                  • <span class="extreme-zone"
                    >{currentTranslations.interp_extreme}</span
                  ><br />
                  •
                  <span class="moderate-zone"
                    >{currentTranslations.interp_moderate}</span
                  ><br />
                  • {currentTranslations.interp_fair_range}
                </p>
              </div>
              <div class="interp-card">
                <h5>{currentTranslations.interp_signals}</h5>
                <p>
                  • <strong>{currentTranslations.interp_profittaking}</strong
                  ><br />
                  •
                  <strong>{currentTranslations.interp_accumulation}</strong><br
                  />
                  • <strong>{currentTranslations.interp_divergence}</strong>
                </p>
              </div>
            </div>
          </div>
        </div>
      {:else if currentTab === "BTC Quant v2"}
        <div class="main-charts">
          <!-- Quant v2 Model Description -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>🧪 {currentTranslations.quant_v2_title}</h3>
              <span class="last-date"
                >Weekly Δlog returns + ElasticNet + PCA GLI Factor</span
              >
            </div>
            <div class="quant-description">
              <p>
                {currentTranslations.quant_v2_desc}
              </p>
              <ul>
                <li>
                  {currentTranslations.quant_v2_weekly}
                </li>
                <li>
                  {currentTranslations.quant_v2_log}
                </li>
                <li>
                  {currentTranslations.quant_v2_elastic}
                </li>
                <li>
                  {currentTranslations.quant_v2_pca}
                </li>
                <li>
                  {currentTranslations.quant_v2_vol}
                </li>
              </ul>
            </div>
          </div>

          <!-- OOS Metrics Panel -->
          <div class="chart-card">
            <div class="chart-header">
              <h3>📈 {currentTranslations.oos_metrics}</h3>
            </div>
            <div class="quant-metrics">
              <div class="metric-item">
                <span class="metric-label">OOS RMSE</span>
                <span class="metric-value"
                  >{(
                    $dashboardData.btc?.models?.quant_v2?.metrics?.oos_rmse || 0
                  ).toFixed(4)}</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">OOS MAE</span>
                <span class="metric-value"
                  >{(
                    $dashboardData.btc?.models?.quant_v2?.metrics?.oos_mae || 0
                  ).toFixed(4)}</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">Hit Rate</span>
                <span class="metric-value highlight"
                  >{(
                    ($dashboardData.btc?.models?.quant_v2?.metrics?.hit_rate ||
                      0) * 100
                  ).toFixed(2)}%</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">R² In-Sample</span>
                <span class="metric-value"
                  >{(
                    ($dashboardData.btc?.models?.quant_v2?.metrics
                      ?.r2_insample || 0) * 100
                  ).toFixed(2)}%</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">Active Features</span>
                <span class="metric-value"
                  >{$dashboardData.btc?.models?.quant_v2?.metrics
                    ?.n_active_features || 0}</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">Frequency</span>
                <span class="metric-value"
                  >{$dashboardData.btc?.models?.quant_v2?.frequency ||
                    "weekly"}</span
                >
              </div>
            </div>
          </div>

          <!-- {currentTranslations.model_params} -->
          <div class="chart-card">
            <div class="chart-header">
              <h3>⚙️ {currentTranslations.model_params}</h3>
            </div>
            <div class="quant-metrics">
              <div class="metric-item">
                <span class="metric-label">Alpha (λ)</span>
                <span class="metric-value"
                  >{(
                    $dashboardData.btc?.models?.quant_v2?.metrics?.alpha || 0
                  ).toFixed(6)}</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">L1 Ratio</span>
                <span class="metric-value"
                  >{$dashboardData.btc?.models?.quant_v2?.metrics?.l1_ratio ||
                    0}</span
                >
              </div>
            </div>
          </div>

          <!-- Fair Value Chart (Cumulative) -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>₿ Bitcoin: Quant v2 Fair Value (Weekly - Cumulative)</h3>
              <span class="last-date"
                >⚠️ Cumulative drift may cause divergence over time</span
              >
            </div>
            <div class="chart-content tv-chart-wrap">
              <LightweightChart
                {darkMode}
                data={quantV2ChartData}
                logScale={true}
              />
            </div>
          </div>

          <!-- Rebalanced Fair Value Chart -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>₿ Bitcoin: Rebalanced Fair Value (Quarterly Reset)</h3>
              <span class="last-date"
                >✅ Resets to actual price every 13 weeks to avoid drift</span
              >
            </div>
            <div class="chart-content tv-chart-wrap">
              <LightweightChart
                {darkMode}
                data={quantV2RebalancedData}
                logScale={true}
              />
            </div>
          </div>

          <!-- Returns Comparison Chart -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>📊 Weekly Returns: Predicted vs Actual (%)</h3>
              <span class="last-date"
                >Orange bars = Actual | Green line = Predicted</span
              >
            </div>
            <div class="chart-content">
              <Chart {darkMode} data={quantV2ReturnsData} />
            </div>
          </div>

          <!-- Active Features List -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>🎯 Active Features (Selected by ElasticNet)</h3>
            </div>
            <div class="features-grid">
              {#each Object.entries($dashboardData.btc?.models?.quant_v2?.active_features || {}) as [feature, coef]}
                <div
                  class="feature-item"
                  class:positive={coef > 0}
                  class:negative={coef < 0}
                >
                  <span class="feature-name">{feature}</span>
                  <span class="feature-coef">{coef.toFixed(4)}</span>
                </div>
              {/each}
            </div>
          </div>

          <!-- Current Valuation -->
          <div class="chart-card">
            <div class="chart-header">
              <h3>📊 Current Valuation (Quant v2)</h3>
            </div>
            <div class="btc-stats">
              <div class="btc-stat-item">
                <span class="btc-label">{currentTranslations.btc_price}</span>
                <span class="btc-value price">
                  ${getLatestValue(
                    $dashboardData.btc?.models?.quant_v2?.btc_price,
                  )?.toLocaleString() || "N/A"}
                </span>
              </div>
              <div class="btc-stat-item">
                <span class="btc-label">{currentTranslations.fair_value}</span>
                <span class="btc-value fair">
                  ${Math.round(
                    getLatestValue(
                      $dashboardData.btc?.models?.quant_v2?.fair_value,
                    ) || 0,
                  ).toLocaleString()}
                </span>
              </div>
              <div class="btc-stat-item">
                <span class="btc-label">{currentTranslations.deviation}</span>
                <span
                  class="btc-value deviation"
                  class:overvalued={getLatestValue(
                    $dashboardData.btc?.models?.quant_v2?.deviation_pct,
                  ) > 0}
                  class:undervalued={getLatestValue(
                    $dashboardData.btc?.models?.quant_v2?.deviation_pct,
                  ) < 0}
                >
                  {getLatestValue(
                    $dashboardData.btc?.models?.quant_v2?.deviation_pct,
                  )?.toFixed(1) || "0"}%
                </span>
              </div>
              <div class="btc-stat-item">
                <span class="btc-label">{currentTranslations.zscore}</span>
                <span
                  class="btc-value zscore"
                  class:extreme={Math.abs(
                    getLatestValue(
                      $dashboardData.btc?.models?.quant_v2?.deviation_zscore,
                    ) || 0,
                  ) > 2}
                >
                  {getLatestValue(
                    $dashboardData.btc?.models?.quant_v2?.deviation_zscore,
                  )?.toFixed(2) || "0"}σ
                </span>
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </main>
</div>

<style>
  /* CSS Variables for Theme */
  :global(:root) {
    --bg-primary: #f8fafc;
    --bg-secondary: #ffffff;
    --bg-tertiary: #f1f5f9;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --border-color: #e2e8f0;
    --accent-primary: #4f46e5;
    --accent-secondary: #3b82f6;
    --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    --chart-description-bg: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    --positive-color: #059669;
    --negative-color: #dc2626;
  }

  :global([data-theme="dark"]) {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --text-primary: #f8fafc;
    --text-secondary: #cbd5e1;
    --text-muted: #94a3b8;
    --border-color: #334155;
    --accent-primary: #6366f1;
    --accent-secondary: #60a5fa;
    --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    --chart-description-bg: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    --positive-color: #10b981;
    --negative-color: #f87171;
  }

  :global(body) {
    margin: 0;
    padding: 0;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family:
      "Inter",
      -apple-system,
      system-ui,
      sans-serif;
    overflow-x: hidden;
    transition:
      background-color 0.3s ease,
      color 0.3s ease;
  }

  .app-container {
    display: flex;
    min-height: 100vh;
    width: 100vw;
  }

  .sidebar {
    width: 280px;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    padding: 40px 24px;
    flex-shrink: 0;
    transition:
      background-color 0.3s ease,
      border-color 0.3s ease;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 48px;
    padding-left: 8px;
  }

  .logo-box {
    width: 44px;
    height: 44px;
    background: #4f46e5;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 800;
    font-size: 1.25rem;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
  }

  .brand-text h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .brand-text span {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
  }

  nav {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .nav-item {
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 0.9375rem;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 500;
  }

  .nav-icon {
    font-size: 1.125rem;
  }

  .nav-item:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .nav-item.active {
    background: rgba(79, 70, 229, 0.1);
    color: var(--accent-primary);
    font-weight: 600;
  }

  .sidebar-footer {
    margin-top: auto;
    padding: 0 8px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.8125rem;
    color: var(--text-muted);
    font-weight: 500;
  }

  .pulse {
    width: 10px;
    height: 10px;
    background: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 0 rgba(16, 185, 129, 0.4);
    animation: pulse-light 2s infinite;
  }

  @keyframes pulse-light {
    0% {
      transform: scale(0.95);
      box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6);
    }
    70% {
      transform: scale(1);
      box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
    }
    100% {
      transform: scale(0.95);
      box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
    }
  }

  .content {
    flex: 1;
    padding: 48px;
    overflow-y: auto;
    background: var(--bg-primary);
    transition: background-color 0.3s ease;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 48px;
    max-width: 1600px;
    margin-right: auto;
  }

  .content-header h1 {
    margin: 0 0 4px 0;
    font-size: 2.25rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.025em;
  }

  .content-header p {
    margin: 0;
    color: var(--text-muted);
    font-size: 1.125rem;
  }

  .refresh-btn {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 10px 20px;
    border-radius: 12px;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: var(--card-shadow);
  }

  .refresh-btn:hover {
    background: var(--bg-tertiary);
    border-color: var(--accent-secondary);
    transform: translateY(-1px);
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .header-toggle {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border: 1px solid var(--border-color);
    background: var(--bg-secondary);
    border-radius: 10px;
    cursor: pointer;
    font-size: 0.8125rem;
    color: var(--text-secondary);
    transition: all 0.2s;
  }

  .header-toggle:hover {
    background: var(--accent-primary);
    color: white;
    border-color: var(--accent-primary);
  }

  .toggle-icon {
    font-size: 0.875rem;
  }

  .toggle-label {
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }

  .toggle-btn {
    border: none;
    background: transparent;
    padding: 6px 16px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 700;
    cursor: pointer;
    color: var(--text-muted);
    transition: all 0.2s;
  }

  .toggle-btn.active {
    background: var(--bg-secondary);
    color: var(--accent-primary);
    box-shadow: var(--card-shadow);
  }

  .btc-analysis-view {
    margin-top: 24px;
  }

  .btc-analysis-view h2 {
    margin-bottom: 8px;
    font-size: 1.75rem;
    color: var(--text-primary);
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .error-banner {
    background: #fef2f2;
    border: 1px solid #fee2e2;
    color: #dc2626;
    padding: 16px 24px;
    border-radius: 16px;
    margin-bottom: 32px;
    font-size: 0.9375rem;
    font-weight: 500;
  }

  .dashboard-grid {
    max-width: 1600px;
    margin-right: auto;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 32px;
    margin-bottom: 40px;
  }

  .main-charts {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 32px;
  }

  .chart-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 24px;
    padding: 32px;
    display: flex;
    flex-direction: column;
    box-shadow: var(--card-shadow);
    transition:
      background-color 0.3s ease,
      border-color 0.3s ease;
  }

  .wide {
    grid-column: span 2;
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
  }

  .header-controls {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .chart-header h3 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .last-date {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 600;
    background: var(--bg-tertiary);
    padding: 4px 10px;
    border-radius: 6px;
  }

  .model-toggle {
    display: flex;
    gap: 8px;
    background: var(--bg-tertiary);
    padding: 4px;
    border-radius: 8px;
    width: fit-content;
  }

  .model-toggle .toggle-btn {
    padding: 6px 16px;
    font-size: 0.75rem;
    border: none;
    background: transparent;
    color: var(--text-muted);
    box-shadow: none;
  }

  .model-toggle .toggle-btn.active {
    background: var(--bg-secondary);
    color: var(--accent-primary);
    font-weight: 700;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  :global([data-theme="dark"]) .model-toggle .toggle-btn.active {
    background: #6366f1;
    color: white !important;
  }

  .roc-section {
    margin-top: 40px;
    max-width: 1600px;
  }

  .roc-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 24px;
    padding: 32px;
    box-shadow: var(--card-shadow);
  }

  .roc-card h4 {
    margin: 0 0 24px 0;
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--text-primary);
  }

  .roc-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .roc-row {
    display: grid;
    grid-template-columns: 2fr repeat(4, 1fr);
    padding: 12px 16px;
    border-radius: 12px;
    align-items: center;
  }

  .roc-row.header {
    background: var(--bg-tertiary);
    color: var(--text-muted);
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .roc-col.label {
    font-weight: 600;
    color: var(--text-primary);
  }

  .roc-col {
    display: flex;
    align-items: center;
    justify-content: flex-end;
  }

  .roc-row.header .roc-col {
    justify-content: flex-end;
  }

  .roc-row.header .roc-col:first-child {
    justify-content: flex-start;
  }

  .roc-col:first-child {
    justify-content: flex-start;
  }

  .roc-col.plus {
    color: var(--positive-color);
    font-weight: 700;
  }

  .roc-col.minus {
    color: var(--negative-color);
    font-weight: 700;
  }

  /* ROC Inline Display */
  .roc-inline {
    display: flex;
    gap: 16px;
    margin-top: 12px;
    padding: 10px 16px;
    font-size: 12px;
    background: var(--bg-tertiary);
    border-radius: 8px;
    justify-content: center;
    align-items: center;
    flex-wrap: wrap;
  }

  .roc-inline span {
    font-weight: 600;
  }

  .roc-inline span.positive {
    color: var(--positive-color);
    font-weight: 700;
  }

  .roc-inline span.negative {
    color: var(--negative-color);
    font-weight: 700;
  }

  .label-group {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .chart-content {
    min-height: 500px;
    height: 500px;
    flex: none; /* Force fixed height to rule out flex issues */
    width: 100%;
    position: relative;
    overflow: hidden;
  }

  .chart-description {
    margin: 8px 0 16px 0;
    padding: 12px 16px;
    background: var(--chart-description-bg);
    border-radius: 8px;
    font-size: 0.85rem;
    color: var(--text-secondary);
    line-height: 1.5;
    border-left: 3px solid var(--accent-secondary);
  }

  .debug-chart-info {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(0, 0, 0, 0.4);
    color: white;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    pointer-events: none;
    z-index: 100;
  }

  .loader {
    width: 28px;
    height: 28px;
    border: 3px solid var(--bg-tertiary);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  /* FX Toggle Styles */
  .fx-toggle {
    display: flex;
    background: var(--bg-tertiary);
    padding: 2px;
    border-radius: 8px;
    gap: 2px;
    margin-right: 8px;
    border: 1px solid var(--border-color);
  }

  .fx-btn {
    padding: 4px 10px;
    border: none;
    background: transparent;
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
  }

  .fx-btn:hover {
    color: #1e293b;
    background: rgba(255, 255, 255, 0.5);
  }

  .fx-btn.active {
    background: white;
    color: #6366f1;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  /* Color override for Constant FX active state */
  .fx-btn.active:last-child {
    color: #10b981;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* Quant v2 Tab Styles */
  .quant-description {
    padding: 16px;
    background: var(--bg-tertiary);
    border-radius: 8px;
    border-left: 4px solid var(--positive-color);
  }

  .quant-description p {
    margin: 0 0 12px 0;
    color: var(--positive-color);
    font-weight: 500;
  }

  .quant-description ul {
    margin: 0;
    padding-left: 20px;
    color: var(--text-secondary);
  }

  .quant-description li {
    margin-bottom: 6px;
    line-height: 1.5;
  }

  .quant-metrics {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    padding: 16px;
  }

  .metric-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 12px;
    background: var(--bg-tertiary);
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }

  .metric-label {
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
  }

  .metric-value {
    font-size: 20px;
    font-weight: 700;
    color: var(--text-primary);
  }

  .metric-value.highlight {
    color: var(--positive-color);
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    padding: 16px;
  }

  .feature-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    border-left: 3px solid var(--text-muted);
  }

  .feature-item.positive {
    border-left-color: var(--positive-color);
    background: rgba(16, 185, 129, 0.1);
  }

  .feature-item.negative {
    border-left-color: var(--negative-color);
    background: rgba(239, 68, 68, 0.1);
  }

  .feature-name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
  }

  .feature-coef {
    font-size: 13px;
    font-weight: 600;
    font-family: "Monaco", "Consolas", monospace;
    color: var(--text-secondary);
  }

  .feature-item.positive .feature-coef {
    color: var(--positive-color);
  }

  .feature-item.negative .feature-coef {
    color: var(--negative-color);
  }

  @media (max-width: 1200px) {
    .main-charts {
      grid-template-columns: 1fr;
    }
    .wide {
      grid-column: span 1;
    }
  }

  /* BTC Analysis Styles */
  .btc-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    padding: 24px;
  }

  .btc-stat-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 16px;
    background: var(--bg-tertiary);
    border-radius: 12px;
    border: 1px solid var(--border-color);
  }

  .btc-label {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .btc-value {
    font-size: 24px;
    font-weight: 700;
    color: var(--text-primary);
  }

  .btc-value.price {
    color: #f7931a;
  }

  .btc-value.fair {
    color: var(--positive-color);
  }

  .btc-value.deviation.overvalued {
    color: var(--negative-color);
  }

  .btc-value.deviation.undervalued {
    color: var(--positive-color);
  }

  .btc-value.zscore.extreme {
    color: var(--negative-color);
    animation: pulse 2s ease-in-out infinite;
  }

  .interpretation-panel {
    background: var(--bg-tertiary);
    border: 2px solid #fbbf24;
  }

  .interpretation-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    padding: 16px;
  }

  .interp-card {
    background: var(--bg-secondary);
    padding: 16px;
    border-radius: 8px;
    border: 1px solid #f59e0b;
  }

  .interp-card h5 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: #92400e;
  }

  .interp-card p {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
    color: #78350f;
  }

  .extreme-zone {
    color: #dc2626;
    font-weight: 600;
  }

  .moderate-zone {
    color: #f59e0b;
    font-weight: 600;
  }

  @media (max-width: 1200px) {
    .interpretation-grid {
      grid-template-columns: 1fr;
    }
    .btc-stats {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 768px) {
    .app-container {
      flex-direction: column;
    }
    .sidebar {
      width: 100%;
      height: auto;
      padding: 24px;
      border-right: none;
      border-bottom: 1px solid #e2e8f0;
    }
    .content {
      padding: 24px;
    }
  }

  /* GLI Metrics Panel */
  .gli-layout {
    display: grid;
    grid-template-columns: 1fr 420px;
    gap: 20px;
  }

  .metrics-sidebar {
    display: flex;
    flex-direction: column;
    gap: 20px;
    background: var(--bg-secondary);
    padding: 16px;
    border-radius: 12px;
    border: 1px solid var(--border-color);
    max-height: 800px;
    overflow-y: auto;
  }

  .metrics-section h4 {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-color);
  }

  .metrics-table {
    width: 100%;
    border-collapse: collapse;
  }

  .metrics-table th {
    text-align: left;
    font-size: 11px;
    color: var(--text-muted);
    padding-bottom: 8px;
  }

  .metrics-table th,
  .metrics-table td {
    padding: 8px 4px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
    font-size: 10px;
    color: var(--text-primary);
  }
  .impact-cell {
    background: var(--bg-tertiary);
    font-size: 9px;
    opacity: 0.9;
  }
  .metrics-table tr:last-child td {
    border-bottom: none;
  }

  .roc-val {
    font-weight: 600;
    font-family: "Monaco", "Consolas", monospace;
  }

  .roc-val.positive {
    color: #10b981;
  }
  .roc-val.negative {
    color: #ef4444;
  }

  /* Data Health Panel Styles */
  .data-health-section {
    border-left: 3px solid #10b981;
    background: rgba(16, 185, 129, 0.03);
    padding: 16px;
    margin-bottom: 8px;
  }

  .health-dot {
    width: 8px;
    height: 8px;
    background: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
    animation: pulse-green 2s infinite;
  }

  @keyframes pulse-green {
    0% {
      box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
    }
    70% {
      box-shadow: 0 0 0 10px rgba(16, 185, 129, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
    }
  }

  .health-table td {
    border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
  }

  .freshness-tag {
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
    font-size: 9px;
    font-weight: 700;
  }

  /* Liquidity Score */
  .liquidity-score {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-left: 12px;
    padding-left: 12px;
    border-left: 1px solid rgba(148, 163, 184, 0.2);
  }
  .score-label {
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
  }
  .score-val {
    font-size: 16px;
    font-weight: 700;
    color: var(--text-primary);
  }
  .score-val.high {
    color: #10b981;
    text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
  }
  .score-val.low {
    color: #ef4444;
    text-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
  }

  .freshness-tag.stale {
    background: rgba(245, 158, 11, 0.1);
    color: #f59e0b;
  }

  .coverage-note {
    margin-top: 12px;
    font-size: 11px;
    color: var(--text-muted);
    text-align: right;
  }

  @media (max-width: 1200px) {
    .gli-layout {
      grid-template-columns: 1fr;
    }
  }
  .total-row {
    background-color: rgba(148, 163, 184, 0.1);
    border-top: 2px solid var(--border-color);
  }
  .total-row td {
    padding-top: 10px !important;
    padding-bottom: 10px !important;
  }

  /* Macro Regime Panel */
  .regime-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    position: relative;
    overflow: hidden;
    box-shadow: var(--card-shadow);
    margin-bottom: 24px;
  }

  .regime-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }

  .regime-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .regime-badge {
    padding: 6px 14px;
    border-radius: 99px;
    font-size: 13px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 6px;
    color: white;
  }

  .bg-bullish {
    background: #10b981;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
  }
  .bg-bearish {
    background: #ef4444;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
  }
  .bg-global_inj {
    background: #3b82f6;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
  }
  .bg-us_inj {
    background: #8b5cf6;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
  }
  .bg-early_warning {
    background: #f59e0b;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
  }
  .bg-losing_steam {
    background: #6366f1;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
  }
  .bg-neutral {
    background: #94a3b8;
    box-shadow: 0 4px 12px rgba(148, 163, 184, 0.2);
  }

  .regime-body {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .regime-description {
    font-size: 14px;
    line-height: 1.5;
    color: var(--text-primary);
    font-weight: 500;
  }

  .regime-details {
    font-size: 12px;
    color: var(--text-muted);
    font-style: italic;
  }

  .regime-glow {
    position: absolute;
    top: -30px;
    right: -30px;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    opacity: 0.15;
    filter: blur(40px);
    transition: all 0.5s ease;
  }

  .glow-bullish {
    background: #10b981;
  }
  .glow-bearish {
    background: #ef4444;
  }
  .glow-global_inj {
    background: #3b82f6;
  }
  .glow-us_inj {
    background: #8b5cf6;
  }
  .glow-early_warning {
    background: #f59e0b;
  }
  .glow-losing_steam {
    background: #6366f1;
  }
  .glow-neutral {
    background: #94a3b8;
  }
</style>
