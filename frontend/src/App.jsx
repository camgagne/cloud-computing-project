import { useEffect, useState } from "react";
import { getCurrentUser, signOut } from "aws-amplify/auth";
import { Hub } from "aws-amplify/utils";
import AuthPage from "./AuthPage";
import { configureAuth, isAuthConfigured } from "./amplify";
import "./App.css";
import ImageUpload from "./ImageUpload";


function Feed({ userLabel, onSignOut }) {
  const [search, setSearch] = useState("");
  const [posts, setPosts] = useState(
    Array.from({ length: 8 }, (_, i) => ({
      id: i + 1,
      label: `Post ${i + 1}`,
    }))
  );

  function addPost() {
    const id = Math.max(0, ...posts.map((p) => p.id)) + 1;
    setPosts((prev) => [{ id, label: `Post ${id}` }, ...prev]);
  }

  const filteredPosts = posts.filter((post) =>
    post.label.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <header>
        <input
          id="search"
          type="search"
          placeholder="Search posts..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <button id="post-btn" onClick={addPost}>
          Post
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

      <main id="posts">
        {filteredPosts.map((post) => (
          <div key={post.id} className="post" title={post.label} />
        ))}
      </main>
      <ImageUpload />
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
