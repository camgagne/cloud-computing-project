import { useEffect, useState } from "react";
import { getCurrentUser, signOut } from "aws-amplify/auth";
import { Hub } from "aws-amplify/utils";
import AuthPage from "./AuthPage";
import { configureAuth, isAuthConfigured } from "./amplify";
import "./App.css";
import HomeFeed from "./HomeFeed";
import ImageUpload from "./ImageUpload";
import ProfilePage from "./ProfilePage";
import UserSearch from "./UserSearch";

function Feed({ userLabel, onSignOut }) {
  const [view, setView] = useState("home");
  const [selectedUserId, setSelectedUserId] = useState(null);

  function openProfile(userId) {
    setSelectedUserId(userId);
    setView("profile");
  }

  return (
    <>
      <header>
        <UserSearch onSelectUser={openProfile} />

        {/* Open home page */}
        <button className="default-btn" onClick={() => setView("home")}>
          Home
        </button>

        {/* Open post page (image upload) */}
        <button className="default-btn" onClick={() => setView("post")}>
          Create Post
        </button>

        {/* Open profile page */}
        <button
          className="default-btn"
          onClick={() => {
            setSelectedUserId(null);
            setView("profile");
          }}
        >
          My Profile
        </button>

        <div className="header-user">
          <span className="user-label" title={userLabel}>
            {userLabel}
          </span>
          <button type="button" className="sign-out-btn" onClick={onSignOut}>
            Sign out
          </button>
        </div>
      </header>

      {/* Show the current page below the header */}
      {view === "home" && <HomeFeed onSelectUser={openProfile} />}

      {view === "post" && <ImageUpload />}

      {view === "profile" && <ProfilePage userId={selectedUserId} />}
    </>
  );
}

function App() {
  const [authState, setAuthState] = useState("loading"); // loading | signedOut | signedIn
  const [userLabel, setUserLabel] = useState("");

  async function refreshSession() {
    if (!isAuthConfigured()) {
      setAuthState("signedOut");
      setUserLabel("");
      return;
    }
    try {
      const user = await getCurrentUser();
      setUserLabel(user.signInDetails?.loginId || user.username || "Signed in");
      setAuthState("signedIn");
    } catch {
      setUserLabel("");
      setAuthState("signedOut");
    }
  }

  useEffect(() => {
    let unsubscribe = () => {};

    (async () => {
      await configureAuth();
      await refreshSession();

      unsubscribe = Hub.listen("auth", ({ payload }) => {
        if (
          payload.event === "signedIn" ||
          payload.event === "signedOut" ||
          payload.event === "tokenRefresh"
        ) {
          refreshSession();
        }
      });
    })();

    return () => unsubscribe();
  }, []);

  async function handleSignOut() {
    try {
      await signOut();
    } finally {
      setAuthState("signedOut");
      setUserLabel("");
    }
  }

  if (authState === "loading") {
    return (
      <div className="auth-loading" aria-busy="true">
        Loading…
      </div>
    );
  }

  if (authState === "signedOut") {
    return <AuthPage onAuthenticated={refreshSession} />;
  }

  return <Feed userLabel={userLabel} onSignOut={handleSignOut} />;
}
export default App;
