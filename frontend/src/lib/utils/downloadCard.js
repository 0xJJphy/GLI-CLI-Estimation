/**
 * downloadCard.js
 * Utility to capture an entire card container as a PNG image using html2canvas.
 */
import html2canvas from 'html2canvas';

/**
 * Captures a DOM element and triggers a PNG download.
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
        // Detect current theme from document body class or data attribute
        const isDarkMode = document.documentElement.classList.contains('dark') ||
            document.body.classList.contains('dark') ||
            document.documentElement.getAttribute('data-theme') === 'dark' ||
            window.matchMedia('(prefers-color-scheme: dark)').matches;

        const backgroundColor = isDarkMode ? '#050505' : '#ffffff';

        const canvas = await html2canvas(element, {
            backgroundColor: backgroundColor,
            scale: 2, // Higher resolution for better quality
            useCORS: true, // Allow cross-origin images
            logging: false,
            ...options,
        });

        // Convert canvas to blob and trigger download
        canvas.toBlob((blob) => {
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
