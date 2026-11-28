import { useCallback, useEffect, useState } from "react";
import { fetchAuthSession } from "aws-amplify/auth";
import "./HomeFeed.css";

export default function HomeFeed({ onSelectUser }) {
  const [posts, setPosts] = useState([]);
  const [nextToken, setNextToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  const loadPosts = useCallback(async ({ token = null, append = false } = {}) => {
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
      setError("");
    }

    try {
      const config = await fetch("/config.json").then((res) => res.json());
      if (!config.apiUrl || config.apiUrl === "None") {
        throw new Error("API is not configured");
      }

      const session = await fetchAuthSession();
      const accessToken = session.tokens?.accessToken?.toString();
      if (!accessToken) {
        throw new Error("You must be signed in");
      }

      const url = new URL(`${config.apiUrl}/posts`);
      if (token) {
        url.searchParams.set("nextToken", token);
      }

      const response = await fetch(url, {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) {
        throw new Error("Failed to load posts");
      }

      const data = await response.json();
      setPosts((prev) => (append ? [...prev, ...data.posts] : data.posts));
      setNextToken(data.nextToken || null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    loadPosts();
  }, [loadPosts]);

  return (
    <main className="home-feed">
      <div className="home-feed-header">
        <h2>Recent posts</h2>
        <span>{posts.length} shown</span>
      </div>

      {error && <p className="home-feed-error">Error: {error}</p>}

      {loading ? (
        <p className="home-feed-empty">Loading posts…</p>
      ) : posts.length === 0 ? (
        <p className="home-feed-empty">No posts yet. Be the first to share something.</p>
      ) : (
        <div className="home-feed-posts">
          {posts.map((post) => (
            <article key={post.postId} className="home-feed-post">
              <img src={post.imageUrl} alt="" loading="lazy" />
              <div className="home-feed-post-body">
                <button
                  type="button"
                  className="home-feed-author"
                  onClick={() => onSelectUser?.(post.userId)}
                >
                  {post.username}
                </button>
                <p className="home-feed-caption">{post.caption}</p>
                <p className="home-feed-date">
                  {new Date(post.createdAt).toLocaleString()}
                </p>
              </div>
            </article>
          ))}
        </div>
      )}

      {nextToken && (
        <div className="home-feed-more">
          <button
            type="button"
            className="default-btn"
            disabled={loadingMore}
            onClick={() => loadPosts({ token: nextToken, append: true })}
          >
            {loadingMore ? "Loading…" : "View more"}
          </button>
        </div>
      )}
    </main>
  );
}
