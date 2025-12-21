// SPA Router - Sahifalar o'rtasida tez o'tish
class SPARouter {
    constructor() {
        this.routes = {
            '/': 'index',
            '/warehouse': 'warehouse',
            '/reports': 'reports',
            '/employees': 'employees',
            '/ai-chat': 'ai_chat'
        };
        this.currentPage = null;
        this.pageCache = {};
        this.init();
    }

    init() {
        // Browser navigation'ni handle qilish
        window.addEventListener('popstate', (e) => {
            this.loadPage(window.location.pathname, false);
        });

        // Barcha linklarni intercept qilish
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="/"]');
            if (link && !link.hasAttribute('data-external')) {
                e.preventDefault();
                const href = link.getAttribute('href');
                this.navigate(href);
            }
        });

        // Dastlabki sahifani yuklash (faqat birinchi marta)
        if (!window.routerInitialized) {
            window.routerInitialized = true;
            // Dastlabki sahifa allaqachon yuklangan, shuning uchun faqat init qilish
            this.onPageLoad(window.location.pathname);
        }
    }

    async navigate(path) {
        if (path === window.location.pathname) return;
        
        // History'ga qo'shish
        window.history.pushState({}, '', path);
        
        // Sahifani yuklash
        await this.loadPage(path, true);
    }

    async loadPage(path, animate = true) {
        // Path'ni normalize qilish
        if (path === '' || path === '/') path = '/';
        if (!path.startsWith('/')) path = '/' + path;

        // Loading ko'rsatish
        if (animate) {
            this.showTransition();
        }

        try {
            // Cache'dan tekshirish
            if (this.pageCache[path]) {
                this.renderPage(this.pageCache[path], animate);
                return;
            }

            // Sahifani yuklash
            const response = await fetch(path);
            if (!response.ok) throw new Error('Sahifa topilmadi');
            
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Faqat main content'ni olish
            const mainContent = doc.querySelector('body').innerHTML;
            
            // Cache'ga saqlash
            this.pageCache[path] = mainContent;
            
            // Render qilish
            this.renderPage(mainContent, animate);
            
            // Script'larni bajarish
            this.executeScripts(doc, path);
            
        } catch (error) {
            console.error('Sahifa yuklash xatosi:', error);
            this.hideTransition();
        }
    }

    renderPage(html, animate) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        const newBody = tempDiv.querySelector('body');
        if (!newBody) {
            document.body.innerHTML = html;
            this.hideTransition();
            return;
        }
        
        const newMain = newBody.querySelector('.min-h-screen') || newBody;
        const currentMain = document.querySelector('.min-h-screen') || document.body;
        
        if (animate && currentMain) {
            // Fade out
            currentMain.style.opacity = '0';
            currentMain.style.transform = 'translateX(-10px)';
            currentMain.style.transition = 'all 0.2s ease';
            
            setTimeout(() => {
                // Content'ni almashtirish
                if (currentMain === document.body) {
                    document.body.innerHTML = newBody.innerHTML;
                } else {
                    currentMain.replaceWith(newMain);
                }
                
                // Fade in
                const updatedMain = document.querySelector('.min-h-screen') || document.body;
                updatedMain.style.opacity = '0';
                updatedMain.style.transform = 'translateX(10px)';
                updatedMain.style.transition = 'all 0.2s ease';
                
                setTimeout(() => {
                    updatedMain.style.opacity = '1';
                    updatedMain.style.transform = 'translateX(0)';
                    this.hideTransition();
                }, 50);
            }, 150);
        } else {
            if (currentMain === document.body) {
                document.body.innerHTML = newBody.innerHTML;
            } else {
                currentMain.replaceWith(newMain);
            }
            this.hideTransition();
        }
    }

    executeScripts(doc, path) {
        // Script fayllarni yuklash va bajarish
        const scripts = doc.querySelectorAll('script[src]');
        const scriptPromises = [];
        
        scripts.forEach(script => {
            const src = script.getAttribute('src');
            if (src) {
                // Agar script allaqachon yuklangan bo'lsa, skip qilish
                if (document.querySelector(`script[src="${src}"]`)) {
                    return;
                }
                
                const promise = new Promise((resolve) => {
                    const newScript = document.createElement('script');
                    newScript.src = src;
                    newScript.onload = resolve;
                    newScript.onerror = resolve; // Xatolik bo'lsa ham davom etish
                    document.body.appendChild(newScript);
                });
                scriptPromises.push(promise);
            }
        });

        // Barcha script'lar yuklangandan keyin
        Promise.all(scriptPromises).then(() => {
            // Inline script'larni bajarish
            const inlineScripts = doc.querySelectorAll('script:not([src])');
            inlineScripts.forEach(script => {
                try {
                    const scriptContent = script.textContent;
                    if (scriptContent.trim()) {
                        // Function declaration'larni eval qilish
                        if (scriptContent.includes('function')) {
                            eval(scriptContent);
                        }
                    }
                } catch (e) {
                    console.error('Script xatosi:', e);
                }
            });

            // Sahifa funksiyalarini chaqirish
            setTimeout(() => {
                this.initPage(path);
            }, 100);
        });
    }

    initPage(path) {
        // Har bir sahifa uchun initialization
        const pageName = this.routes[path] || 'index';
        
        // Global page init funksiyasini chaqirish
        const initFuncName = `init${pageName.charAt(0).toUpperCase() + pageName.slice(1)}`;
        if (window[initFuncName] && typeof window[initFuncName] === 'function') {
            // Kichik kechikish - DOM to'liq tayyor bo'lishi uchun
            setTimeout(() => {
                window[initFuncName]();
            }, 50);
        }

        // DOMContentLoaded event'ni trigger qilish
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.onPageLoad(path);
            });
        } else {
            this.onPageLoad(path);
        }
    }

    onPageLoad(path) {
        // Bottom navigation'ni yangilash
        this.updateNavigation(path);
        
        // Telegram WebApp'ni yangilash
        if (window.tg) {
            window.tg.ready();
            window.tg.expand();
        }
    }

    updateNavigation(path) {
        // Bottom navigation'da active state'ni yangilash
        document.querySelectorAll('nav a').forEach(link => {
            const href = link.getAttribute('href');
            if (href === path) {
                link.classList.remove('text-gray-400');
                link.classList.add('text-blue-600');
            } else {
                link.classList.remove('text-blue-600');
                link.classList.add('text-gray-400');
            }
        });
    }

    showTransition() {
        // Loading overlay ko'rsatish
        let overlay = document.getElementById('pageTransition');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'pageTransition';
            overlay.className = 'fixed inset-0 bg-white bg-opacity-90 z-50 flex items-center justify-center';
            overlay.style.transition = 'opacity 0.2s ease';
            overlay.innerHTML = `
                <div class="text-center">
                    <div class="loading-spinner inline-block w-10 h-10 border-3 border-blue-600 border-t-transparent rounded-full mb-2"></div>
                    <p class="text-gray-600 text-xs">Yuklanmoqda...</p>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
        overlay.style.opacity = '1';
    }

    hideTransition() {
        const overlay = document.getElementById('pageTransition');
        if (overlay) {
            overlay.style.opacity = '0';
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.style.display = 'none';
                }
            }, 150);
        }
    }

    // Prefetch - keyingi sahifalarni oldindan yuklash
    prefetch(path) {
        if (this.pageCache[path]) return;
        
        fetch(path)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                this.pageCache[path] = doc.querySelector('body').innerHTML;
            })
            .catch(err => console.log('Prefetch xatosi:', err));
    }
}

// Router'ni ishga tushirish
const router = new SPARouter();

// Prefetch - hover bo'lganda oldindan yuklash
document.addEventListener('mouseover', (e) => {
    const link = e.target.closest('a[href^="/"]');
    if (link && !link.hasAttribute('data-external')) {
        const href = link.getAttribute('href');
        router.prefetch(href);
    }
});

// Global navigate funksiyasi
window.navigate = (path) => router.navigate(path);

