// Global Data Cache Manager
class DataCache {
    constructor() {
        this.cache = {};
        this.cacheTime = 60000; // 60 soniya
    }

    get(key) {
        const item = this.cache[key];
        if (!item) return null;
        
        // Cache eskirgan bo'lsa
        if (Date.now() - item.timestamp > this.cacheTime) {
            delete this.cache[key];
            return null;
        }
        
        return item.data;
    }

    set(key, data) {
        this.cache[key] = {
            data: data,
            timestamp: Date.now()
        };
    }

    clear(key) {
        if (key) {
            delete this.cache[key];
        } else {
            this.cache = {};
        }
    }

    clearPattern(pattern) {
        Object.keys(this.cache).forEach(key => {
            if (key.includes(pattern)) {
                delete this.cache[key];
            }
        });
    }
}

// Global cache instance
window.dataCache = new DataCache();

