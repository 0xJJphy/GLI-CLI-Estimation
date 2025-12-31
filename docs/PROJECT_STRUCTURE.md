# GLI-CLI Dashboard - Project Structure & Documentation

This document provides a comprehensive overview of all files in the project and their functions.

---

## Project Root

| File | Purpose |
|------|---------|
| `README.md` | Project overview, setup instructions, and features documentation |
| `LICENSE` | Project license information |
| `.gitignore` | Git ignore patterns |

---

## Backend (`/backend`)

The backend handles data processing and generation for the dashboard.

### `/backend/data_pipeline.py`

Main data processing pipeline that fetches and transforms financial data.

### `/backend/train_regime_offset.py`

Trains the regime detection model and calculates optimal offset parameters.

---

## Frontend (`/frontend`)

Svelte-based frontend application for the liquidity dashboard.

### Configuration Files

| File | Purpose |
|------|---------|
| `vite.config.js` | Vite build configuration with code splitting for plotly.js and lightweight-charts |
| `package.json` | NPM dependencies and scripts |
| `svelte.config.js` | Svelte compiler configuration |

---

## Source Files (`/frontend/src`)

### Entry Points

| File | Purpose |
|------|---------|
| `main.js` | Application entry point, mounts App.svelte |
| `App.svelte` | Main application component with routing, layout, and core data processing |
| `app.css` | Global CSS variables, theme system, and common styles |

---

## Stores (`/frontend/src/stores`)

### `dataStore.js`

Svelte stores for managing application state and data fetching.

| Export | Type | Description |
|--------|------|-------------|
| `dashboardData` | `writable` | Main store containing all dashboard data (GLI, M2, CLI, BTC, etc.) |
| `isLoading` | `writable` | Loading state indicator |
| `error` | `writable` | Error state for data fetching |
| `selectedSource` | `writable` | Data source selector ('tv' or 'fred') |
| `latestStats` | `derived` | Computed latest values and changes for key metrics |
| `fetchData()` | `function` | Fetches dashboard data from JSON file and populates stores |

### `settingsStore.js`

Application settings and translations.

| Export | Type | Description |
|--------|------|-------------|
| `darkMode` | `writable` | Dark/light theme toggle |
| `language` | `writable` | Current language ('en' or 'es') |
| `currentTranslations` | `derived` | Translation strings for current language |
| `toggleDarkMode()` | `function` | Toggles dark mode and saves to localStorage |
| `toggleLanguage()` | `function` | Toggles language and saves to localStorage |
| `initSettings()` | `function` | Initializes settings from localStorage |
| `t(key)` | `function` | Translation helper function |

---

## Utility Functions (`/frontend/src/lib/utils`)

### `helpers.js`

Shared helper functions for data processing and chart formatting.

#### Data Access Helpers

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getLastDate(dashboardData, seriesKey)` | `dashboardData: Object`, `seriesKey: string` | `string` | Gets the last available date for a series from `dashboardData.last_dates` |
| `getLatestValue(arr)` | `arr: Array` | `number` | Returns the last element of an array |
| `getChange(arr, period)` | `arr: Array`, `period: number = 7` | `number` | Calculates percentage change over N periods |

#### Time Range Helpers

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getCutoffDate(range)` | `range: string` | `Date\|null` | Converts range string ("1M", "3M", etc.) to cutoff Date |
| `getFilteredIndices(dates, range)` | `dates: string[]`, `range: string` | `number[]` | Returns array indices that fall within the time range |

#### Chart Formatting Helpers

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `filterPlotlyData(traceArray, dates, range)` | `traceArray: Array`, `dates: string[]`, `range: string` | `Array` | Filters Plotly trace data based on time range, auto-trims leading zeros |
| `formatTV(dates, values)` | `dates: string[]`, `values: number[]` | `Array<{time, value}>` | Formats data for TradingView LightweightCharts |
| `formatLC(dates, values, range, name, color, type)` | `dates: string[]`, `values: number[]`, `range: string`, `name: string`, `color: string`, `type: string` | `Array` | Creates LightweightChart series config with time range filtering |

#### Statistical Helpers

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `calculateCorrelation(xArray, yArray)` | `xArray: number[]`, `yArray: number[]` | `number` | Calculates Pearson correlation coefficient between two arrays |
| `findOptimalLag(dates, signalValues, btcRocValues, minLag, maxLag)` | Multiple | `{lag, corr}` | Finds optimal lag for signal vs BTC ROC correlation |
| `calculateZScore(values)` | `values: number[]` | `number[]` | Calculates Z-score for an array of values |
| `calculateBtcRoc(prices, dates, period, lag)` | Multiple | `Array<{x, y}>` | Calculates BTC Rate of Change |
| `calculateHistoricalRegimes(dates, gli, netliq)` | Multiple | `Array` | Generates Plotly shapes for regime background coloring |

---

## Components (`/frontend/src/lib/components`)

### `Chart.svelte`

Plotly.js wrapper component for rendering charts.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `Array` | `[]` | Plotly trace data array |
| `darkMode` | `boolean` | `false` | Enables dark theme styling |
| `layout` | `Object` | `{}` | Custom Plotly layout options |
| `shapes` | `Array` | `[]` | Plotly shapes for annotations/regime backgrounds |

### `LightweightChart.svelte`

TradingView LightweightCharts wrapper for financial visualizations.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `Array` | `[]` | Series config array: `[{name, type, color, data: [{time, value}...]}]` |
| `title` | `string` | `""` | Optional chart title |
| `logScale` | `boolean` | `false` | Enables logarithmic price scale |
| `darkMode` | `boolean` | `false` | Enables dark theme styling |

### `TimeRangeSelector.svelte`

Time range button group component.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `selectedRange` | `string` | `"ALL"` | Currently selected range |
| `onRangeChange` | `function` | - | Callback when range changes |
| `ranges` | `Array` | `["1M","3M","6M","1Y","3Y","5Y","ALL"]` | Available range options |

### `StatsCard.svelte`

Dashboard metric card with value and change indicator.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | - | Card title |
| `value` | `number` | - | Main metric value |
| `change` | `number` | - | Percentage change |
| `format` | `string` | `"number"` | Value format: "number", "currency", "percent" |
| `darkMode` | `boolean` | `false` | Enables dark theme styling |

### `SignalBadge.svelte`

Signal/status indicator badge.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `signal` | `string` | - | Signal type: "bullish", "bearish", "neutral" |
| `label` | `string` | - | Badge label text |

### `StressPanel.svelte`

Stress analysis summary panel with multiple stress indicators.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `stressData` | `Object` | - | Stress analysis data object |
| `darkMode` | `boolean` | `false` | Enables dark theme styling |
| `translations` | `Object` | `{}` | Translation strings |

### `ChartAnalysisBadge.svelte`

Chart analysis badge with AI-generated insights.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `analysis` | `Object` | - | Analysis data with title and description |
| `darkMode` | `boolean` | `false` | Enables dark theme styling |

---

## Tab Components (`/frontend/src/lib/tabs`)

Each tab component is self-contained with its own state management and chart processing.

### `DashboardTab.svelte`

Main dashboard overview with GLI, Net Liquidity, CLI, and regime indicators.

| Prop | Type | Description |
|------|------|-------------|
| `darkMode` | `boolean` | Theme mode |
| `language` | `string` | Current language |
| `translations` | `Object` | Translation strings |
| `dashboardData` | `Object` | Full dashboard data |
| Multiple chart props | Various | GLI data, regime data, weights, etc. |

### `GlobalFlowsCbTab.svelte`

Central bank balance sheet charts (Fed, ECB, BoJ, BoE, PBoC, etc.) with CB Breadth and Concentration.

| Prop | Type | Description |
|------|------|-------------|
| `darkMode` | `boolean` | Theme mode |
| `language` | `string` | Current language |
| `translations` | `Object` | Translation strings |
| `dashboardData` | `Object` | Dashboard data containing GLI and macro_regime |

### `GlobalM2Tab.svelte`

Global M2 money supply charts with aggregate and per-country views.

| Prop | Type | Description |
|------|------|-------------|
| `darkMode` | `boolean` | Theme mode |
| `translations` | `Object` | Translation strings |
| `dashboardData` | `Object` | Dashboard data containing M2 data |

### `UsSystemTab.svelte`

US liquidity system charts (Fed, RRP, TGA, Net Liquidity).

| Prop | Type | Description |
|------|------|-------------|
| `darkMode` | `boolean` | Theme mode |
| `language` | `string` | Current language |
| `translations` | `Object` | Translation strings |
| `dashboardData` | `Object` | Dashboard data containing US system data |

### `RiskModelTab.svelte`

Comprehensive risk model with credit spreads, volatility indices, yield curves, and TIPS.

| Prop | Type | Description |
|------|------|-------------|
| `darkMode` | `boolean` | Theme mode |
| `language` | `string` | Current language |
| `translations` | `Object` | Translation strings |
| `dashboardData` | `Object` | Dashboard data containing risk metrics |

### `BtcAnalysisTab.svelte`

Bitcoin analysis with fair value models and correlation analysis.

| Prop | Type | Description |
|------|------|-------------|
| `darkMode` | `boolean` | Theme mode |
| `translations` | `Object` | Translation strings |
| `dashboardData` | `Object` | Dashboard data containing BTC data |

### `BtcQuantV2Tab.svelte`

Advanced Bitcoin quantitative analysis (v2 model).

| Prop | Type | Description |
|------|------|-------------|
| `darkMode` | `boolean` | Theme mode |
| `translations` | `Object` | Translation strings |
| `dashboardData` | `Object` | Dashboard data containing BTC data |
| `quantV2ChartData` | `Array` | Quant model chart data |
| `quantV2RebalancedData` | `Array` | Rebalanced strategy data |
| `quantV2ReturnsData` | `Array` | Returns comparison data |
| `getLatestValue` | `function` | Helper function for latest values |

### `FedForecastsTab.svelte`

Federal Reserve economic forecasts and indicators.

| Prop | Type | Description |
|------|------|-------------|
| `darkMode` | `boolean` | Theme mode |
| `translations` | `Object` | Translation strings |
| `dashboardData` | `Object` | Dashboard data containing Fed forecast data |

### `index.js`

Barrel export file for all tab components.

---

## Data Flow Architecture

```
┌─────────────────┐
│  dashboard_data │
│   _tv.json      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   dataStore.js  │
│ dashboardData   │──────────────────────────┐
│ latestStats     │                          │
│ fetchData()     │                          │
└────────┬────────┘                          │
         │                                   │
         ▼                                   ▼
┌─────────────────┐    ┌─────────────────────────────┐
│    App.svelte   │    │    Tab Components           │
│ - Layout        │───▶│ - DashboardTab.svelte       │
│ - Tab routing   │    │ - GlobalFlowsCbTab.svelte   │
│ - Data passing  │    │ - GlobalM2Tab.svelte        │
└─────────────────┘    │ - RiskModelTab.svelte       │
                       │ - etc.                      │
                       └─────────────────────────────┘
                                   │
                                   ▼
                       ┌───────────────────────────┐
                       │    Components             │
                       │ - Chart.svelte            │
                       │ - LightweightChart.svelte │
                       │ - TimeRangeSelector       │
                       │ - StatsCard.svelte        │
                       └───────────────────────────┘
```

---

## Styling Architecture

| File | Purpose |
|------|---------|
| `app.css` | Global CSS variables, theme tokens, scrollbar styles, utility classes |
| `App.svelte <style>` | Layout styles (sidebar, main content, grid) |
| Component `<style>` | Component-scoped styles |

### CSS Variables

- `--bg-primary`, `--bg-secondary`, `--bg-tertiary`: Background colors
- `--text-primary`, `--text-secondary`, `--text-muted`: Text colors
- `--accent-primary`, `--accent-secondary`: Brand/accent colors
- `--positive-color`, `--negative-color`: Signal colors
- `--border-color`, `--card-shadow`: UI element styles

---

## Build Configuration (`vite.config.js`)

```javascript
{
  plugins: [svelte()],
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          'plotly': ['plotly.js-dist-min'],      // ~4.8 MB (cached)
          'lightweight-charts': ['lightweight-charts'], // ~165 KB
          'vendor': ['svelte']                   // ~41 KB
        }
      }
    }
  }
}
```

**Result:** App code bundle is ~293 KB (95% reduction from monolithic bundle)
