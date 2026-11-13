chrome.webRequest.onAuthRequired.addListener(
  (details) => {
    const proxyCredentials = {
      "rtvgarrj-rotate": "lm01alulir0q",
      "dnqirzkr-rotate": "chzafg7c61vh",
      "gniprpsk-rotate": "nfe3v5p8ljh7",
      "orlhwzjj-rotate": "9npj7i4fr2qn",
      "zukrbczt-rotate": "lthv78w8ar6o",
      "xmclwhdf-rotate": "slgbxf0pirf2",
      "ujwgoped-rotate": "51tl7ogtsedj",
      "nduqzpyq-rotate": "3n43tqu33zop",
      "umsobndd-rotate": "9s801aw7inuh",
      "yegnulof-rotate": "vrr51m5335le",
      "ujqhbjhm-rotate": "bbzznuytyq7f",
      "xqthonfl-rotate": "atviwiojz5lo",
      "uiwltwjb-rotate": "ndj2ml3tp60x",
      "lulnoqml-rotate": "wkecio9ce6vt",
      "rdiwjxyb-rotate": "95xr5tvqhjwa",
      "cnvpknrz-rotate": "esdfw6zokuuc",
      "kvevteie-rotate": "lubw6c2yhkcu",
      "rvdvcyks-rotate": "hbq4fxkq9tzf",
      "vbpfwwjl-rotate": "shgzyp5jgyr4"
    };
    if (details.isProxy && details.challenger) {
      for (const [user, pass] of Object.entries(proxyCredentials)) {
        return {authCredentials: {username: user, password: pass}};
      }
    }
    return {};
  },
  {urls: ["<all_urls>"]},
  ["blocking"]
);
