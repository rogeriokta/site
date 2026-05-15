class CameraManager {
    constructor(videoElement, statusText, statusBadge) {
        this.video = videoElement;
        this.statusText = statusText;
        this.statusBadge = statusBadge;
        this.stream = null;
        this.isActive = false;
        this.onActiveChange = null;
    }

    async start() {
        try {
            if (!navigator.mediaDevices?.getUserMedia) {
                throw new Error('API de câmera não suportada');
            }

            const config = { ...CONFIG.camera };
            const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
            if (isMobile) {
                config.facingMode = { exact: 'environment' };
            }

            this.stream = await navigator.mediaDevices.getUserMedia({ video: config });
            this.video.srcObject = this.stream;
            await this.video.play();

            this.isActive = true;
            this.setStatus('Câmera Ativa', false);
            if (this.onActiveChange) this.onActiveChange(true);

        } catch (error) {
            console.error('Erro ao acessar câmera:', error);
            this.setStatus('Erro na Câmera', true);

            let msg = 'Não foi possível acessar a câmera. ';
            if (error.name === 'NotAllowedError') {
                msg += 'Permita o acesso à câmera nas configurações do navegador.';
            } else if (error.name === 'NotFoundError') {
                msg += 'Nenhuma câmera encontrada no dispositivo.';
            } else {
                msg += error.message;
            }
            alert(msg);
            throw error;
        }
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(t => t.stop());
            this.stream = null;
            this.video.srcObject = null;
        }
        this.isActive = false;
        this.setStatus('Câmera Desligada', true);
        if (this.onActiveChange) this.onActiveChange(false);
    }

    capture() {
        if (!this.isActive) return null;

        const canvas = document.createElement('canvas');
        canvas.width = this.video.videoWidth;
        canvas.height = this.video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(this.video, 0, 0, canvas.width, canvas.height);

        return canvas;
    }

    setStatus(text, inactive) {
        this.statusText.textContent = text;
        if (inactive) {
            this.statusBadge.classList.add('inactive');
        } else {
            this.statusBadge.classList.remove('inactive');
        }
    }
}
