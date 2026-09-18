const AppAuth = {
  TOKEN_KEY: "asset_admin_token",
  USER_KEY: "asset_admin_user",

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem(this.USER_KEY));
    } catch (e) {
      return null;
    }
  },

  setLogin(token, user) {
    localStorage.setItem(this.TOKEN_KEY, token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },

  logout() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    window.location.href = "/login";
  },

  isAdmin() {
    const user = this.getUser();
    return !!(user && user.roles && user.roles.indexOf("admin") !== -1);
  },

  displayName() {
    const user = this.getUser();
    if (!user) {
      return "";
    }
    return user.real_name || user.username;
  },

  requireLogin() {
    if (!this.getToken()) {
      window.location.href = "/login";
      return false;
    }
    return true;
  },

  errorMsg(error, fallback) {
    return (error.response && error.response.data && error.response.data.msg) || fallback;
  },
};

axios.interceptors.request.use(function (config) {
  const token = AppAuth.getToken();
  if (token) {
    config.headers.Authorization = "Bearer " + token;
  }
  return config;
});

axios.interceptors.response.use(
  function (response) {
    return response;
  },
  function (error) {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem(AppAuth.TOKEN_KEY);
      localStorage.removeItem(AppAuth.USER_KEY);
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
