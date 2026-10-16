// ライト/ダークの切替。初期値の決定は default.html の head 内インラインスクリプトで行う。
(function () {
  var STORAGE_KEY = 'theme';
  var root = document.documentElement;
  var button = document.querySelector('.theme-toggle');
  if (!button) return;

  function getStored() {
    try {
      var value = localStorage.getItem(STORAGE_KEY);
      return value === 'light' || value === 'dark' ? value : null;
    } catch (e) {
      return null;
    }
  }

  function current() {
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    var label = theme === 'dark' ? button.dataset.labelLight : button.dataset.labelDark;
    button.setAttribute('aria-label', label);
    button.setAttribute('title', label);
  }

  button.addEventListener('click', function () {
    var next = current() === 'dark' ? 'light' : 'dark';
    apply(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (e) {
      // 保存できない環境ではこのページ表示中のみ反映する
    }
  });

  // 利用者が明示的に選んでいない間は OS 設定の変更に追従する
  var media = window.matchMedia('(prefers-color-scheme: dark)');
  var onSystemChange = function (event) {
    if (getStored()) return;
    apply(event.matches ? 'dark' : 'light');
  };
  if (media.addEventListener) {
    media.addEventListener('change', onSystemChange);
  } else if (media.addListener) {
    media.addListener(onSystemChange);
  }

  apply(current());
  button.hidden = false;
})();
