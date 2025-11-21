const navToggle = document.querySelector('.nav-toggle');
const navList = document.getElementById('nav-list');
const isHomePage = window.location.pathname.endsWith('index.html') || window.location.pathname === '/';

// キーワードの正解
const CORRECT_KEYWORD = "漆黒のネコ";

// 解錠フォーム関係
const form = document.getElementById("keyword-form");
const input = document.getElementById("keyword-input");
const msg = document.getElementById("keyword-message");

// メニューの表示切り替え
navToggle.addEventListener('click', () => {
  navList.classList.toggle('active');
});

// ページ読み込み後に実行
window.addEventListener('DOMContentLoaded', () => {
  // 初期状態はメニューを表示
  if (isHomePage) {
    navList.classList.add('active');  // index.htmlでは表示
    msg.textContent = ""; // メッセージクリア
  } else {
    navList.classList.remove('active'); // 他ページでは非表示
  }
});

// キーワード認証ロジック
if (form) {
  form.addEventListener("submit", function(e) {
    e.preventDefault();
    if (input.value.trim() === CORRECT_KEYWORD) {
      sessionStorage.setItem("unlocked", "true");
      alert("あなたは漆黒だ！");
      msg.textContent = "漆黒認証済み";
    } else {
      msg.textContent = "キーワードが間違っています。";
    }
  });
}

// クリック制御：リンクは隠さないがクリックでチェックする
document.querySelectorAll("a.locked").forEach(link => {
  link.addEventListener("click", function(e) {
    // ロックされていたらアラートして移動キャンセル
    if (sessionStorage.getItem("unlocked") !== "true") {
      e.preventDefault();
      alert("このページにはキーワードが必要です。");
    }
  });
});