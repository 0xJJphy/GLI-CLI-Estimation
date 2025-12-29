<script>
    /**
     * DashboardTab.svelte
     * Main dashboard displaying GLI, Net Liquidity, CLI, Regime and Impulse Analysis.
     */
    import Chart from "../components/Chart.svelte";
    import LightweightChart from "../components/LightweightChart.svelte";
    import StatsCard from "../components/StatsCard.svelte";
    import SignalBadge from "../components/SignalBadge.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";

    // Props
    export let darkMode = false;
    export let language = "en";
    export let translations = {};
    export let dashboardData = {};
    /** @type {{ gli?: { value: number, change: number }, us_net_liq?: { value: number, change: number }, cli?: { value: number, change: number }, vix?: { value: number, change: number } } | null} */
    export let latestStats = null;

    // Chart data
    export let gliData = [];
    export let netLiqData = [];
    export let cliData = [];
    export let cliComponentData = [];
    export let regimeLCData = [];
    export let impulseData = [];
    export let impulseLayout = {};

    // Metrics
    export let gliWeights = [];
    export let usSystemMetrics = [];
    export let usSystemTotal = { delta1: 0, imp1: 0, imp3: 0, imp1y: 0 };
    export let gliSignal = "neutral";
    export let liqSignal = "neutral";
    export let currentRegime = {
        color: "grey",
        emoji: "⚖️",
        name: "Neutral",
        desc: "",
        details: "",
    };
    export let liquidityScore = 50;
    export let regimeDiagnostics = {
        liquidity_z: 0,
        credit_z: 0,
        brakes_z: 0,
        total_z: 0,
    };

    // State bindings
    export let regimeLag = 42;
    export let btcRocPeriod = 21;
    export let btcLag = 0;
    export let showComposite = false;
    export let optimalLagLabel = "";

    // Helper functions
    export let getLastDate = (key) => "N/A";
    export let getLatestValue = (arr) => arr?.[arr?.length - 1] ?? 0;

    // Local time range states
    export let gliRange = "ALL";
    export let gliShowConstantFx = false;
    export let netLiqRange = "ALL";
    export let cliRange = "ALL";
    export let cliCompRange = "ALL";
    export let impulseRange = "ALL";
</script>

<!-- Stats Cards -->
{#if latestStats}
    <div class="stats-grid">
        <StatsCard
            title={translations.stat_gli || "Global Liquidity Index"}
            value={latestStats.gli?.value}
            change={latestStats.gli?.change}
            period="7d"
            suffix="T"
            icon="🌍"
        />
        <StatsCard
            title={translations.stat_us_net || "US Net Liquidity"}
            value={latestStats.us_net_liq?.value}
            change={latestStats.us_net_liq?.change}
            period="7d"
            suffix="T"
            icon="🇺🇸"
        />
        <StatsCard
            title={translations.stat_cli || "Credit Liquidity Index"}
            value={latestStats.cli?.value}
            change={latestStats.cli?.change}
            period="7d"
            suffix="Z"
            icon="💳"
            precision={3}
        />
        <StatsCard
            title={translations.stat_vix || "VIX"}
            value={latestStats.vix?.value}
            change={latestStats.vix?.change}
            period="7d"
            icon="🌪️"
        />
    </div>
{/if}

<div class="main-charts">
    <!-- GLI Chart with Metrics Sidebar -->
    <div class="chart-card wide">
        <div class="gli-layout">
            <div class="chart-main">
                <div class="chart-header">
                    <div class="label-group">
                        <h3>
                            {translations.stat_gli || "GLI"} ({dashboardData.gli
                                ?.cb_count || 15}
                            {translations.nav_dashboard === "Dashboard"
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
                                >{translations.spot_usd || "Spot USD"}</button
                            >
                            <button
                                class="fx-btn"
                                class:active={gliShowConstantFx}
                                on:click={() => (gliShowConstantFx = true)}
                                >{translations.const_fx || "Const FX"}</button
                            >
                        </div>
                        <TimeRangeSelector
                            selectedRange={gliRange}
                            onRangeChange={(r) => (gliRange = r)}
                        />
                        <span class="last-date"
                            >{translations.last || "Last:"}
                            {getLastDate("GLI_TOTAL")}</span
                        >
                    </div>
                </div>
                <p class="chart-description">
                    {translations.gli ||
                        "Sum of 15 major central bank balance sheets in USD."}
                </p>
                <div class="chart-content">
                    <Chart {darkMode} data={gliData} />
                </div>
            </div>

            <div class="metrics-sidebar">
                <!-- Data Health Panel -->
                <div class="metrics-section data-health-section">
                    <h4 style="display: flex; align-items: center; gap: 8px;">
                        <span class="health-dot"></span>
                        {translations.data_health || "Data Health"}
                    </h4>
                    <div class="metrics-table-container">
                        <table class="metrics-table health-table">
                            <thead>
                                <tr>
                                    <th>{translations.series || "Series"}</th>
                                    <th
                                        >{translations.real_date ||
                                            "Last Date"}</th
                                    >
                                    <th>{translations.freshness || "Age"}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {#each Object.entries(dashboardData.series_metadata || {}) as [id, meta]}
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
                                                    : (meta.freshness || "?") +
                                                      "d"}
                                            </span>
                                        </td>
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                    {#if dashboardData.series_metadata?.GLI?.cb_count}
                        <div class="coverage-note">
                            {translations.active_cbs || "Active CBs"}:
                            <strong
                                >{dashboardData.series_metadata.GLI
                                    .cb_count}/15</strong
                            >
                        </div>
                    {/if}
                </div>

                <!-- GLI Composition -->
                <div class="metrics-section">
                    <h4>{translations.chart_gli_comp || "GLI Composition"}</h4>
                    <div class="metrics-table-container">
                        <table class="metrics-table">
                            <thead>
                                <tr>
                                    <th>Bank</th>
                                    <th>Wgt</th>
                                    <th>1M</th>
                                    <th
                                        title={translations.impact_1m ||
                                            "Impact 1M"}>Imp</th
                                    >
                                    <th>3M</th>
                                    <th
                                        title={translations.impact_3m ||
                                            "Impact 3M"}>Imp</th
                                    >
                                    <th>1Y</th>
                                    <th
                                        title={translations.impact_1y ||
                                            "Impact 1Y"}>Imp</th
                                    >
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
                    </div>
                    <p
                        style="font-size: 10px; color: #94a3b8; margin-top: 8px;"
                    >
                        {translations.impact_note_gli ||
                            "* Imp = contribution to GLI change."}
                    </p>
                </div>

                <!-- Flow Impulse -->
                <div class="metrics-section" style="margin-top: 24px;">
                    <h4>⚡ {translations.flow_impulse || "Flow Impulse"}</h4>
                    <p
                        class="section-note"
                        style="font-size: 11px; margin-bottom: 12px; color: var(--text-muted);"
                    >
                        {translations.flow_desc ||
                            "13-week rolling change in liquidity."}
                    </p>
                    <div class="metrics-table-container">
                        <table class="metrics-table">
                            <thead>
                                <tr>
                                    <th>{translations.economy || "Economy"}</th>
                                    <th>Impulse (13W)</th>
                                    <th>Accel</th>
                                    <th>Z-Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {#each [{ name: "Global Liquidity", key: "gli" }, { name: "Global M2", key: "m2" }] as aggregate}
                                    <tr>
                                        <td
                                            ><strong>{aggregate.name}</strong
                                            ></td
                                        >
                                        <td
                                            class="roc-val"
                                            class:positive={getLatestValue(
                                                dashboardData.flow_metrics?.[
                                                    `${aggregate.key}_impulse_13w`
                                                ],
                                            ) > 0}
                                            class:negative={getLatestValue(
                                                dashboardData.flow_metrics?.[
                                                    `${aggregate.key}_impulse_13w`
                                                ],
                                            ) < 0}
                                        >
                                            {getLatestValue(
                                                dashboardData.flow_metrics?.[
                                                    `${aggregate.key}_impulse_13w`
                                                ],
                                            )?.toFixed(2)}T
                                        </td>
                                        <td
                                            class="roc-val"
                                            class:positive={getLatestValue(
                                                dashboardData.flow_metrics?.[
                                                    `${aggregate.key}_accel`
                                                ],
                                            ) > 0}
                                            class:negative={getLatestValue(
                                                dashboardData.flow_metrics?.[
                                                    `${aggregate.key}_accel`
                                                ],
                                            ) < 0}
                                        >
                                            {getLatestValue(
                                                dashboardData.flow_metrics?.[
                                                    `${aggregate.key}_accel`
                                                ],
                                            )?.toFixed(2)}T
                                        </td>
                                        <td
                                            class="signal-cell"
                                            class:plus={getLatestValue(
                                                dashboardData.flow_metrics?.[
                                                    `${aggregate.key}_impulse_zscore`
                                                ],
                                            ) > 1}
                                            class:minus={getLatestValue(
                                                dashboardData.flow_metrics?.[
                                                    `${aggregate.key}_impulse_zscore`
                                                ],
                                            ) < -1}
                                        >
                                            {getLatestValue(
                                                dashboardData.flow_metrics?.[
                                                    `${aggregate.key}_impulse_zscore`
                                                ],
                                            )?.toFixed(2)}σ
                                        </td>
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- CB Contribution -->
                <div class="metrics-section" style="margin-top: 24px;">
                    <h4>
                        🏦 {translations.cb_contribution || "CB Contribution"}
                    </h4>
                    <div class="metrics-table-container">
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
                                    {#if getLatestValue(dashboardData.flow_metrics?.[`${cb.key}_contrib_13w`]) !== undefined}
                                        <tr>
                                            <td>{cb.name}</td>
                                            <td
                                                class="roc-val"
                                                class:positive={getLatestValue(
                                                    dashboardData
                                                        .flow_metrics?.[
                                                        `${cb.key}_contrib_13w`
                                                    ],
                                                ) > 0}
                                                class:negative={getLatestValue(
                                                    dashboardData
                                                        .flow_metrics?.[
                                                        `${cb.key}_contrib_13w`
                                                    ],
                                                ) < 0}
                                            >
                                                {getLatestValue(
                                                    dashboardData
                                                        .flow_metrics?.[
                                                        `${cb.key}_contrib_13w`
                                                    ],
                                                )?.toFixed(1)}%
                                            </td>
                                            <td
                                                class="signal-cell"
                                                class:plus={getLatestValue(
                                                    dashboardData
                                                        .flow_metrics?.[
                                                        `${cb.key}_contrib_13w`
                                                    ],
                                                ) > 20}
                                                class:minus={getLatestValue(
                                                    dashboardData
                                                        .flow_metrics?.[
                                                        `${cb.key}_contrib_13w`
                                                    ],
                                                ) < -5}
                                            >
                                                {getLatestValue(
                                                    dashboardData
                                                        .flow_metrics?.[
                                                        `${cb.key}_contrib_13w`
                                                    ],
                                                ) > 20
                                                    ? "Driver"
                                                    : getLatestValue(
                                                            dashboardData
                                                                .flow_metrics?.[
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
    </div>

    <!-- Net Liquidity Chart -->
    <div class="chart-card wide">
        <div class="gli-layout">
            <div class="chart-main">
                <div class="chart-header">
                    <div class="label-group">
                        <h3>
                            {translations.chart_us_net_liq ||
                                "US Net Liquidity"}
                        </h3>
                        <SignalBadge type={liqSignal} text={liqSignal} />
                    </div>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={netLiqRange}
                            onRangeChange={(r) => (netLiqRange = r)}
                        />
                        <span class="last-date"
                            >{translations.last_data || "Last Data:"}
                            {getLastDate("FED")}</span
                        >
                    </div>
                </div>
                <p class="chart-description">
                    {translations.net_liq || "Fed Balance Sheet - TGA - RRP"}
                </p>
                <div class="chart-content">
                    <Chart {darkMode} data={netLiqData} />
                </div>
            </div>

            <div class="metrics-sidebar">
                <div class="metrics-section">
                    <h4>
                        {translations.chart_us_comp || "US System Components"}
                    </h4>
                    <div class="metrics-table-container">
                        <table class="metrics-table">
                            <thead>
                                <tr>
                                    <th>Acc</th>
                                    <th>1M</th>
                                    <th title="Absolute change in Billions USD"
                                        >Δ$1M</th
                                    >
                                    <th
                                        title={translations.impact_us ||
                                            "Impact"}>Imp</th
                                    >
                                    <th>3M</th>
                                    <th
                                        title={translations.impact_us ||
                                            "Impact"}>Imp</th
                                    >
                                    <th>1Y</th>
                                    <th
                                        title={translations.impact_us ||
                                            "Impact"}>Imp</th
                                    >
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
                                                (item.isLiability &&
                                                    item.m1 < 0)}
                                            class:negative={(!item.isLiability &&
                                                item.m1 < 0) ||
                                                (item.isLiability &&
                                                    item.m1 > 0)}
                                            >{item.m1.toFixed(1)}%</td
                                        >
                                        <td
                                            class="roc-val"
                                            class:positive={(!item.isLiability &&
                                                item.delta1 > 0) ||
                                                (item.isLiability &&
                                                    item.delta1 < 0)}
                                            class:negative={(!item.isLiability &&
                                                item.delta1 < 0) ||
                                                (item.isLiability &&
                                                    item.delta1 > 0)}
                                            >{item.delta1 > 0
                                                ? "+"
                                                : ""}{item.delta1.toFixed(
                                                0,
                                            )}B</td
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
                                                (item.isLiability &&
                                                    item.m3 < 0)}
                                            class:negative={(!item.isLiability &&
                                                item.m3 < 0) ||
                                                (item.isLiability &&
                                                    item.m3 > 0)}
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
                                                (item.isLiability &&
                                                    item.y1 < 0)}
                                            class:negative={(!item.isLiability &&
                                                item.y1 < 0) ||
                                                (item.isLiability &&
                                                    item.y1 > 0)}
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
                                        class:positive={usSystemTotal.delta1 >
                                            0}
                                        class:negative={usSystemTotal.delta1 <
                                            0}
                                        >{usSystemTotal.delta1 > 0
                                            ? "+"
                                            : ""}{usSystemTotal.delta1.toFixed(
                                            0,
                                        )}B</td
                                    >
                                    <td
                                        class="roc-val impact-cell"
                                        class:positive={usSystemTotal.imp1 > 0}
                                        class:negative={usSystemTotal.imp1 < 0}
                                        >{usSystemTotal.imp1.toFixed(2)}%</td
                                    >
                                    <td>-</td>
                                    <td
                                        class="roc-val impact-cell"
                                        class:positive={usSystemTotal.imp3 > 0}
                                        class:negative={usSystemTotal.imp3 < 0}
                                        >{usSystemTotal.imp3.toFixed(2)}%</td
                                    >
                                    <td>-</td>
                                    <td
                                        class="roc-val impact-cell"
                                        class:positive={usSystemTotal.imp1y > 0}
                                        class:negative={usSystemTotal.imp1y < 0}
                                        >{usSystemTotal.imp1y.toFixed(2)}%</td
                                    >
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- CLI Chart -->
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
        <p class="chart-description">
            {translations.cli || "Credit conditions indicator."}
        </p>
        <div class="chart-content">
            <Chart {darkMode} data={cliData} />
        </div>
    </div>

    <!-- CLI Components -->
    <div class="chart-card wide">
        <div class="chart-header">
            <div class="label-group">
                <h3>CLI Component Contributions</h3>
            </div>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={cliCompRange}
                    onRangeChange={(r) => (cliCompRange = r)}
                />
            </div>
        </div>
        <div class="chart-content">
            <Chart {darkMode} data={cliComponentData} />
        </div>
    </div>

    <!-- Regime Panel -->
    <div class="regime-card wide">
        <div class="regime-header">
            <span class="regime-title"
                >{translations.regime_signal || "Macro Regime"}</span
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
                    max="365"
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
                    >{liquidityScore?.toFixed(0) ?? 50}</span
                >
            </div>
        </div>
        <div class="regime-body">
            <p class="regime-description">{currentRegime.desc}</p>
            <p class="regime-details">{currentRegime.details}</p>

            <div
                class="regime-formula"
                style="margin-top: 12px; padding: 10px; background: var(--card-bg-alt, rgba(0,0,0,0.15)); border-radius: 6px; font-size: 11px;"
            >
                <h4
                    style="margin: 0 0 6px 0; font-size: 12px; color: var(--text-primary);"
                >
                    {translations.regime_formula_title || "Score Formula"}
                </h4>
                <p
                    style="margin: 0 0 4px 0; color: var(--text-muted); font-family: monospace; line-height: 1.4;"
                >
                    {translations.regime_formula_desc ||
                        "Score = 50 + 15 × (Liquidity_Z + Credit_Z - Brakes_Z)"}
                </p>
                <p style="margin: 0; color: #10b981;">
                    • {translations.regime_score_bullish ||
                        "Score > 65 = Risk-ON"}
                </p>
                <p style="margin: 0 0 8px 0; color: #ef4444;">
                    • {translations.regime_score_bearish ||
                        "Score < 35 = Risk-OFF"}
                </p>

                <div
                    style="margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border-color, rgba(255,255,255,0.1));"
                >
                    <p
                        style="margin: 0 0 4px 0; font-size: 10px; color: var(--text-muted);"
                    >
                        {language === "es"
                            ? "Valores Actuales:"
                            : "Current Values:"}
                    </p>
                    <div
                        style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px;"
                    >
                        <span
                            style="color: {regimeDiagnostics.liquidity_z >= 0
                                ? '#10b981'
                                : '#ef4444'};"
                            >Liquidity: {regimeDiagnostics.liquidity_z >= 0
                                ? "+"
                                : ""}{regimeDiagnostics.liquidity_z.toFixed(
                                2,
                            )}</span
                        >
                        <span
                            style="color: {regimeDiagnostics.credit_z >= 0
                                ? '#10b981'
                                : '#ef4444'};"
                            >Credit: {regimeDiagnostics.credit_z >= 0
                                ? "+"
                                : ""}{regimeDiagnostics.credit_z.toFixed(
                                2,
                            )}</span
                        >
                        <span
                            style="color: {regimeDiagnostics.brakes_z >= 0
                                ? '#10b981'
                                : '#ef4444'};"
                            >Brakes: {regimeDiagnostics.brakes_z >= 0
                                ? "+"
                                : ""}{regimeDiagnostics.brakes_z.toFixed(
                                2,
                            )}</span
                        >
                        <span
                            style="font-weight: 600; color: {regimeDiagnostics.total_z >=
                            0
                                ? '#10b981'
                                : '#ef4444'};"
                            >Total Z: {regimeDiagnostics.total_z >= 0
                                ? "+"
                                : ""}{regimeDiagnostics.total_z.toFixed(2)} → {regimeDiagnostics.total_z >
                            0.5
                                ? "🐂"
                                : regimeDiagnostics.total_z < -0.5
                                  ? "🐻"
                                  : "⚖️"}</span
                        >
                    </div>
                </div>
            </div>
        </div>

        <div
            class="regime-chart-container"
            style="margin-top: 16px; border-top: 1px solid var(--border-color); padding-top:10px; height: 450px; display: flex; flex-direction: column;"
        >
            <p
                style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px; line-height: 1.4;"
            >
                {translations.regime_chart_desc ||
                    "BTC price with regime background coloring."}
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

    <!-- Impulse Analysis -->
    <div class="chart-card wide">
        <div class="chart-header">
            <div class="label-group">
                <h3>{translations.impulse_analysis || "Impulse Analysis"}</h3>
            </div>
            <div class="header-controls">
                <div
                    class="control-group"
                    style="display: flex; align-items: center; gap: 8px;"
                >
                    <span style="font-size: 11px; color: var(--text-muted);"
                        >{translations.period || "Period"}:</span
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
                        >{translations.lag_days || "Lag (Days)"}:</span
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
                        >{optimalLagLabel}</span
                    >
                {/if}

                <TimeRangeSelector
                    selectedRange={impulseRange}
                    onRangeChange={(r) => (impulseRange = r)}
                />
            </div>
        </div>
        <p class="chart-description">
            {translations.chart_impulse_desc ||
                "Compare BTC ROC with liquidity impulse."}
        </p>
        <div class="chart-content">
            <Chart {darkMode} data={impulseData} layout={impulseLayout} />
        </div>
    </div>
</div>
