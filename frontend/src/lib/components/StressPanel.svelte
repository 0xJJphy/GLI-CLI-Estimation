<script>
    export let stressAnalysis = {};
    export let darkMode = false;
    export let translations = {};

    $: globalStress = stressAnalysis?.global_stress || {};
    $: inflationStress = stressAnalysis?.inflation_stress || {};
    $: liquidityStress = stressAnalysis?.liquidity_stress || {};
    $: creditStress = stressAnalysis?.credit_stress || {};
    $: volatilityStress = stressAnalysis?.volatility_stress || {};
    $: assessment = stressAnalysis?.overall_assessment || {};

    function getStressBarWidth(score, maxScore) {
        return maxScore > 0 ? (score / maxScore) * 100 : 0;
    }

    function getLevelColor(level) {
        const colors = {
            LOW: "#16a34a",
            MODERATE: "#ca8a04",
            HIGH: "#ea580c",
            CRITICAL: "#dc2626",
        };
        return colors[level] || "#6b7280";
    }

    // Translate the stress level
    function getTranslatedLevel(level) {
        if (!level) return translations.status_neutral || "N/A";
        const key = `stress_${level.toLowerCase()}`;
        return translations[key] || level;
    }
</script>

<div class="stress-panel" class:dark={darkMode}>
    <!-- Header with Global Score -->
    <div class="stress-header">
        <div class="stress-title">
            <span class="stress-icon">📊</span>
            {translations.stress_panel_title || "Market Stress Dashboard"}
        </div>
        <div
            class="global-score"
            style="background-color: {globalStress.color}20; border-color: {globalStress.color ||
                '#6b7280'}"
        >
            <span class="score-label"
                >{translations.stress_global || "Global Stress Level"}</span
            >
            <span
                class="score-value"
                style="color: {globalStress.color || '#6b7280'}"
            >
                {globalStress.percentage || 0}%
            </span>
            <span
                class="score-level"
                style="background-color: {globalStress.color || '#6b7280'}"
            >
                {getTranslatedLevel(globalStress.level)}
            </span>
        </div>
    </div>

    <!-- Assessment Text -->
    <div
        class="assessment-text"
        style="border-left-color: {globalStress.color || '#6b7280'}"
    >
        {globalStress.assessment ||
            translations.loading_analysis ||
            "Loading analysis..."}
    </div>

    <!-- Stress Bars -->
    <div class="stress-bars">
        <!-- Inflation -->
        <div class="stress-bar-item">
            <div class="bar-header">
                <span class="bar-icon">📈</span>
                <span class="bar-label"
                    >{translations.stress_inflation || "Inflation Stress"}</span
                >
                <span
                    class="bar-score"
                    style="color: {getLevelColor(inflationStress.level)}"
                >
                    {inflationStress.score || 0}/{inflationStress.max_score ||
                        7}
                </span>
            </div>
            <div class="bar-track">
                <div
                    class="bar-fill"
                    style="width: {getStressBarWidth(
                        inflationStress.score || 0,
                        inflationStress.max_score || 7,
                    )}%;
                            background-color: {getLevelColor(
                        inflationStress.level,
                    )}"
                ></div>
            </div>
        </div>

        <!-- Liquidity -->
        <div class="stress-bar-item">
            <div class="bar-header">
                <span class="bar-icon">💧</span>
                <span class="bar-label"
                    >{translations.stress_liquidity || "Liquidity Stress"}</span
                >
                <span
                    class="bar-score"
                    style="color: {getLevelColor(liquidityStress.level)}"
                >
                    {liquidityStress.score || 0}/{liquidityStress.max_score ||
                        7}
                </span>
            </div>
            <div class="bar-track">
                <div
                    class="bar-fill"
                    style="width: {getStressBarWidth(
                        liquidityStress.score || 0,
                        liquidityStress.max_score || 7,
                    )}%;
                            background-color: {getLevelColor(
                        liquidityStress.level,
                    )}"
                ></div>
            </div>
        </div>

        <!-- Credit -->
        <div class="stress-bar-item">
            <div class="bar-header">
                <span class="bar-icon">💳</span>
                <span class="bar-label"
                    >{translations.stress_credit || "Credit Stress"}</span
                >
                <span
                    class="bar-score"
                    style="color: {getLevelColor(creditStress.level)}"
                >
                    {creditStress.score || 0}/{creditStress.max_score || 7}
                </span>
            </div>
            <div class="bar-track">
                <div
                    class="bar-fill"
                    style="width: {getStressBarWidth(
                        creditStress.score || 0,
                        creditStress.max_score || 7,
                    )}%;
                            background-color: {getLevelColor(
                        creditStress.level,
                    )}"
                ></div>
            </div>
        </div>

        <!-- Volatility -->
        <div class="stress-bar-item">
            <div class="bar-header">
                <span class="bar-icon">⚡</span>
                <span class="bar-label"
                    >{translations.stress_volatility ||
                        "Volatility Stress"}</span
                >
                <span
                    class="bar-score"
                    style="color: {getLevelColor(volatilityStress.level)}"
                >
                    {volatilityStress.score || 0}/{volatilityStress.max_score ||
                        4}
                </span>
            </div>
            <div class="bar-track">
                <div
                    class="bar-fill"
                    style="width: {getStressBarWidth(
                        volatilityStress.score || 0,
                        volatilityStress.max_score || 4,
                    )}%;
                            background-color: {getLevelColor(
                        volatilityStress.level,
                    )}"
                ></div>
            </div>
        </div>
    </div>

    <!-- Key Points -->
    <div class="key-points">
        <div class="risks-section">
            <h4>⚠️ {translations.key_risks || "Key Risks"}</h4>
            <ul>
                {#each assessment.key_risks || [translations.no_data || "No data"] as risk}
                    <li>{risk}</li>
                {/each}
            </ul>
        </div>
        <div class="positives-section">
            <h4>✅ {translations.key_positives || "Key Positives"}</h4>
            <ul>
                {#each assessment.key_positives || [translations.no_data || "No data"] as positive}
                    <li>{positive}</li>
                {/each}
            </ul>
        </div>
    </div>

    <!-- Recommendation -->
    <div
        class="recommendation"
        style="border-left-color: {globalStress.color || '#6b7280'}"
    >
        <span class="rec-label"
            >💡 {translations.recommendation || "Recommendation"}:</span
        >
        <span class="rec-text"
            >{assessment.recommendation ||
                translations.loading ||
                "Loading..."}</span
        >
    </div>
</div>

<style>
    .stress-panel {
        background: var(--bg-secondary, #1e1e2e);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid var(--border-color, #333);
    }

    .stress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        flex-wrap: wrap;
        gap: 12px;
    }

    .stress-title {
        font-size: 18px;
        font-weight: 700;
        color: var(--text-primary, #fff);
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .stress-icon {
        font-size: 24px;
    }

    .global-score {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 16px;
        border-radius: 8px;
        border: 2px solid;
    }

    .score-label {
        font-size: 12px;
        font-weight: 500;
        color: var(--text-secondary, #aaa);
        text-transform: uppercase;
    }

    .score-value {
        font-size: 28px;
        font-weight: 800;
        font-family: "Monaco", "Consolas", monospace;
    }

    .score-level {
        font-size: 11px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 4px;
        color: white;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .assessment-text {
        font-size: 14px;
        line-height: 1.5;
        color: var(--text-primary, #fff);
        padding: 12px 16px;
        background: var(--bg-tertiary, #2a2a3e);
        border-radius: 8px;
        border-left: 4px solid;
        margin-bottom: 20px;
    }

    .stress-bars {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin-bottom: 20px;
    }

    .stress-bar-item {
        background: var(--bg-tertiary, #2a2a3e);
        padding: 12px;
        border-radius: 8px;
    }

    .bar-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }

    .bar-icon {
        font-size: 16px;
    }

    .bar-label {
        flex: 1;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary, #fff);
    }

    .bar-score {
        font-size: 13px;
        font-weight: 700;
        font-family: "Monaco", monospace;
    }

    .bar-track {
        height: 8px;
        background: var(--bg-primary, #1a1a2e);
        border-radius: 4px;
        overflow: hidden;
    }

    .bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease-out;
    }

    .key-points {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 16px;
    }

    .risks-section,
    .positives-section {
        background: var(--bg-tertiary, #2a2a3e);
        padding: 12px;
        border-radius: 8px;
    }

    .key-points h4 {
        font-size: 13px;
        font-weight: 600;
        margin: 0 0 8px 0;
        color: var(--text-primary, #fff);
    }

    .key-points ul {
        margin: 0;
        padding-left: 16px;
        font-size: 12px;
        color: var(--text-secondary, #aaa);
    }

    .key-points li {
        margin-bottom: 4px;
        line-height: 1.4;
    }

    .recommendation {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        background: var(--bg-tertiary, #2a2a3e);
        border-radius: 8px;
        border-left: 4px solid;
    }

    .rec-label {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-muted, #888);
    }

    .rec-text {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-primary, #fff);
    }

    @media (max-width: 768px) {
        .stress-bars {
            grid-template-columns: 1fr;
        }
        .key-points {
            grid-template-columns: 1fr;
        }
        .global-score {
            width: 100%;
            justify-content: center;
        }
    }
</style>
