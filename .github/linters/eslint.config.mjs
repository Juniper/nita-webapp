// ESLint v9 flat config — replaces legacy .eslintrc.json
// Mirrors the previous configuration: browser/jQuery environment with
// permissive rules suited to the legacy jQuery/SlickGrid codebase.
export default [
  {
    languageOptions: {
      ecmaVersion: 2015,
      sourceType: "script",
      globals: {
        // Browser globals
        window: "readonly",
        document: "readonly",
        navigator: "readonly",
        location: "readonly",
        history: "readonly",
        console: "readonly",
        alert: "readonly",
        confirm: "readonly",
        prompt: "readonly",
        setTimeout: "readonly",
        setInterval: "readonly",
        clearTimeout: "readonly",
        clearInterval: "readonly",
        XMLHttpRequest: "readonly",
        FormData: "readonly",
        Blob: "readonly",
        URL: "readonly",
        JSON: "readonly",
        Math: "readonly",
        Date: "readonly",
        Object: "readonly",
        Array: "readonly",
        String: "readonly",
        Number: "readonly",
        Boolean: "readonly",
        RegExp: "readonly",
        Error: "readonly",
        Promise: "readonly",
        // jQuery
        $: "readonly",
        jQuery: "readonly",
        // SlickGrid
        SlickGrid: "readonly",
        Slick: "readonly",
      },
    },
    rules: {
      "no-unused-vars": "warn",
      // Disabled — too many implicit browser/framework globals to enumerate
      // without the `globals` npm package (unavailable in linter path)
      "no-undef": "off",
      "eqeqeq": "off",
      "no-var": "off",
      "prefer-const": "off",
      "no-implicit-globals": "off",
    },
  },
];
