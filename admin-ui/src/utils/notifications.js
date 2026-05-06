export const playNotificationSound = () => {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if (!audioCtx) return;
        
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();

        // A pleasant "pop/ding" sound
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
        oscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.1);

        gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
        gainNode.gain.linearRampToValueAtTime(0.3, audioCtx.currentTime + 0.02);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);

        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        oscillator.start(audioCtx.currentTime);
        oscillator.stop(audioCtx.currentTime + 0.3);
    } catch (e) {
        console.warn('AudioContext not supported or blocked', e);
    }
};

export const showBrowserNotification = (title, body) => {
    if (!("Notification" in window)) {
        return;
    }

    if (Notification.permission === "granted") {
        new Notification(title, { body, icon: '/favicon.ico' });
    } else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(permission => {
            if (permission === "granted") {
                new Notification(title, { body, icon: '/favicon.ico' });
            }
        });
    }
};

export const requestNotificationPermission = () => {
    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }
};
