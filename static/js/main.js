/**
 * 活动报名平台 — 基础交互脚本
 */

document.addEventListener('DOMContentLoaded', function () {
    // 用户下拉菜单切换
    const menuBtn = document.getElementById('user-menu-btn');
    const dropdown = document.getElementById('user-dropdown');
    if (menuBtn && dropdown) {
        menuBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            dropdown.classList.toggle('hidden');
        });
        document.addEventListener('click', function () {
            dropdown.classList.add('hidden');
        });
    }

    // 通知未读数轮询
    const badge = document.getElementById('unread-badge');
    if (badge) {
        function pollUnreadCount() {
            fetch('/notifications/unread-count')
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    if (data.count > 0) {
                        badge.textContent = data.count > 99 ? '99+' : data.count;
                        badge.classList.remove('hidden');
                    } else {
                        badge.classList.add('hidden');
                    }
                })
                .catch(function () { /* 忽略轮询错误 */ });
        }
        pollUnreadCount();
        setInterval(pollUnreadCount, 30000); // 每30秒轮询一次
    }

    // Flash 消息自动消失
    var flashMessages = document.querySelectorAll('[class*="bg-green-100"], [class*="bg-red-100"]');
    flashMessages.forEach(function (msg) {
        if (msg.closest('nav') === null) {
            setTimeout(function () {
                msg.style.transition = 'opacity 0.5s';
                msg.style.opacity = '0';
                setTimeout(function () { msg.remove(); }, 500);
            }, 4000);
        }
    });
});
