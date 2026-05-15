const CONFIG = {
    api: {
        baseUrl: 'http://localhost:8000',
        endpoints: {
            health: '/api/health',
            login: '/api/auth/login',
            register: '/api/auth/register',
            me: '/api/auth/me',
            upload: '/api/corrections/upload',
            list: '/api/corrections',
        },
    },
    camera: {
        width: { ideal: 1920 },
        height: { ideal: 1080 },
        facingMode: 'environment',
        aspectRatio: { ideal: 3 / 4 },
    },
    image: {
        quality: 0.95,
        format: 'image/jpeg',
        maxSizeMB: 20,
    },
    processing: {
        cardWidth: 2100,
        cardHeight: 2970,
        answerColumns: 5,
    },
};
