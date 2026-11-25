import { Amplify } from "aws-amplify";

let configured = false;
let configurePromise = null;

export function isAuthConfigured() {
  return configured;
}

export function configureAuth() {
  if (configurePromise) return configurePromise;

  configurePromise = (async () => {
    try {
      const res = await fetch("/config.json", { cache: "no-store" });
      if (!res.ok) return false;

      const config = await res.json();
      const userPoolId = config.userPoolId;
      const userPoolClientId = config.userPoolClientId;

      if (!userPoolId || !userPoolClientId) return false;

      Amplify.configure({
        Auth: {
          Cognito: {
            userPoolId,
            userPoolClientId,
          },
        },
      });
      configured = true;
      return true;
    } catch {
      configured = false;
      return false;
    }
  })();

  return configurePromise;
}
