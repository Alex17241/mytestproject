document.addEventListener('DOMContentLoaded', () => {

    // ── Auto-dismiss alerts ────────────────────────────────────
    document.querySelectorAll('.alert').forEach(alert => {
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => dismiss(alert));
        }
        setTimeout(() => dismiss(alert), 5000);
    });

    function dismiss(el) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(-8px)';
        el.style.transition = 'all .3s ease';
        setTimeout(() => el.remove(), 300);
    }


    // ── Like toggle (AJAX) ─────────────────────────────────────
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', async function () {
            const postId = this.dataset.postId;
            const csrf  = getCookie('csrftoken');

            try {
                const res = await fetch(`/posts/${postId}/like/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrf },
                    credentials: 'same-origin',
                });

                if (res.status === 401) { window.location.href = '/login/'; return; }

                const data = await res.json();
                const icon = this.querySelector('i');

                if (data.liked) {
                    this.classList.add('liked');
                    icon.className = 'fa-solid fa-heart';
                    this.style.transform = 'scale(1.25)';
                    setTimeout(() => { this.style.transform = 'scale(1)'; }, 200);
                } else {
                    this.classList.remove('liked');
                    icon.className = 'fa-regular fa-heart';
                }

                // Обновляем все счётчики этого поста
                document.querySelectorAll('.like-count').forEach(el => {
                    el.textContent = data.count;
                });

            } catch (err) {
                console.error('Like error:', err);
            }
        });
    });


    // ── Предпросмотр изображения ───────────────────────────────
    const fileInput  = document.getElementById('id_image');
    const previewWrap = document.getElementById('image-preview');
    const previewImg  = document.getElementById('preview-img');
    const uploadArea  = document.querySelector('.image-upload-area');

    if (fileInput) {
        fileInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = e => {
                    if (previewImg) {
                        previewImg.src = e.target.result;
                        previewWrap.style.display = 'block';
                    }
                    if (uploadArea) uploadArea.style.borderColor = 'var(--primary)';
                };
                reader.readAsDataURL(file);
            }
        });

        if (uploadArea) {
            uploadArea.addEventListener('click', () => fileInput.click());
        }
    }


    // ── Мобильное меню ─────────────────────────────────────────
    const toggle     = document.querySelector('.navbar-toggle');
    const mobileMenu = document.getElementById('mobile-menu');

    if (toggle && mobileMenu) {
        toggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('open');
        });

        document.addEventListener('click', e => {
            if (!toggle.contains(e.target) && !mobileMenu.contains(e.target)) {
                mobileMenu.classList.remove('open');
            }
        });
    }


    // ── CSRF helper ────────────────────────────────────────────
    function getCookie(name) {
        const val = `; ${document.cookie}`;
        const parts = val.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

});