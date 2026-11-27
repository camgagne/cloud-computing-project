import { useEffect, useState } from "react";
import { getCurrentUser, signOut } from "aws-amplify/auth";
import { Hub } from "aws-amplify/utils";
import AuthPage from "./AuthPage";
import { configureAuth, isAuthConfigured } from "./amplify";
import "./App.css";
import ImageUpload from "./ImageUpload";
import ProfilePage from "./ProfilePage";
import UserSearch from "./UserSearch";

function Feed({ userLabel, onSignOut }) {
  const [search, setSearch] = useState("");
  const [view, setView] = useState("home")
  const [selectedUserId, setSelectedUserId] = useState(null);

  // Old dummy home page post system, for now blank, will eventually replace with feed maybe?
  // const [posts, setPosts] = useState(
  //   Array.from({ length: 8 }, (_, i) => ({
  //     id: i + 1,
  //     label: `Post ${i + 1}`,
  //   }))
  // );

  // function addPost() {
  //   const id = Math.max(0, ...posts.map((p) => p.id)) + 1;
  //   setPosts((prev) => [{ id, label: `Post ${id}` }, ...prev]);
  // }

  // const filteredPosts = posts.filter((post) =>
  //   post.label.toLowerCase().includes(search.toLowerCase())
  // );

  return (
    <>
      <header>
        <UserSearch
          onSelectUser={userId => {
            setSelectedUserId(userId);
            setView("profile");
          }}
        />

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
      {view === "home" && (
        <p>Home feed coming soon.</p>
        // also from old dummy home page
        // <main id="posts">
        //   {filteredPosts.map((post) => (
        //     <div key={post.id} className="post" title={post.label} />
        //   ))}
        // </main>
      )}

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
