import { useState } from "react";
import {
  signIn,
  signUp,
  confirmSignUp,
  resendSignUpCode,
} from "aws-amplify/auth";
import { isAuthConfigured } from "./amplify";
import "./AuthPage.css";

const MODES = {
  login: "login",
  signup: "signup",
  confirm: "confirm",
};

function friendlyError(err) {
  if (!err) return "Something went wrong.";
  const name = err.name || "";
  const message = err.message || String(err);

  if (name === "UserNotConfirmedException") {
    return "Please confirm your email before signing in.";
  }
  if (name === "NotAuthorizedException" || name === "UserNotFoundException") {
    return "Incorrect email or password.";
  }
  if (name === "UsernameExistsException") {
    return "An account with this email already exists.";
  }
  if (name === "CodeMismatchException") {
    return "That confirmation code is incorrect.";
  }
  if (name === "ExpiredCodeException") {
    return "That confirmation code has expired. Request a new one.";
  }
  if (name === "InvalidPasswordException") {
    return "Password must be at least 8 characters and include upper, lower, number, and symbol.";
  }
  if (name === "LimitExceededException" || name === "TooManyRequestsException") {
    return "Too many attempts. Please wait and try again.";
  }
  if (message.includes("Username is already taken")) {
  return "That username is already taken. Choose another one.";
  }
  if (message.includes("Username must contain")) {
    return "Username must contain 3–20 letters, numbers, or underscores.";
  }
  return message;
}

export default function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState(MODES.login);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState(false);

  const configured = isAuthConfigured();

  async function handleLogin(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setBusy(true);
    try {
      const result = await signIn({ username: email.trim(), password });
      if (result.isSignedIn) {
        onAuthenticated();
        return;
      }
      if (result.nextStep?.signInStep === "CONFIRM_SIGN_UP") {
        setMode(MODES.confirm);
        setInfo("Confirm your email with the code we sent you.");
        return;
      }
      setError("Additional sign-in steps are required. Try again or contact support.");
    } catch (err) {
      if (err?.name === "UserNotConfirmedException") {
        setMode(MODES.confirm);
        setInfo("Confirm your email with the code we sent you.");
        try {
          await resendSignUpCode({ username: email.trim() });
        } catch {
          /* ignore resend failure; user can retry */
        }
      } else {
        setError(friendlyError(err));
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleSignup(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setBusy(true);
    try {
      const result = await signUp({
        username: email.trim(),
        password,
        options: {
          userAttributes: {
            email: email.trim(),
            preferred_username: username.trim(),
          },
        },
      });
      if (result.isSignUpComplete) {
        setMode(MODES.login);
        setInfo("Account created. You can sign in now.");
        return;
      }
      if (result.nextStep?.signUpStep === "CONFIRM_SIGN_UP") {
        setMode(MODES.confirm);
        setInfo("We sent a confirmation code to your email.");
        return;
      }
      setError("Signup needs extra steps that are not supported yet.");
    } catch (err) {
      setError(friendlyError(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirm(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setBusy(true);
    try {
      await confirmSignUp({
        username: email.trim(),
        confirmationCode: code.trim(),
      });
      const result = await signIn({ username: email.trim(), password });
      if (result.isSignedIn) {
        onAuthenticated();
        return;
      }
      setMode(MODES.login);
      setInfo("Email confirmed. Sign in to continue.");
    } catch (err) {
      setError(friendlyError(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleResend() {
    setError("");
    setInfo("");
    setBusy(true);
    try {
      await resendSignUpCode({ username: email.trim() });
      setInfo("A new confirmation code was sent.");
    } catch (err) {
      setError(friendlyError(err));
    } finally {
      setBusy(false);
    }
  }

  function switchMode(next) {
    setMode(next);
    setError("");
    setInfo("");
    setCode("");
  }

  const title =
    mode === MODES.signup
      ? "Create account"
      : mode === MODES.confirm
        ? "Confirm email"
        : "Welcome back";

  const subtitle =
    mode === MODES.signup
      ? "Sign up with your email to start posting."
      : mode === MODES.confirm
        ? "Enter the code Cognito emailed you."
        : "Sign in to continue to your feed.";

  return (
    <div className="auth-page">
      <div className="auth-panel">
        <p className="auth-brand">Album</p>
        <h1>{title}</h1>
        <p className="auth-sub">{subtitle}</p>

        {!configured && (
          <p className="auth-banner" role="alert">
            Cognito is not configured. Run ./scripts/setup.sh with your
            deploy name once, then use ./scripts/dev.sh for local work.
          </p>
        )}

        {error && (
          <p className="auth-error" role="alert">
            {error}
          </p>
        )}
        {info && !error && (
          <p className="auth-info" role="status">
            {info}
          </p>
        )}

        {mode === MODES.login && (
          <form className="auth-form" onSubmit={handleLogin}>
            <label>
              Email
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={busy || !configured}
              />
            </label>
            <label>
              Password
              <input
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={busy || !configured}
              />
            </label>
            <button type="submit" disabled={busy || !configured}>
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>
        )}

        {mode === MODES.signup && (
          <form className="auth-form" onSubmit={handleSignup}>
            <label>
              Email
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={busy || !configured}
              />
            </label>
            <label>
              Username
              <input
                type="text"
                autoComplete="username"
                required
                minLength={3}
                maxLength={20}
                pattern="[a-zA-Z0-9_]+"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={busy || !configured}
              />
            </label>
            <p className="auth-hint">
              3–20 characters. Letters, numbers, and underscores only.
            </p>
            <label>
              Password
              <input
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={busy || !configured}
              />
            </label>
            <p className="auth-hint">
              At least 8 characters, with upper, lower, number, and symbol.
            </p>
            <button type="submit" disabled={busy || !configured}>
              {busy ? "Creating…" : "Create account"}
            </button>
          </form>
        )}

        {mode === MODES.confirm && (
          <form className="auth-form" onSubmit={handleConfirm}>
            <label>
              Email
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={busy || !configured}
              />
            </label>
            <label>
              Confirmation code
              <input
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                value={code}
                onChange={(e) => setCode(e.target.value)}
                disabled={busy || !configured}
              />
            </label>
            <button type="submit" disabled={busy || !configured}>
              {busy ? "Confirming…" : "Confirm & sign in"}
            </button>
            <button
              type="button"
              className="auth-link-btn"
              onClick={handleResend}
              disabled={busy || !configured || !email.trim()}
            >
              Resend code
            </button>
          </form>
        )}

        <div className="auth-switch">
          {mode === MODES.login && (
            <p>
              New here?{" "}
              <button type="button" onClick={() => switchMode(MODES.signup)}>
                Create an account
              </button>
            </p>
          )}
          {mode === MODES.signup && (
            <p>
              Already have an account?{" "}
              <button type="button" onClick={() => switchMode(MODES.login)}>
                Sign in
              </button>
            </p>
          )}
          {mode === MODES.confirm && (
            <p>
              Wrong account?{" "}
              <button type="button" onClick={() => switchMode(MODES.login)}>
                Back to sign in
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
