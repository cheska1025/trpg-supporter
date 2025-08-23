/** @type {import("eslint").Linter.Config} */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    ecmaFeatures: {
      jsx: true,
    },
    project: "./tsconfig.json", // 타입 기반 linting 필요 시
  },
  settings: {
    react: {
      version: "detect",
    },
  },
  plugins: ["react", "@typescript-eslint", "react-hooks"],
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/recommended-requiring-type-checking",
    "prettier", // prettier와 충돌 방지
  ],
  rules: {
    // ---- 코드 품질 규칙 ----
    "no-unused-vars": "off", // TS가 대신 체크
    "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],

    // ---- React 관련 ----
    "react/react-in-jsx-scope": "off", // React 17+ JSX transform
    "react/prop-types": "off", // TS로 타입 체크

    // ---- 스타일 관련 ----
    "@typescript-eslint/explicit-function-return-type": "off",
    "@typescript-eslint/no-explicit-any": "warn",

    // ---- 기타 ----
    "no-console": ["warn", { allow: ["warn", "error"] }],
  },
  ignorePatterns: [
    "dist/",
    "node_modules/",
    "*.config.js",
    "*.config.cjs",
  ],
};
