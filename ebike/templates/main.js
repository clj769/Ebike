function href(id, url) {
  var btn = document.getElementById(id);

  btn.onclick = function () {
    window.location.href = url;
  };
}
href("sign", "map.html?id=2");

window.onload = function () {
  var login_submit = document.getElementById("login");
  var login_form = document.getElementById("loginForm");
  login_submit.onclick = function () {
    login_form.submit();
  };
};
