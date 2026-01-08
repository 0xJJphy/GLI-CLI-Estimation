/**
 * downloadCard.js
 * Utility to capture an entire card container as a PNG image using html2canvas.
 * Enhanced to properly capture LightweightCharts and Plotly charts with watermarks.
 */
import html2canvas from 'html2canvas';
import Plotly from 'plotly.js-dist-min';

/**
 * Captures a DOM element and triggers a PNG download.
 * Handles WebGL canvas elements (LightweightCharts) and Plotly SVG charts by compositing them manually.
 * @param {HTMLElement} element - The card container element to capture
 * @param {string} filename - Filename for the downloaded image (without extension)
 * @param {Object} options - Optional html2canvas options
 */
export async function downloadCardAsImage(element, filename = 'chart_card', options = {}) {
    if (!element) {
        console.error('[downloadCard] No element provided');
        return;
    }

    try {
        // Detect current theme
        const isDarkMode = document.documentElement.classList.contains('dark') ||
            document.body.classList.contains('dark') ||
            document.documentElement.getAttribute('data-theme') === 'dark' ||
            window.matchMedia('(prefers-color-scheme: dark)').matches;

        const backgroundColor = isDarkMode ? '#050505' : '#ffffff';
        const scale = options.scale || 2;
        const parentRect = element.getBoundingClientRect();

        // ===== CAPTURE CANVAS ELEMENTS (LightweightCharts) =====
        const canvasElements = element.querySelectorAll('canvas');
        const canvasData = [];

        for (const canvas of canvasElements) {
            try {
                const rect = canvas.getBoundingClientRect();
                const relX = rect.left - parentRect.left;
                const relY = rect.top - parentRect.top;

                let dataURL = null;
                try {
                    dataURL = canvas.toDataURL('image/png');
                    if (dataURL && dataURL.length > 100) {
                        canvasData.push({
                            dataURL,
                            x: relX * scale,
                            y: relY * scale,
                            width: rect.width * scale,
                            height: rect.height * scale,
                        });
                    }
                } catch (e) {
                    console.warn('[downloadCard] Could not capture canvas:', e.message);
                }
            } catch (e) {
                console.warn('[downloadCard] Error processing canvas:', e);
            }
        }

        // ===== CAPTURE PLOTLY CHARTS (SVG) =====
        const plotlyContainers = element.querySelectorAll('.js-plotly-plot');
        const plotlyData = [];

        for (const plotlyEl of plotlyContainers) {
            try {
                const rect = plotlyEl.getBoundingClientRect();
                const relX = rect.left - parentRect.left;
                const relY = rect.top - parentRect.top;

                // Use Plotly's native toImage to capture the chart with annotations/watermarks
                const dataURL = await Plotly.toImage(/** @type {HTMLElement} */(plotlyEl), {
                    format: 'png',
                    width: rect.width * scale,
                    height: rect.height * scale,
                    scale: 1,
                });

                if (dataURL) {
                    plotlyData.push({
                        dataURL,
                        x: relX * scale,
                        y: relY * scale,
                        width: rect.width * scale,
                        height: rect.height * scale,
                    });
                }
            } catch (e) {
                console.warn('[downloadCard] Could not capture Plotly chart:', e.message);
            }
        }

        // ===== CAPTURE REST WITH HTML2CANVAS =====
        const html2canvasResult = await html2canvas(element, {
            backgroundColor: backgroundColor,
            scale: scale,
            useCORS: true,
            logging: false,
            // Ignore charts since we capture them separately
            ignoreElements: (el) => {
                const tagName = el.tagName?.toLowerCase();
                return tagName === 'canvas' || el.classList?.contains('js-plotly-plot');
            },
            ...options,
        });

        // ===== COMPOSITE EVERYTHING =====
        const finalCanvas = document.createElement('canvas');
        finalCanvas.width = html2canvasResult.width;
        finalCanvas.height = html2canvasResult.height;
        const ctx = finalCanvas.getContext('2d');

        // Draw html2canvas result first (background with headers, controls, etc)
        ctx.drawImage(html2canvasResult, 0, 0);

        // Helper to draw image from dataURL
        const drawImage = (data) => new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                ctx.drawImage(img, data.x, data.y, data.width, data.height);
                resolve();
            };
            img.onerror = () => {
                console.warn('[downloadCard] Failed to load image');
                resolve();
            };
            img.src = data.dataURL;
        });

        // Overlay canvas elements (LightweightCharts)
        for (const data of canvasData) {
            await drawImage(data);
        }

        // Overlay Plotly charts
        for (const data of plotlyData) {
            await drawImage(data);
        }

        // ===== DOWNLOAD =====
        finalCanvas.toBlob((blob) => {
            if (!blob) {
                console.error('[downloadCard] Failed to create blob');
                return;
            }

            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${filename}_${new Date().toISOString().split('T')[0]}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }, 'image/png');
    } catch (error) {
        console.error('[downloadCard] Error capturing element:', error);
    }
}
