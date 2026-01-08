<script>
    import { onMount } from "svelte";

    let {
        options = [],
        value = $bindable(),
        onSelect = () => {},
        darkMode = true,
        small = false,
        placeholder = "Select...",
        labelPrefix = "",
    } = $props();

    let isOpen = $state(false);
    let dropdownElement = $state();

    const selectedOption = $derived(options.find((opt) => opt.value === value));

    function toggle() {
        isOpen = !isOpen;
    }

    function handleSelect(option) {
        value = option.value;
        onSelect(option.value);
        isOpen = false;
    }

    function handleClickOutside(event) {
        if (dropdownElement && !dropdownElement.contains(event.target)) {
            isOpen = false;
        }
    }

    onMount(() => {
        window.addEventListener("click", handleClickOutside);
        return () => window.removeEventListener("click", handleClickOutside);
    });
</script>

<div class="custom-dropdown" class:active={isOpen} bind:this={dropdownElement}>
    <button
        class="dropdown-trigger"
        class:small
        class:light={!darkMode}
        onclick={toggle}
        type="button"
    >
        <span class="trigger-text">
            {#if labelPrefix}<span class="prefix">{labelPrefix}:</span>{/if}
            {selectedOption ? selectedOption.label : placeholder}
        </span>
        <span class="arrow">▾</span>
    </button>

    {#if isOpen}
        <div class="dropdown-menu" class:light={!darkMode}>
            {#each options as option}
                <button
                    class="dropdown-item"
                    class:selected={value === option.value}
                    onclick={() => handleSelect(option)}
                    type="button"
                >
                    {option.label}
                    {#if value === option.value}
                        <span class="check">✓</span>
                    {/if}
                </button>
            {/each}
        </div>
    {/if}
</div>

<style>
    .custom-dropdown {
        position: relative;
        display: inline-block;
        z-index: 50;
    }

    .dropdown-trigger {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        padding: 8px 14px;
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        min-width: 140px;
        justify-content: space-between;
        outline: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .dropdown-trigger.small {
        padding: 5px 12px;
        font-size: 0.8rem;
        min-width: 110px;
    }

    .dropdown-trigger:hover {
        background: rgba(15, 23, 42, 0.6);
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.1);
        transform: translateY(-1px);
    }

    .dropdown-trigger.light {
        background: white;
        border-color: rgba(0, 0, 0, 0.08);
        color: #1e293b;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .dropdown-trigger.light:hover {
        background: #f8fafc;
        border-color: #cbd5e1;
    }

    .prefix {
        opacity: 0.6;
        margin-right: 4px;
        font-weight: 400;
    }

    .dropdown-menu {
        position: absolute;
        top: calc(100% + 8px);
        right: 0;
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 6px;
        min-width: 180px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        display: flex;
        flex-direction: column;
        gap: 4px;
        backdrop-filter: blur(16px);
        animation: slideDown 0.2s ease-out;
    }

    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-5px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .dropdown-menu.light {
        background: rgba(255, 255, 255, 0.98);
        border-color: rgba(0, 0, 0, 0.1);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    .dropdown-item {
        background: transparent;
        border: none;
        color: #94a3b8;
        padding: 10px 12px;
        border-radius: 8px;
        font-size: 0.85rem;
        text-align: left;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }

    .dropdown-item:hover {
        background: rgba(99, 102, 241, 0.1);
        color: white;
    }

    .dropdown-item.selected {
        background: rgba(99, 102, 241, 0.15);
        color: #818cf8;
        font-weight: 700;
    }

    .dropdown-menu.light .dropdown-item {
        color: #64748b;
    }

    .dropdown-menu.light .dropdown-item:hover {
        background: #f1f5f9;
        color: #4f46e5;
    }

    .dropdown-menu.light .dropdown-item.selected {
        background: rgba(99, 102, 241, 0.08);
        color: #4f46e5;
    }

    .check {
        font-size: 0.9rem;
        font-weight: bold;
    }

    .arrow {
        font-size: 0.75rem;
        transition: transform 0.3s;
        opacity: 0.7;
    }

    .active .arrow {
        transform: rotate(180deg);
        color: #818cf8;
    }
</style>
