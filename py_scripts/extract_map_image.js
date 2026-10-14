const { chromium } = require("playwright");

let browser;
let page;

async function initialize() {
    browser = await chromium.launch({ headless: true });
    page = await browser.newPage({
        viewport: { width: 1365, height: 900 }
    });
}

async function extractImage(mapUrl) {
    try {
        await page.goto(mapUrl, {
            waitUntil: "domcontentloaded",
            timeout: 60000
        });

        // Wait for Google Maps to render its content
        await page.waitForTimeout(5000);

        const imageUrl = await page.evaluate(() => {
            const images = Array.from(document.images);

            const image = images.find(img => {
                const src = img.currentSrc || img.src;
                const rect = img.getBoundingClientRect();

                return (
                    src &&
                    src.startsWith("https://") &&
                    (
                        src.includes("googleusercontent.com") ||
                        src.includes("ggpht.com")
                    ) &&
                    rect.width > 100 &&
                    rect.height > 100 &&
                    rect.bottom > 0 &&
                    rect.right > 0 &&
                    rect.top < window.innerHeight &&
                    rect.left < window.innerWidth
                );
            });

            return image
                ? (image.currentSrc || image.src)
                : null;
        });

        return imageUrl;

    } catch (error) {
        console.error(
            `Image extraction failed for ${mapUrl}: ${error.message}`
        );

        return null;
    }
}

async function main() {
    const urls = JSON.parse(process.argv[2] || "[]");

    await initialize();

    try {
        const results = {};

        for (const url of urls) {
            if (!results[url]) {
                results[url] = await extractImage(url);
            }
        }

        // Send JSON results to Python
        console.log("IMAGE_RESULTS:" + JSON.stringify(results));

    } finally {
        await browser.close();
    }
}

main().catch(error => {
    console.error(error);
    process.exit(1);
});