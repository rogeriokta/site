class Viewer {
    constructor() {
        this.currentTab = 'original';
        this.currentZoom = { original: 1, processed: 1 };
        this.isDragging = false;

        this.initTabs();
        this.initSlider();
        this.initZoomClicks();
    }

    initTabs() {
        document.querySelectorAll('.viewer-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
    }

    switchTab(tabName) {
        this.currentTab = tabName;
        document.querySelectorAll('.viewer-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        document.getElementById('viewer-original').style.display = tabName === 'original' ? 'block' : 'none';
        document.getElementById('viewer-processed').style.display = tabName === 'processed' ? 'block' : 'none';
        document.getElementById('viewer-comparison').style.display = tabName === 'comparison' ? 'block' : 'none';
        document.getElementById('viewer-result').style.display = tabName === 'result' ? 'block' : 'none';
    }

    showOriginal(url) {
        const img = document.getElementById('img-original');
        const placeholder = document.getElementById('placeholder-original');
        img.src = url;
        img.style.display = 'block';
        placeholder.style.display = 'none';
    }

    showProcessed(url) {
        const img = document.getElementById('img-processed');
        const placeholder = document.getElementById('placeholder-processed');
        img.src = url;
        img.style.display = 'block';
        placeholder.style.display = 'none';

        const compImg = document.getElementById('img-comparison-processed');
        if (compImg) compImg.src = url;
    }

    showComparison(originalUrl, processedUrl) {
        const imgOrig = document.getElementById('img-comparison-original');
        const imgProc = document.getElementById('img-comparison-processed');
        if (originalUrl) imgOrig.src = originalUrl;
        if (processedUrl) imgProc.src = processedUrl;
    }

    clear() {
        document.getElementById('img-original').style.display = 'none';
        document.getElementById('placeholder-original').style.display = 'block';
        document.getElementById('img-processed').style.display = 'none';
        document.getElementById('placeholder-processed').style.display = 'block';
        this.switchTab('original');
    }

    zoom(type, factor) {
        const container = document.getElementById(`viewer-${type}`);
        const img = document.getElementById(`img-${type}`);
        if (!img.src) return;

        this.currentZoom[type] = Math.max(0.5, Math.min(3, this.currentZoom[type] * factor));
        img.style.transform = `scale(${this.currentZoom[type]})`;
        container.classList.toggle('zoomed', this.currentZoom[type] > 1);
    }

    resetZoom(type) {
        const container = document.getElementById(`viewer-${type}`);
        const img = document.getElementById(`img-${type}`);
        this.currentZoom[type] = 1;
        img.style.transform = 'scale(1)';
        container.classList.remove('zoomed');
    }

    initSlider() {
        const handle = document.getElementById('slider-handle');
        const overlay = document.getElementById('comparison-overlay');

        const startDrag = (e) => {
            this.isDragging = true;
            e.preventDefault();
        };

        const moveDrag = (e) => {
            if (!this.isDragging) return;
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const slider = document.getElementById('viewer-comparison');
            const rect = slider.getBoundingClientRect();
            let pos = ((clientX - rect.left) / rect.width) * 100;
            pos = Math.max(0, Math.min(100, pos));
            overlay.style.width = pos + '%';
            handle.style.left = pos + '%';
        };

        const stopDrag = () => { this.isDragging = false; };

        handle.addEventListener('mousedown', startDrag);
        handle.addEventListener('touchstart', startDrag);
        document.addEventListener('mousemove', moveDrag);
        document.addEventListener('touchmove', moveDrag);
        document.addEventListener('mouseup', stopDrag);
        document.addEventListener('touchend', stopDrag);
    }

    initZoomClicks() {
        ['original', 'processed'].forEach(type => {
            document.getElementById(`viewer-${type}`).addEventListener('click', (e) => {
                if (e.target.tagName === 'BUTTON') return;
                const img = document.getElementById(`img-${type}`);
                if (!img.src) return;

                if (this.currentZoom[type] > 1) {
                    this.resetZoom(type);
                } else {
                    this.zoom(type, 2);
                }
            });
        });
    }
}
