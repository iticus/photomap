 function decodeJWT(token) {
    let base64Url = token.split(".")[1];
    let base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    let jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map(function (c) {
          return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join("")
    );
    return JSON.parse(jsonPayload);
}


window.handleCredentialResponse = async (response) => {
    const responsePayload = decodeJWT(response.credential);
    const payload = {
        "source": "google",
        "key": responsePayload.sub,
        "name": responsePayload.name,
        "image": responsePayload.picture,
        "email": responsePayload.email
    };
//    document.cookie = document.cookie.replaceAll('"', "");  // fix double quotes in Cookie value
    const result = await fetch("/login", {
        method: "POST",
        body: new URLSearchParams(payload)
    });
    if (result.ok) {
        const searchParams = new URLSearchParams(window.location.search);
        window.location.href = searchParams.get("next") || "/";
    }
    else {
        console.log("cannot login:  " + result.text);
    }

}