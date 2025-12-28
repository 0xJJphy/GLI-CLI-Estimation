<script>
    /**
     * RiskModelTab.svelte
     * Displays Credit Liquidity Index (CLI) and risk metrics.
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";

    // Props
    export let darkMode = false;
    export let language = "en";
    export let translations = {};
    export let dashboardData = {};

    // Chart data
    export let cliData = [];
    export let hyZData = [];
    export let igZData = [];
    export let nfciCreditZData = [];
    export let nfciRiskZData = [];
    export let lendingZData = [];
    export let vixZData = [];
    export let tipsData = [];
    export let tipsLayout = {};
    export let repoStressData = [];

    // Last date lookup function
    export let getLastDate = (bank) => "N/A";
    export let getLatestValue = (arr) => arr?.[arr?.length - 1] ?? 0;
    export let getLatestROC = (rocs, period) =>
        rocs?.[period]?.[rocs?.[period]?.length - 1] ?? 0;

    // Time range states - managed locally
    export let cliRange = "ALL";
    export let hyRange = "ALL";
    export let igRange = "ALL";
    export let nfciRange = "ALL";
    export let lendingRange = "ALL";
    export let vixRange = "ALL";
    export let tipsRange = "ALL";
    export let repoStressRange = "ALL";

    // Credit indicators configuration
    $: creditIndicators = [
        {
            id: "hy",
            name: "HY Spread Contrast",
            data: hyZData,
            range: hyRange,
            setRange: (r) => (hyRange = r),
            bank: "HY_SPREAD",
            descKey: "hy_spread",
        },
        {
            id: "ig",
            name: "IG Spread Contrast",
            data: igZData,
            range: igRange,
            setRange: (r) => (igRange = r),
            bank: "IG_SPREAD",
            descKey: "ig_spread",
        },
        {
            id: "nfci_credit",
            name: "NFCI Credit Contrast",
            data: nfciCreditZData,
            range: nfciRange,
            setRange: (r) => (nfciRange = r),
            bank: "NFCI",
            descKey: "nfci_credit",
        },
        {
            id: "nfci_risk",
            name: "NFCI Risk Contrast",
            data: nfciRiskZData,
            range: nfciRange,
            setRange: (r) => (nfciRange = r),
            bank: "NFCI",
            descKey: "nfci_risk",
        },
        {
            id: "lending",
            name: "Lending Standards Contrast",
            data: lendingZData,
            range: lendingRange,
            setRange: (r) => (lendingRange = r),
            bank: "LENDING_STD",
            descKey: "lending",
        },
        {
            id: "vix_z",
            name: "VIX Contrast (Z-Score)",
            data: vixZData,
            range: vixRange,
            setRange: (r) => (vixRange = r),
            bank: "VIX",
            descKey: "vix",
        },
    ];
</script>

<div class="main-charts">
    <!-- Top Row: TIPS Market and CLI Aggregate -->
    <div class="stats-grid">
        <!-- TIPS / Inflation Expectations Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_inflation_exp ||
                        "Inflation Expectations (TIPS Market)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={tipsRange}
                        onRangeChange={(r) => (tipsRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.tips || "Breakeven, Real Rate, and 5Y5Y Forward."}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={tipsData} layout={tipsLayout} />
            </div>
        </div>

        <!-- CLI Aggregate Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>Credit Liquidity Index (CLI Aggregate)</h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={cliRange}
                        onRangeChange={(r) => (cliRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.cli ||
                    "Aggregates credit conditions, volatility, and lending."}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={cliData} />
            </div>
        </div>
    </div>

    <!-- Second Row: Repo Stress Chart (Wide) -->
    <div class="chart-card wide">
        <div class="gli-layout">
            <div class="chart-main">
                <div class="chart-header">
                    <h3>
                        {translations.chart_repo_stress ||
                            "Repo Market Stress (SOFR vs IORB)"}
                    </h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={repoStressRange}
                            onRangeChange={(r) => (repoStressRange = r)}
                        />
                        <span class="last-date"
                            >{translations.last_data || "Last Data:"}
                            {getLastDate("SOFR")}</span
                        >
                    </div>
                </div>
                <p class="chart-description">
                    {translations.repo_stress ||
                        "SOFR vs IORB spread indicates funding stress."}
                </p>
                <div class="chart-content">
                    <Chart {darkMode} data={repoStressData} />
                </div>
            </div>

            <div class="metrics-sidebar">
                <div class="metrics-section">
                    <h4>SOFR vs IORB</h4>
                    <div class="metrics-table-container">
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
                                    <td
                                        style="color: #f59e0b; font-weight: 600;"
                                        >SOFR</td
                                    >
                                    <td
                                        >{(
                                            getLatestValue(
                                                dashboardData.repo_stress?.sofr,
                                            ) ?? 0
                                        ).toFixed(2)}%</td
                                    >
                                    <td style="font-size: 10px;"
                                        >{language === "en"
                                            ? "Market Rate"
                                            : "Tasa Mercado"}</td
                                    >
                                </tr>
                                <tr>
                                    <td
                                        style="color: #8b5cf6; font-weight: 600;"
                                        >IORB</td
                                    >
                                    <td
                                        >{(
                                            getLatestValue(
                                                dashboardData.repo_stress?.iorb,
                                            ) ?? 0
                                        ).toFixed(2)}%</td
                                    >
                                    <td style="font-size: 10px;"
                                        >{language === "en"
                                            ? "Fed Floor"
                                            : "Piso Fed"}</td
                                    >
                                </tr>
                                <tr>
                                    <td>Spread</td>
                                    <td
                                        class:positive={getLatestValue(
                                            dashboardData.repo_stress?.sofr,
                                        ) -
                                            getLatestValue(
                                                dashboardData.repo_stress?.iorb,
                                            ) >
                                            0}
                                        class:negative={getLatestValue(
                                            dashboardData.repo_stress?.sofr,
                                        ) -
                                            getLatestValue(
                                                dashboardData.repo_stress?.iorb,
                                            ) <
                                            -0.05}
                                    >
                                        {(
                                            (getLatestValue(
                                                dashboardData.repo_stress?.sofr,
                                            ) ?? 0) -
                                            (getLatestValue(
                                                dashboardData.repo_stress?.iorb,
                                            ) ?? 0)
                                        ).toFixed(2)} bps
                                    </td>
                                    <td
                                        class="signal-cell"
                                        class:plus={getLatestValue(
                                            dashboardData.repo_stress?.sofr,
                                        ) -
                                            getLatestValue(
                                                dashboardData.repo_stress?.iorb,
                                            ) >
                                            0}
                                        class:minus={getLatestValue(
                                            dashboardData.repo_stress?.sofr,
                                        ) -
                                            getLatestValue(
                                                dashboardData.repo_stress?.iorb,
                                            ) <
                                            -0.05}
                                    >
                                        {getLatestValue(
                                            dashboardData.repo_stress?.sofr,
                                        ) >
                                        getLatestValue(
                                            dashboardData.repo_stress?.iorb,
                                        )
                                            ? "OK"
                                            : "⚠️"}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Following Rows: Individual Credit Indicators (2 per row) -->
    <div class="main-charts">
        {#each creditIndicators as item}
            <div class="chart-card">
                <div class="chart-header">
                    <h3>{item.name}</h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={item.range}
                            onRangeChange={item.setRange}
                        />
                    </div>
                </div>
                <p class="chart-description">
                    {translations[item.descKey] || ""}
                </p>
                <div class="chart-content">
                    <Chart {darkMode} data={item.data} />
                </div>
            </div>
        {/each}
    </div>

    <!-- ROC Section -->
    <div class="roc-section">
        <div class="roc-card">
            <h4>Pulsar Momentum (ROC)</h4>
            <div class="metrics-table-container">
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
                            class:plus={getLatestROC(
                                dashboardData.gli?.rocs,
                                "1M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.gli?.rocs,
                                "1M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.gli?.rocs,
                                "1M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.gli?.rocs,
                                "3M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.gli?.rocs,
                                "3M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.gli?.rocs,
                                "3M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.gli?.rocs,
                                "6M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.gli?.rocs,
                                "6M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.gli?.rocs,
                                "6M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.gli?.rocs,
                                "1Y",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.gli?.rocs,
                                "1Y",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.gli?.rocs,
                                "1Y",
                            ).toFixed(2)}%
                        </div>
                    </div>
                    <div class="roc-row">
                        <div class="roc-col label">US Net Liq</div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "1M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "1M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "1M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "3M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "3M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "3M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "6M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "6M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "6M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "1Y",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "1Y",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                "1Y",
                            ).toFixed(2)}%
                        </div>
                    </div>
                    <div class="roc-row">
                        <div class="roc-col label">Fed Assets</div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "1M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "1M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "1M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "3M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "3M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "3M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "6M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "6M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "6M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "1Y",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "1Y",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                "1Y",
                            ).toFixed(2)}%
                        </div>
                    </div>
                    <div class="roc-row">
                        <div class="roc-col label">PBoC Assets</div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "1M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "1M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "1M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "3M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "3M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "3M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "6M",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "6M",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "6M",
                            ).toFixed(2)}%
                        </div>
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "1Y",
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "1Y",
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                "1Y",
                            ).toFixed(2)}%
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
