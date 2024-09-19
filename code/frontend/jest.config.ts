import type { Config } from "@jest/types";

const config: Config.InitialOptions = {
  verbose: true,

  preset: "ts-jest",

  testEnvironment: "jest-environment-jsdom",

  testEnvironmentOptions: {
    customExportConditions: [""],
  },

  moduleNameMapper: {
    "\\.(css|less|scss|svg|png|jpg)$": "identity-obj-proxy",
  },

  setupFilesAfterEnv: ['<rootDir>/src/test/setupTests.ts'],

  transform: {
    "^.+\\.(ts|tsx)$": "ts-jest",
  },

  setupFiles: ["<rootDir>/jest.polyfills.js"],
};

export default config;
